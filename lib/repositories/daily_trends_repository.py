# lib/repositories/daily_trends_repository.py
from typing import Any, Dict, Iterable, Optional
from lib.db.mongo_client import get_db
from pymongo.collection import Collection


class DailyTrendsRepository:
    def __init__(self) -> None:
        self.collection: Collection = get_db()["daily_trends"]

    def insert_daily_trends(self, doc: Dict[str, Any]) -> str:
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def get_daily_trends(self, params: Dict[str, Any]):
        return self.collection.find(params)

    def get_one_daily_trends(self, params: Dict[str, Any]):
        return self.collection.find_one(params)

    def delete_daily_trends(self, selector: Dict[str, Any]) -> int:
        result = self.collection.delete_many(selector)
        return result.deleted_count

    def delete_daily_trend(self, selector: Dict[str, Any]) -> int:
        result = self.collection.delete_one(selector)
        return result.deleted_count

    def update_daily_trends(self, selector: Dict[str, Any], update_data: Dict[str, Any]) -> int:
        result = self.collection.update_one(selector, update_data)
        return result.modified_count
