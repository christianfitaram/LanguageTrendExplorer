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

    def delete_link(self, selector):
        """
        Deletes a single document from the link_pool collection based on the selector.

        :param selector: Dictionary specifying which document to delete.
        :return: Number of documents deleted (0 or 1).
        """
        result = self.collection.delete_one(selector)
        return result.deleted_count

    def delete_links(self, selector):
        """
        Deletes all documents matching the selector from the link_pool collection.

        :param selector: Dictionary specifying which documents to delete.
        :return: Number of documents deleted.
        """
        result = self.collection.delete_many(selector)
        return result.deleted_count
