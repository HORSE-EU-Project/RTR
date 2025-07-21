from pymongo import MongoClient
from ..core.settings import settings


class DatabaseConnection:
    """MongoDB database connection manager"""
    
    def __init__(self):
        self._client = None
        self._db = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        if self._client is None:
            self._client = MongoClient(settings.mongo_url)
            self._db = self._client[settings.MONGO_DATABASE]
        return self._db
    
    @property
    def db(self):
        """Get database instance"""
        if self._db is None:
            self.connect()
        return self._db
    
    @property
    def users_collection(self):
        """Get users collection"""
        return self.db["users"]
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


# Global database instance
db_connection = DatabaseConnection()
