import pymongo
import os

# Try both lowercase 'a' and uppercase 'A' passwords
passwords = ["Admin123", "admin123"]
base_uri = "mongodb+srv://admin:{password}@bookstore.u9bheuh.mongodb.net/?appName=bookstore"

for pwd in passwords:
    uri = base_uri.format(password=pwd)
    print(f"\n--- Testing with password: {pwd} ---")
    try:
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force a command to trigger connection
        print("Pinging...")
        client.admin.command('ping')
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
