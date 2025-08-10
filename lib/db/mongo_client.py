# lib/db/mongo_client.py
import os
from pymongo import MongoClient

_client = None
_db = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI", "")
        _client = MongoClient(uri, appname=os.getenv("APP_NAME", ""))
    return _client


def get_db():
    global _db
    if _db is None:
        db_name = os.getenv("MONGODB_DB", "")
        _db = get_client()[db_name]
    return _db
