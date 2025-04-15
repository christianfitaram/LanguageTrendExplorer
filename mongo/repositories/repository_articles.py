from bson import ObjectId


class RepositoryArticles:
    def __init__(self, db):
        self.collection = db["articles"]

    def create_articles(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_articles(self, params):
        result = self.collection.find(params)
        return result

    def get_one_article(self, params, sorting=None):
        result = self.collection.find_one(params, sort=sorting)
        return result

    def update_articles(self, selector, update_data):
        result = self.collection.update_one(selector, update_data)
        return result.modified_count

    def setup_indexes(self):
        compound_index = self.collection.create_index(
            [("isCleaned", 1), ("sample", 1)]
        )
        print(f"✅ Compound index '{compound_index}' created on 'isCleaned + sample'")
