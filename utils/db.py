import os
from pymongo import MongoClient

_client = None

# Fallback connection string so the system works out of the box. You can
# override it anytime by setting a MONGO_URI environment variable on Render
# instead (recommended for production), without touching this file.
_DEFAULT_MONGO_URI = (
    "mongodb+srv://devms786178_db_user:cEtMdLjmHF5EM2Pf@cluster0.xbqyvnn.mongodb.net/?appName=Cluster0"
)


def get_db():
    """
    Returns the MongoDB database handle used to store Lecture/Quiz links
    (original url <-> generated name mapping).
    """
    global _client
    mongo_uri = os.environ.get("MONGO_URI", _DEFAULT_MONGO_URI)

    if _client is None:
        _client = MongoClient(mongo_uri)

    db_name = os.environ.get("MONGO_DB_NAME", "lectyebro_live_class_system")
    return _client[db_name]
