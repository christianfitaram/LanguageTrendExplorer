from bson import ObjectId


class RepositoryMetadata:

    def __init__(self, db):
        self.collection = db["metadata"]

    def insert_metadata(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_metadata(self,param):
        result = self.collection.find(param)
        return result

    def setup_indexes(self):
        index_name = self.collection.create_index("is_articles_processed")
        print(f"✅ Index '{index_name}' created successfully on 'is_articles_processed'")

    def update_metadata(self, selector, update_data):
        self.collection.update_one(selector, update_data)
