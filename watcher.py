import os
import time
from pymongo import MongoClient
from dotenv import load_dotenv
from cache import invalidate_cache_for_term

load_dotenv()

MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
MONGO_DB = os.getenv("MONGO_DB", "jobportal")


def watch_collection():
    """
    Triggers cache invalidation when a job title is inserted, updated, or deleted.
    """
    client = MongoClient(MONGO_CONNECTION_STRING)
    db = client[MONGO_DB]
    collection = db["job_postings"]

    print("MongoDB Watcher started. Listening for changes...")

    try:
        pipeline_options = {
            "full_document": "updateLookup",
            "full_document_before_change": "whenAvailable",
        }

        with collection.watch(**pipeline_options) as stream:
            for change in stream:
                op_type = change.get("operationType")

                doc = None

                # For DELETE, we look at what the document WAS ('fullDocumentBeforeChange')
                if op_type == "delete":
                    doc = change.get("fullDocumentBeforeChange")

                # 2. For INSERT/UPDATE/REPLACE, we look at what the document IS ('fullDocument')
                else:
                    doc = change.get("fullDocument")

                if not doc:
                    continue

                job_title = doc.get("job_title")

                if job_title:
                    print(f"Detected {op_type} on job: '{job_title}'")
                    invalidate_cache_for_term(job_title)

    except Exception as e:
        print(f"Watcher Stream Error: {e}")


if __name__ == "__main__":
    while True:
        try:
            watch_collection()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Connection lost, retrying in 5s... Error: {e}")
            time.sleep(5)
