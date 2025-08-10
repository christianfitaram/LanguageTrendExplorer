class RepositoryCleanArticles:
    def __init__(self, db):
        self.collection = db["clean_articles"]

    def create_articles(self, article_data):
        result = self.collection.insert_one(article_data)
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

    def delete_articles(self, selector):
        result = self.collection.delete_many(selector)
        return result.deleted_count

    def setup_indexes(self):
        compound_index = self.collection.create_index(
            [("isCleaned", 1), ("sample", 1)]
        )
        print(f"✅ Compound index '{compound_index}' created on 'isCleaned + sample'")
