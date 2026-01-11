import os
from dotenv import load_dotenv
from cache import make_key, cache_get, cache_set
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jVector
from neo4j import GraphDatabase
from pymongo import MongoClient
from typing import Annotated, Sequence, Literal
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from prometheus_client import Counter, start_http_server
from pydantic import BaseModel
import operator
import json

load_dotenv()
CACHE_HIT = Counter(
    "cache_hit_total",
    "Total number of cache hits"
)

CACHE_MISS = Counter(
    "cache_miss_total",
    "Total number of cache misses"
)


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
AUTH = (NEO4J_USERNAME, NEO4J_PASSWORD)

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

MONGO_DB = os.getenv("MONGO_DB", "jobportal")

print("Loading Embeddings..")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Connecting to Databases...")

mongo_client = MongoClient(MONGO_CONNECTION_STRING)
jobs_collection = mongo_client[MONGO_DB]["job_postings"]

try:
    vector_store = Neo4jVector.from_existing_graph(
        embedding=embedding_model,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        index_name="job_vector_index",
        node_label="Role",
        text_node_properties=["description", "name"],
        embedding_node_property="embedding",
    )
except Exception as e:
    print(f"[ERROR]: Could not connect to Neo4j Vector Index: {e}")

llm_discovery = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
llm_extract = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


class CareerState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], operator.add]

    career_goal: str | None = None
    current_skills: list[str] | None = None
    experience_level: str | None = None
    location: str | None = None

    identified_role: str | None = None

    active_agent: Literal["advisor", "scout"] = "advisor"


@tool
def find_best_role_match(skills: list[str]) -> str:
    """
    Finds the best Job Role by counting skill matches in Neo4j.
    """

    cache_key = make_key(
        "role_match",
        {"skills": [s.strip().lower() for s in skills]},
    )

    cached = cache_get(cache_key)
    if cached is not None:
        CACHE_HIT.inc()
        print("[CACHE HIT] role_match")
        return json.dumps(cached)

    CACHE_MISS.inc()
    print("[CACHE MISS] role_match")

    driver = GraphDatabase.driver(NEO4J_URI, auth=AUTH)

    cypher_query = """
    UNWIND $skills AS user_skill
    MATCH (r:Role)-[:REQUIRES|RECOMMENDS]-(s:Skill)
    WHERE toLower(s.name) = toLower(user_skill)
    WITH r, count(s) AS match_count, collect(s.name) AS matched_skills
    ORDER BY match_count DESC LIMIT 1
    RETURN r.name AS role_name, r.description AS description, match_count, matched_skills
    """
    try:
        records, summary, keys = driver.execute_query(
            cypher_query, skills=skills, database_="neo4j"
        )

        if not records:
            return json.dumps({"error": "No matching role found."})

        print(records[0]["role_name"])

        result = {
            "role_name": records[0]["role_name"],
            "description": records[0]["description"],
            "match_score": records[0]["match_count"],
            "matched_skills": records[0]["matched_skills"],
        }

        cache_set(cache_key, result, ttl=3600)  

        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        driver.close()



@tool
def search_mongodb_jobs(
    job_title: str, location: str = None, experience_level: str = None
) -> str:
    """

    Hybrid Search: Attempts Vector Search first, falls back to Standard Regex if no results.
    """

    missing_fields = []
    if not location or location.lower() in ["unknown", "none", ""]:
        missing_fields.append("Location")

    if not experience_level or experience_level.lower() in ["unknown", "none", ""]:
        missing_fields.append("Experience Level")

    if missing_fields:
        return f"STOP: You cannot search yet. The user has not provided: {', '.join(missing_fields)}. Ask the user for this information."

    cache_key = make_key(
        "job_search",
        {
            "job_title": (job_title or "").strip().lower(),
            "location": (location or "").strip().lower(),
            "experience_level": (experience_level or "").strip().lower(),
        },
    )

    cached = cache_get(cache_key)
    if cached is not None:
        CACHE_HIT.inc()
        print("[CACHE HIT] job_search")
        return json.dumps(cached)

    CACHE_MISS.inc()
    print("[CACHE MISS] job_search")

    try:
        print(
            f"Scout Debug: Searching for '{job_title}' in '{location}' ({experience_level})"
        )

        query_text = f"{location} {experience_level} {job_title}"

        query_embedding = embedding_model.embed_query(query_text)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "job_vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": 50,
                }
            }
        ]

        match_conditions = []
        if location:
            match_conditions.append({"location": {"$regex": location, "$options": "i"}})
        if experience_level:
            match_conditions.append(
                {"experience_level": {"$regex": experience_level, "$options": "i"}}
            )

        if match_conditions:
            pipeline.append({"$match": {"$and": match_conditions}})

        pipeline.extend(
            [
                {"$addFields": {"score": {"$meta": "vectorSearchScore"}}},
                {
                    "$project": {
                        "_id": 0,
                        "job_title": 1,
                        "company": 1,
                        "location": 1,
                        "salary_range": 1,
                        "score": 1,
                    }
                },
                {"$limit": 5},
            ]
        )

        results = list(jobs_collection.aggregate(pipeline))

        if not results:
            print("Vector search yielded 0 results. Switching to Regex Fallback...")
            query = {}
            if job_title and "anything" not in job_title.lower():
                query["job_title"] = {"$regex": job_title, "$options": "i"}
            if location:
                query["location"] = {"$regex": location, "$options": "i"}
            if experience_level:
                query["experience_level"] = {
                    "$regex": experience_level,
                    "$options": "i",
                }

            results = list(
                jobs_collection.find(
                    query,
                    {
                        "_id": 0,
                        "job_title": 1,
                        "company": 1,
                        "location": 1,
                        "salary_range": 1,
                    },
                ).limit(5)
            )

        if not results:
            return json.dumps({"message": "No jobs found matching your criteria."})

        cache_set(cache_key, results, ttl=600)

        return json.dumps(results)

    except Exception as e:
        print(f"Error in search tool: {e}")
        return json.dumps({"error": str(e)})


ADVISOR_PROMPT = """You are a Career Path Architect.
Your goal is to map user skills to a Standardized Role in the Neo4j database.

TOOLS:
- `find_best_role_match`: specificy a list of skills. 
  It queries the graph relationships directly (e.g. Job -> REQUIRES -> Skill).

INSTRUCTIONS:
1. Ask for at least 3-4 specific technical skills.
2. Call `find_best_role_match`.
3. If the tool returns a match (even with a low score), explain *why* it matched (e.g. "You matched 3 out of 4 skills for Data Scientist").
4. If the user confirms, say "HANDOFF_TO_SCOUT.

When a tool returns JSON:
- Read it
- Explain it clearly to the user
- Do NOT show raw JSON
"""

SCOUT_PROMPT = """You are a Headhunter / Job Scout.
Your goal is to find active job listings in MongoDB for a specific role.

CONTEXT:
The previous agent has identified the target role: "{identified_role}".

TOOLS:
- You have access to `search_mongodb_jobs`.
- You MUST use this tool once you have the user's Location and Experience Level.

INSTRUCTIONS:
1. You need two things before searching: Location and Experience Level.
2. Check the conversation history. 
   - If the user provided them, DO NOT ASK AGAIN. CALL THE TOOL IMMEDIATELY.
   - If they are missing, ask for them.
3. Once you call the tool, summarize the results for the user.

CRITICAL RULES:
- Do not say "I cannot execute this task". You HAVE the tool. Use it.
- Do not ask for confirmation if the user just gave you the info.

When a tool returns JSON:
- Read it
- Explain it clearly to the user
- Do NOT show raw JSON
"""

advisor_model = llm_discovery.bind_tools([find_best_role_match])
scout_model = llm_discovery.bind_tools([search_mongodb_jobs])


def run_advisor(state: CareerState):
    """
    Agent 1: Handles Skill -> Role mapping.
    """

    if state.active_agent == "scout":
        print("--- Advisor: Passing through to Scout ---")
        return {"active_agent": "scout"}

    print("--- Advisor Agent Running ---")
    messages = [SystemMessage(content=ADVISOR_PROMPT)] + state.messages
    response = advisor_model.invoke(messages)

    next_agent = "advisor"
    if "HANDOFF_TO_SCOUT" in response.content:
        response.content = response.content.replace("HANDOFF_TO_SCOUT", "").strip()
        next_agent = "scout"

    return {"messages": [response], "active_agent": next_agent}


def run_scout(state: CareerState):
    """
    Agent 2: Handles Logistics -> Job Listing
    """
    print("--- Scout Agent Running ---")

    print(state.identified_role)
    role = state.identified_role or "Software Engineer"  # Fallback
    formatted_prompt = SCOUT_PROMPT.format(identified_role=role)

    messages = [SystemMessage(content=formatted_prompt)] + state.messages

    response = scout_model.invoke(messages)

    return {
        "messages": [response],
        "active_agent": "scout",  # Stays here
    }


def handle_tool_call(state: CareerState):
    """
    Custom Tool Node: Executes tools AND updates 'identified_role' in state.
    """

    tool_node = ToolNode([find_best_role_match, search_mongodb_jobs])
    result = tool_node.invoke(state)  # Returns {"messages": [ToolMessage, ...]}

    new_messages = result["messages"]

    state_update = {"messages": new_messages}

    for message in new_messages:
        if isinstance(message, ToolMessage) and message.name == "find_best_role_match":
            try:
                output_data = json.loads(message.content)

                role_name = output_data.get("role_name")

                if role_name:
                    print(f"State Update: Identified Role set to '{role_name}'")
                    state_update["identified_role"] = role_name

            except Exception as e:
                print(f"Failed to parse tool output for state update: {e}")

    return state_update


def route_advisor(state):
    if not state.messages:
        return END

    last_message = state.messages[-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    if state.active_agent == "scout":
        return "scout"

    return END


def route_scout(state):
    if not state.messages:
        return END

    last_message = state.messages[-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return END


workflow = StateGraph(CareerState)


workflow.add_node("advisor", run_advisor)
workflow.add_node("scout", run_scout)


workflow.add_node("tools", handle_tool_call)

workflow.set_entry_point("advisor")


workflow.add_conditional_edges(
    "advisor", route_advisor, {"tools": "tools", "scout": "scout", END: END}
)

workflow.add_conditional_edges("scout", route_scout)


def route_tools(state):
    if state.active_agent == "advisor":
        return "advisor"
    return "scout"


workflow.add_conditional_edges("tools", route_tools)

app = workflow.compile()
print("Graph Compiled and Ready to Export.")
