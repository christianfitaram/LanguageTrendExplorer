import datetime

from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.metadata_repository import MetadataRepository
from lib.repositories.summaries_repository import SummariesRepository
from lib.repositories.daily_trends_repository import DailyTrendsRepository

repo_articles = ArticlesRepository()
repo_summaries = SummariesRepository()
repo_metadata = MetadataRepository()
repo_daily_trends = DailyTrendsRepository()

sample_id = "1-2025-08-17"
sample_new = "1-2025-08-16"


def modify_sample_in_articles():
    cursor = repo_articles.get_articles({"sample": sample_id})
    for article in cursor:
        repo_articles.update_articles({"_id": article["_id"]}, {"$set": {"sample": sample_new}})
        print(f"Updated article with ID {article['_id']} to new sample: {sample_new}")


def modify_sample_in_summaries():
    cursor = repo_summaries.get_articles({"sample": sample_id})
    for summary in cursor:
        repo_summaries.update_articles({"_id": summary["_id"]}, {"$set": {"sample": sample_new}})
        print(f"Updated summary with ID {summary['_id']} to new sample: {sample_new}")


def create_metadata():
    doc = repo_metadata.get_one_metadata({"_id": sample_id})
    insert = repo_metadata.insert_metadata(
        {"_id": sample_new,
         "gathering_sample_startedAt": {"$date": {"$numberLong": doc.get("gathering_sample_startedAt")}},
         "batch": {"$numberInt": "1"}, "prev": "1-2025-08-12", "next": "",
         "articles_processed": doc.get("articles_processed"),
         "gathering_sample_finishedAt": {"$date": {"$numberLong": doc.get("gathering_sample_finishedAt")}},
         "sentiment_distribution": doc.get("sentiment_distribution"),
         "topic_distribution": doc.get("topic_distribution")})
    if insert:
        print(f"Metadata for sample {insert} inserted successfully.")


def delete_metadata():
    repo_metadata.delete_metadata_one({"_id": sample_id})
    print(f"Metadata  deleted successfully.")


def update_metadata():
    metadata = repo_metadata.get_metadata_broad({"_id": "1-2025-08-11"})
    for doc in metadata:
        repo_metadata.update_metadata({"_id": doc["_id"]},
                                      {"$set": {
                                          "gathering_sample_startedAt": datetime.datetime(2025, 8, 16, 17, 40, 41,
                                                                                          352000),
                                          "batch": 1,
                                          "prev": "2-2025-08-10",
                                          "next": "1-2025-08-12",
                                          "articles_processed": {'successfully': 83, 'unsuccessfully': 0, 'skipped': 1},
                                          "gathering_sample_finishedAt": datetime.datetime(2025, 8, 16, 18, 20, 11,
                                                                                           227000),
                                          "sentiment_distribution": [{'label': 'NEGATIVE', 'percentage': 60.24},
                                                                     {'label': 'POSITIVE', 'percentage': 39.76}],
                                          'topic_distribution': [{'label': 'technology and innovation',
                                                                  'percentage': 21.69},
                                                                 {'label': 'business and finance',
                                                                  'percentage': 12.05},
                                                                 {'label': 'sports and athletics',
                                                                  'percentage': 12.05},
                                                                 {'label': 'crime and justice',
                                                                  'percentage': 12.05},
                                                                 {'label': 'entertainment and celebrity',
                                                                  'percentage': 12.05},
                                                                 {'label': 'politics and government',
                                                                  'percentage': 9.64},
                                                                 {'label': 'climate and environment',
                                                                  'percentage': 4.82},
                                                                 {'label': 'war and conflict',
                                                                  'percentage': 4.82},
                                                                 {'label': 'science and research',
                                                                  'percentage': 3.61},
                                                                 {'label': 'travel and tourism',
                                                                  'percentage': 2.41},
                                                                 {'label': 'health and medicine',
                                                                  'percentage': 2.41},
                                                                 {'label': 'education and schools',
                                                                  'percentage': 2.41}]
                                      }})


def get_metadata():
    metadata = repo_metadata.get_metadata_broad({"_id": "1-2025-08-11"})
    for doc in metadata:
        print(doc)


def get_summaries_by_sample():
    sample_target = "1-2025-08-11"
    summaries = repo_summaries.get_articles({"sample": sample_target})
    for summary in summaries:
        print(summary.get("summary"))
        print("\n")


def date_and_sample():
    result = repo_daily_trends.get_daily_trends({})
    for doc in result:
        substring_date = doc.get("sample", "").split("-")
        substring_date_string = "-".join(substring_date[1:4])
        repo_daily_trends.update_daily_trends({"_id": doc.get("_id")},
                                              {"$set": {"date": substring_date_string}})
        # Print the updated document ID, sample, and substring date string


def show_daily_trends():
    result = repo_daily_trends.get_daily_trends({})
    for doc in result:
        print(f"Sample: {doc.get('sample')}, Date: {doc.get('date')}")


if __name__ == "__main__":
    date_and_sample()
    show_daily_trends()
