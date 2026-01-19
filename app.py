import os
from dotenv import load_dotenv
from cache import make_key, cache_get, cache_set
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

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
from cache import init_semantic_cache, semantic_cache_get, semantic_cache_set
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import threading
import metrics
from metrics import TOOL_USAGE, REQUEST_LATENCY, ERROR_COUNT


load_dotenv()
init_semantic_cache()

# CACHE_HIT = Counter("cache_hit_total", "Total number of cache hits")

# CACHE_MISS = Counter("cache_miss_total", "Total number of cache misses")


threading.Thread(target=metrics.start_metrics, daemon=True).start()


NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
AUTH = (NEO4J_USER, NEO4J_PASSWORD)

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

MONGO_DB = os.getenv("MONGO_DB", "jobportal")

print("Loading Embeddings..")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

print("Connecting to Databases...")

mongo_client = MongoClient(MONGO_CONNECTION_STRING)
jobs_collection = mongo_client[MONGO_DB]["job_postings"]


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
    Uses Semantic Caching to handle variations in skill naming.
    """

    TOOL_USAGE.labels(tool_name="find_best_role_match").inc()

    with REQUEST_LATENCY.labels(stage="neo4j_lookup").time():
        skills_text = ", ".join(sorted([s.strip() for s in skills]))

        try:
            query_vector = embedding_model.embed_query(skills_text)
        except Exception as e:
            return json.dumps({"error": f"Embedding failed: {str(e)}"})

        # We use a strict threshold because skills are specific.
        # We don't want "Java" to accidentally match "JavaScript" just because they share letters
        cached_result = semantic_cache_get(
            query_vector, category="role_match", threshold=0.1
        )

        if cached_result and "role_name" in cached_result:
            # CACHE_HITS.labels(layer="semantic").inc()
            print(f"[SEMANTIC HIT] role_match for '{skills_text}'")
            return json.dumps(cached_result)

        exact_key = make_key("role_match", {"skills": sorted(skills)})
        if cache_get(exact_key):
            # CACHE_HITS.labels(layer="exact").inc()
            return json.dumps(cache_get(exact_key))

        # CACHE_MISSES.labels(layer="role_match").inc()
        print(f"[CACHE MISS] role_match for '{skills_text}'")

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
            with driver.session(database="neo4j") as session:
                result = session.run(cypher_query, skills=skills)
                records = list(result)

            if not records:
                return json.dumps({"error": "No matching role found."})

            record = records[0]

            result = {
                "role_name": record["role_name"],
                "description": record["description"],
                "match_score": record["match_count"],
                "matched_skills": record["matched_skills"],
            }

            semantic_cache_set(skills_text, query_vector, result, category="role_match")

            cache_set(exact_key, result, ttl=3600)

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
    Uses Semantic Caching to skip database querying.
    """

    TOOL_USAGE.labels(tool_name="search_mongodb_jobs").inc()

    missing_fields = []
    if not location or location.lower() in ["unknown", "none", ""]:
        missing_fields.append("Location")

    if not experience_level or experience_level.lower() in ["unknown", "none", ""]:
        missing_fields.append("Experience Level")

    if missing_fields:
        return f"STOP: You cannot search yet. The user has not provided: {', '.join(missing_fields)}. Ask the user for this information."

    # STANDARD CACHE
    payload = {
        "job_title": job_title.strip().lower(),
        "location": location.strip().lower(),
        "experience_level": experience_level.strip().lower(),
    }

    exact_key = make_key("job_search", payload)

    if exact_match := cache_get(exact_key):
        print(f"[EXACT HIT] job_search for {payload}")
        return json.dumps(exact_match)

    print(f"[EXACT MISS] job_search for {payload}")

    # SEMANTIC CACHE
    semantic_query = f"{job_title} {location} {experience_level}".strip().lower()

    query_vector = embedding_model.embed_query(semantic_query)

    cached_result = semantic_cache_get(
        query_vector, category="job_search", threshold=0.15
    )
    if cached_result:
        print("[CACHE OPTIMIZATION] Backfilling Exact Cache from Semantic Hit")
        cache_set(exact_key, cached_result, ttl=3600)
        return json.dumps(cached_result)

    print("[CACHE MISS] job_search")

    try:
        print(
            f"Scout Debug: Searching for '{job_title}' in '{location}' ({experience_level})"
        )

        with REQUEST_LATENCY.labels(stage="mongo_lookup").time():
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
                match_conditions.append(
                    {"location": {"$regex": location, "$options": "i"}}
                )
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

        semantic_cache_set(semantic_query, query_vector, results, category="job_search")
        cache_set(exact_key, results, ttl=3600)

        return json.dumps(results)

    except Exception as e:
        print(f"Error in search tool: {e}")
        return json.dumps({"error": str(e)})


EXTRACT_PROMPT = """
You are an expert Resume Parser. 
Extract the technical skills from the user's input below.
Return ONLY a JSON object with a single key 'skills' containing a list of strings.
Do not include non-technical skills like "hard working" or "team player".
If no skills are found, return {{"skills": []}}.

User Input: {input}
"""


ADVISOR_PROMPT = """You are a Career Path Architect.
Your goal is to map user skills to a Standardized Role in the Neo4j database.

TOOLS:
- `find_best_role_match`: specificy a list of skills. 
  It queries the graph relationships directly (e.g. Job -> REQUIRES -> Skill).

INSTRUCTIONS:
1. Call `find_best_role_match`.
2. If the tool returns a match (even with a low score), explain *why* it matched (e.g. "You matched 3 out of 4 skills for Data Scientist").
    - clearly state the **Role Name** and **Description** found.
   - explain the match strength (e.g., "Matched 3/4 skills").
   - **CRITICAL:** You MUST ask the user for confirmation. End your response with: "Does this role sound like the right direction for you?"
3. If the user confirms, say "HANDOFF_TO_SCOUT.

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


extract_parser = JsonOutputParser()


def extract_skills_with_semantic_cache(user_input: str):
    """
    Check semantic cache for similar user introductions.
    If hit: return cached skills.
    If miss: Run LLM extraction, cache result, return skills.
    """

    try:
        query_vector = embedding_model.embed_query(user_input)
    except Exception as e:
        print(f"[Extraction Error] Embedding failed: {e}")
        return []

    cached_result = semantic_cache_get(
        query_vector, category="extraction", threshold=0.15
    )

    if cached_result and isinstance(cached_result, dict) and "skills" in cached_result:
        # CACHE_HIT.inc()
        print(f"[SEMANTIC HIT] Extraction for input: '{user_input[:30]}...'")

        return (
            cached_result.get("skills", [])
            if isinstance(cached_result, dict)
            else cached_result
        )

    # CACHE_MISS.inc()
    print(f"[CACHE MISS] Running LLM Extraction for: '{user_input[:30]}...'")

    prompt = ChatPromptTemplate.from_template(EXTRACT_PROMPT)

    # LLM extracts skills form the promt and parses the result
    chain = prompt | llm_extract | extract_parser

    try:
        result = chain.invoke({"input": user_input})
        skills_list = result.get("skills", [])

        semantic_cache_set(
            user_input, query_vector, {"skills": skills_list}, category="extraction"
        )

        return skills_list
    except Exception as e:
        print(f"[Extraction Error] LLM parsing failed: {e}")
        return []


def run_extractor(state: CareerState):
    """
    Entry Point Node.
    Analyzes the initial user message to pre-populate state.current_skills.
    """
    with REQUEST_LATENCY.labels(stage="extractor_llm").time():
        print("--- Extractor Node Running ---")

        if not state.messages:
            return {"current_skills": []}

        last_message = state.messages[-1]
        user_text = last_message.content

        extracted_skills = extract_skills_with_semantic_cache(user_text)

        if extracted_skills:
            print(f"Skills Extracted: {extracted_skills}")

            return {"current_skills": extracted_skills}

        return {"current_skills": []}


extract_parser = JsonOutputParser()


def run_advisor(state: CareerState):
    """
    Agent 1: Handles Skill -> Role mapping.
    Dynamically adjusts prompt based on whether skills were already extracted.
    """
    if state.active_agent == "scout":
        return {"active_agent": "scout"}

    print("--- Advisor Agent Running ---")

    existing_skills = state.current_skills or []

    if existing_skills and len(existing_skills) > 0:
        skills_str = ", ".join(existing_skills)
        print(f"Advisor Context: User already has skills: {skills_str}")

        system_context = f"""{ADVISOR_PROMPT}

        IMPORTANT UPDATE: 
        The user has ALREADY provided the following skills: {skills_str}.
        
        Action Plan:
        1. IMMEDIATELY call `find_best_role_match` with these skills.
        2. DO NOT assume the user accepts the result.
        3. Once the tool provides the Role, you MUST display it and ask: "Do you agree to continue with this role?"
        """
    else:
        system_context = ADVISOR_PROMPT

    messages = [SystemMessage(content=system_context)] + state.messages
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


def route_tools(state):
    if state.active_agent == "advisor":
        return "advisor"
    return "scout"


def route_entry(state: CareerState):
    if state.active_agent == "scout":
        return "scout"

    return "extractor"


workflow = StateGraph(CareerState)


workflow.add_node("extractor", run_extractor)
workflow.add_node("advisor", run_advisor)
workflow.add_node("scout", run_scout)
workflow.add_node("tools", handle_tool_call)

# workflow.set_entry_point("extractor")

workflow.set_conditional_entry_point(
    route_entry,
    {
        "extractor": "extractor",
        "scout": "scout",
    },
)

workflow.add_edge("extractor", "advisor")


workflow.add_conditional_edges(
    "advisor",
    route_advisor,
    {
        "tools": "tools",
        "scout": "scout",
        END: END,
    },
)

workflow.add_conditional_edges("scout", route_scout)
workflow.add_conditional_edges("tools", route_tools)

app = workflow.compile()
print("Graph Compiled and Ready to Export.")
