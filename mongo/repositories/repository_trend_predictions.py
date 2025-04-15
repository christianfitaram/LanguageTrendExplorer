
class RepositoryTrendPredictions:

    def __init__(self, db):
        self.collection = db["metadata"]

    def insert_trend_prediction(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_trend_prediction(self, param):
        result = self.collection.find(param)
        return result

    def update_trend_prediction(self, selector, update_data):
        self.collection.update_one(selector, {"$set": update_data})
