import os
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")

print(MONGO_CONNECTION_STRING)
MONGO_DB = os.getenv("MONGO_DB", "jobportal")
COLLECTION_NAME = "job_postings"


print("Loading Embedding Model (384 dimensions)...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def vectorize_jobs_weighted():
    client = MongoClient(MONGO_CONNECTION_STRING)
    collection = client[MONGO_DB][COLLECTION_NAME]

    jobs = list(collection.find({}))

    print(f"Found {len(jobs)} jobs. Re-generating weighted embeddings...")

    count = 0
    for job in jobs:
        title = job.get("job_title", "")
        desc = job.get("job_description", "") or job.get("description", "")
        loc = job.get("location", "Unknown")
        exp = job.get("experience_level", "Unknown")

        text_to_embed = (
            f"Location: {loc}. Experience: {exp}. Title: {title}. "
            f"Job for {title} in {loc} ({exp}). "
            f"Description: {desc}"
        )

        vector = embedding_model.embed_query(text_to_embed)

        collection.update_one({"_id": job["_id"]}, {"$set": {"embedding": vector}})

        count += 1
        if count % 10 == 0:
            print(f"   Updated {count}/{len(jobs)}: {title}")

    print("All jobs re-vectorized!")


if __name__ == "__main__":
    vectorize_jobs_weighted()
