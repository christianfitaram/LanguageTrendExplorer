from bson import ObjectId


class RepositoryLinkPool:

    def __init__(self, db):
        self.collection = db["link_pool"]

    def insert_link(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_link(self,param):
        result = self.collection.find(param)
        return result

    def is_link_successfully_processed(self, url):
        result = self.collection.find_one({"url": url})
        return result.get("is_articles_processed", False) if result else False

    def setup_indexes(self):
        index_name = self.collection.create_index("is_articles_processed")
        print(f"✅ Index '{index_name}' created successfully on 'is_articles_processed'")

    def update_link_in_pool(self, selector, update_data):
        result = self.collection.update_one(selector, update_data)
        return result.modified_count
