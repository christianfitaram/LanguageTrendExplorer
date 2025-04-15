from datetime import datetime, UTC
from mongo.mongodb_client import db
from mongo.repositories.repository_metadata import RepositoryMetadata
from mongo.repositories.repository_articles import RepositoryArticles
from mongo.repositories.repository_clean_articles import RepositoryCleanArticles
import spacy

from utils.utils_functions import is_valid_sample

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")
repo_articles = RepositoryArticles(db)
repo_metadata = RepositoryMetadata(db)
repo_clean_articles = RepositoryCleanArticles(db)


def extract_nouns(text):
    """
    Extracts lemmatized nouns from the provided text using spaCy.
    Args:
        text (str): The input text from which to extract nouns.

    Returns:
        list: A list of lemmatized, lowercase nouns found in the text.
    """
    doc = nlp(text)
    return [token.lemma_.lower() for token in doc if token.pos_ == "NOUN" and not token.is_stop and token.is_alpha]


def clean_articles(sample_temp=None):
    """
    Processes articles collected today with the specified batch number by extracting nouns
    and storing the cleaned data in the 'clean_articles' collection. Each article is processed
    and inserted individually to optimize memory usage.

    Args:
        sample_temp (str): The sample id from the batch of articles to process.
    """
    # In case the sample id is not provided by the pipeline
    if sample_temp is None:
        sample_temp = input("Enter the sample string (e.g. '1-2025-04-12'): ")
        while is_valid_sample(sample_temp) is False:
            sample_temp = input("Incorrect format (e.g. '1-2025-04-12'): ")

    # Query for articles scraped today with the specified batch number
    raw_articles = repo_articles.get_articles({
        "sample": sample_temp,
    })

    repo_metadata.update_metadata({"_id": sample_temp}, {
        "$set": {"cleaning_sample_startedAt": datetime.now(UTC)}})
    # Process and insert each article individually
    for article in raw_articles:
        if article["text"] is None:
            continue

        nouns = extract_nouns(article["text"])
        cleaned_doc = {
            "title": article["title"],
            "url": article["url"],
            "source": article["source"],
            "scraped_at": article["scraped_at"],
            "batch": article["batch"],
            "isProcessed": False,
            "topic": article["topic"],
            "sentiment": article["sentiment"],
            "sample": sample_temp,
            "nouns": nouns
        }


        # Updating isCleaned from articles to true
        repo_articles.update_articles({"_id": article["_id"]}, {"$set": {"isCleaned": True}})
        print(cleaned_doc)
        # Insert the cleaned document into the 'clean_articles' collection
        repo_clean_articles.create_articles(cleaned_doc)

    repo_metadata.update_metadata({"_id": sample_temp}, {
        "$set": {"cleaning_sample_finishedAt": datetime.now(UTC)}})
    print(f"Processing and insertion of cleaned articles for batch {sample_temp} completed.")
    return sample_temp


if __name__ == "__main__":
    # Example usage: process articles from batch number 1
    clean_articles()
