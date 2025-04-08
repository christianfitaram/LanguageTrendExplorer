from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def find_articles(quantity, params, sorting=None):
    try:
        if quantity == "one":
            result = db.articles.find_one(params)
        elif sorting is not None:
            result = db.articles.find_one(params, sort=sorting)
        elif quantity == "all":
            result = db.articles.find(params)
        else:
            return "Wrong quantity param"

        if result:
            return result
        else:
            return "ERROR in finding"
    except Exception as e:
        print(f"Error:{e}")
        return "ERROR in finding"


def find_clean_articles(params):
    try:
        result = list(db.clean_articles.find(params))
        if result:
            return result
        else:
            "ERROR in finding"
    except Exception as e:
        print(f"Error:{e}")
        return "ERROR in finding"


def find_daily_trends(quantity, params):
    try:
        if quantity == "one":
            result = db.daily_trends.find_one(params)
        elif quantity == "all":
            result = db.daily_trends.find(params)
        else:
            return "Wrong quantity param"

        if result:
            return result
        else:
            return "ERROR in finding"
    except Exception as e:
        print(f"Error:{e}")
        return "ERROR in finding"


def find_trend_predictions(quantity, params):
    try:
        if quantity == "one":
            result = db.trend_predictions.find_one(params)
            return result
        else:
            return "ERROR in finding"
    except Exception as e:
        print(f"Error:{e}")
        return "ERROR in finding"
