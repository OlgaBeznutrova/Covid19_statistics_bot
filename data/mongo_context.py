from datetime import datetime, timedelta
from pymongo import MongoClient


class MongoDBContext:
    """Mongo database context class"""

    # class constructor
    def __init__(self, connection_string, db_name):
        try:
            self.connection_string = connection_string
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            self.db_name = db_name
        except Exception as e:
            raise e

    # save country queried by user
    def save_country_query(self, country_name, user_name, is_known=True):
        db = self.client[self.db_name]
        if is_known:
            collection = db.country_queries
        else:
            collection = db.unknown_queries
        collection.insert_one(
            {"date": datetime.now(),
             "country": country_name,
             "username": user_name}
        )

    # get users queries method
    def get_users_queries(self):
        db = self.client[self.db_name]
        country_queries = db.country_queries
        pipeline = [
            {
                "$facet": {
                    "countries": [
                        {"$sortByCount": "$country"},
                        {"$limit": 5}
                    ],
                    "users": [
                        {"$sortByCount": "$username"},
                        {"$limit": 5}
                    ]
                }
            }
        ]
        stats_for_users = country_queries.aggregate(pipeline)
        return list(stats_for_users)

    # get users and countries for the last few days
    def get_last_days_info(self, days):
        start_date = datetime.now() - timedelta(days=days)
        db = self.client[self.db_name]
        country_queries = db.country_queries
        last_days_info = country_queries.aggregate([
            {
                "$facet": {
                    "unique_users_before_days": [{"$match": {"date": {"$lt": start_date}}},
                                                 {"$group": {"_id": "$username"}}],
                    "unique_users_requested_days": [{"$match": {"date": {"$gte": start_date}}},
                                                    {"$group": {"_id": "$username"}}],
                    "unique_countries_before_days": [{"$match": {"date": {"$lt": start_date}}},
                                                     {"$group": {"_id": "$country"}}],
                    "unique_countries_requested_days": [{"$match": {"date": {"$gte": start_date}}},
                                                        {"$group": {"_id": "$country"}}],
                }
            }
        ])
        return list(last_days_info)
