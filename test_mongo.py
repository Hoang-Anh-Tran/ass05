import pymongo
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("MONGO_URI")
print(f"Testing connection to: {uri}")
try:
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
    print(client.server_info())
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
