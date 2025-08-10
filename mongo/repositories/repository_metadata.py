class RepositoryMetadata:

    def __init__(self, db):
        self.collection = db["metadata"]

    def insert_metadata(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_metadata(self, param, sorting=None):
        if sorting:
            return self.collection.find(param, sort=sorting)
        return  self.collection.find(param)

    def get_one_metadata(self, param, sorting=None):
        if sorting:
            return self.collection.find_one(param, sort=sorting)
        return self.collection.find_one(param)

    def get_metadata_broad(self, filter_param, projection_param=None):
        return self.collection.find(filter_param, projection=projection_param)

    def setup_indexes(self):
        index_name = self.collection.create_index("is_articles_processed")
        print(f"✅ Index '{index_name}' created successfully on 'is_articles_processed'")

    def update_metadata(self, selector, update_data):
        result = self.collection.update_one(selector, update_data)
        return result

    def delete_metadata_many(self, selector):
        result = self.collection.delete_many(selector)
        return result.deleted_count

    def delete_metadata_one(self, selector):
        result = self.collection.delete_many(selector)
        return result.deleted_count

    def count_all_documents(self):
        return self.collection.count_documents({})
