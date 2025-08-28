import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_uri = os.getenv('MONGODB_URI')
if not mongo_uri:
    raise Exception('MONGODB_URI not found in .env')

client = MongoClient(mongo_uri)
db = client['Discordbot']
collection = db['user']

user_id = 0  # You can change this to any user_id you want

# Try to find the user
user = collection.find_one({'user_id': user_id})

if user:
    # If user exists, increment count
    new_count = user.get('count', 0) + 1
    collection.update_one({'user_id': user_id}, {'$set': {'count': new_count}})
    print(f"User {user_id} exists. Count incremented to {new_count}.")
else:
    # If user does not exist, create with count 0
    collection.insert_one({'user_id': user_id, 'count': 0})
    print(f"User {user_id} created with count 0.")
