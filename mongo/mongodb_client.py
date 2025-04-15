from pymongo import MongoClient
from dotenv import load_dotenv
import os

# loading env variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
DB_NAME = os.getenv("DB_NAME")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
