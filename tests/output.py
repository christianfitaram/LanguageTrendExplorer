from mongo.mongodb_client import db
from mongo.repositories.repository_daily_trends import RepositoryDailyTrends
from mongo.repositories.repository_articles import RepositoryArticles

repo = RepositoryDailyTrends(db)
repoart = RepositoryArticles(db)


def output():

    # Adjust the collection name accordingly
    collection = db[""]

    # Define the regex pattern
    pattern = r".*-2025-04-13"

    # Delete all matching documents
    result = collection.delete_many({"in_sample": {"$regex": pattern}})

    print(f"🗑️ Deleted {result.deleted_count} documents.")


if __name__ == "__main__":
    output()
