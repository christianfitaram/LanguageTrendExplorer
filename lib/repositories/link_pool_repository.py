# lib/repositories/link_pool_repository.py
from typing import Any, Dict, Optional
from lib.db.mongo_client import get_db
from pymongo.collection import Collection


class LinkPoolRepository:
    def __init__(self) -> None:
        self.collection: Collection = get_db()["link_pool"]

    def insert_link(self, data: Dict[str, Any]) -> str:
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_link(self, params: Dict[str, Any]):
        return self.collection.find(params)

    def is_link_successfully_processed(self, url: str) -> bool:
        doc = self.collection.find_one({"url": url}, projection={"is_articles_processed": 1})
        return bool(doc and doc.get("is_articles_processed", False))

    def setup_indexes(self) -> None:
        name = self.collection.create_index("is_articles_processed")
        print(f"✅ Index '{name}' created successfully on 'is_articles_processed'")

    def update_link_in_pool(self, selector: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        result = self.collection.update_one(selector, update_data)
        return result.modified_count

    def delete_link(self, selector: Dict[str, Any]) -> int:
        result = self.collection.delete_one(selector)
        return result.deleted_count

    def delete_links(self, selector: Dict[str, Any]) -> int:
        result = self.collection.delete_many(selector)
        return result.deleted_count

    def count_all_documents(self) -> int:
        return self.collection.count_documents({})
