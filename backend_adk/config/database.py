from pymongo import MongoClient
from pymongo.database import Database
from config.settings import MONGO_URI, MONGO_DB_NAME

_client: MongoClient | None = None


def get_db() -> Database:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[MONGO_DB_NAME]


def close_db() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
