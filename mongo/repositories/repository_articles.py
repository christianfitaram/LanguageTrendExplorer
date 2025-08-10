from bson import ObjectId


class RepositoryArticles:
    def __init__(self, db):
        self.collection = db["articles"]

    def create_articles(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_articles(self, params, projection=None):
        if projection:
            result = self.collection.find(params, projection)
        else:
            result = self.collection.find(params)
        return result

    def get_distinct_samples(self, sample_str):
        regex_filter = {"sample": {"$regex": sample_str, "$options": "i"}}
        return self.collection.distinct("sample", regex_filter)

    def get_one_article(self, params, sorting=None):
        result = self.collection.find_one(params, sort=sorting)
        return result

    def update_articles(self, selector, update_data):
        result = self.collection.update_one(selector, update_data)
        return result.modified_count

    def delete_articles(self, selector):
        result = self.collection.delete_many(selector)
        return result.deleted_count

    def setup_indexes(self):
        compound_index = self.collection.create_index(
            [("isCleaned", 1), ("sample", 1)]
        )
        print(f"✅ Compound index '{compound_index}' created on 'isCleaned + sample'")
