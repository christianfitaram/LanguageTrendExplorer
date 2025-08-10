from pymongo import MongoClient
from mongo.mongodb_client import db
from mongo.repositories.repository_articles import RepositoryArticles
from bson import ObjectId

repo_articles = RepositoryArticles(db)


def delete_duplicate_articles_by_sample(sample_id):
    # Step 1: Find all articles in the given sample
    cursor = repo_articles.get_articles({"sample": sample_id}, {"url": 1})

    seen_urls = set()
    duplicates_to_delete = []

    for doc in cursor:
        url = doc.get("url")
        if url in seen_urls:
            duplicates_to_delete.append(doc["_id"])
        else:
            seen_urls.add(url)

    # Step 2: Delete duplicates
    if duplicates_to_delete:
        result = repo_articles.delete_articles({"_id": {"$in": duplicates_to_delete}})
        print(f"🗑️ Deleted {result} duplicates in sample {sample_id}")
    else:
        print(f"✅ No duplicates found in sample {sample_id}")


# usage
if __name__ == "__main__":
    delete_duplicate_articles_by_sample("1-2025-08-09")
