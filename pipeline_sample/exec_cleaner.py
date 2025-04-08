from datetime import datetime, time, UTC
from mongo.update import update_articles, update_metadata
from mongo.insert import insert_clean_articles
from mongo.find import find_articles
import spacy

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")


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


def clean_articles(sample_temp):
    data_sample = sample_temp
    """
    Processes articles collected today with the specified batch number by extracting nouns
    and storing the cleaned data in the 'clean_articles' collection. Each article is processed
    and inserted individually to optimize memory usage.

    Args:
        batch_number (int): The batch number of the articles to process.
    """
    # Define the time range for today
    today = datetime.now(UTC).date()
    start_of_day = datetime.combine(today, time.min, UTC)
    end_of_day = datetime.combine(today, time.max, UTC)

    # Query for articles scraped today with the specified batch number
    raw_articles = find_articles("all", {
        "scraped_at": {
            "$gte": start_of_day,
            "$lt": end_of_day
        },
        "batch": data_sample["batch_number"],
        "isCleaned": False,
    })

    update_metadata({"_id": data_sample["metadata_id"]}, {
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
            "sample": data_sample["metadata_id"],
            "nouns": nouns
        }
        print(cleaned_doc)

        # Updating isCleaned from articles to true
        update_articles({"_id": article["_id"]}, {"$set": {"isCleaned": True}})

        # Insert the cleaned document into the 'clean_articles' collection
        insert_clean_articles(cleaned_doc)

    update_metadata({"_id": data_sample["metadata_id"]}, {
        "$set": {"cleaning_sample_finishedAt": datetime.now(UTC)}})
    print(f"Processing and insertion of cleaned articles for batch {data_sample["batch_number"]} completed.")
    return data_sample["metadata_id"]


if __name__ == "__main__":
    # Example usage: process articles from batch number 1
    clean_articles(sample_temp={}
   )
