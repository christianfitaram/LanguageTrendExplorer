class RepositoryDailyTrends:

    def __init__(self, db):
        self.collection = db["daily_trends"]

    def insert_daily_trends(self, link_data):
        result = self.collection.insert_one(link_data)
        return str(result.inserted_id)

    def get_daily_trends(self, param):
        result = self.collection.find(param)
        return result

    def get_one_daily_trends(self, param):
        result = self.collection.find_one(param)
        return result

    def delete_daily_trends(self, selector):
        result = self.collection.delete_many(selector)
        return result.deleted_count

    def delete_daily_trend(self, selector):
        result = self.collection.delete_one(selector)
        return result.deleted_count

    def update_daily_trends(self, selector, update_data):
        self.collection.update_one(selector, update_data)
