import os
import pymongo
database = "Discordbot"
collection_name = "user"

def connection():
    mongo_uri = os.getenv('MONGODB_URI')
    client = pymongo.MongoClient(mongo_uri)
    return client

def get_user_collection():
    db = connection()[database]
    collection = db[collection_name]
    return collection

def get_user(user_id):
    try:
        collection = get_user_collection()
        user = collection.find_one({"user_id": user_id})
        # if not have, create one with user id
        if not user:
            user = {"user_id": user_id}
            collection.insert_one(user)
        return ["Success", user]
    except Exception as e:
        print(f"Error getting user: {e}")
        return ["Failed", None]

def get_user_data(user_id, variable):
    try:
        collection = get_user_collection()
        user = collection.find_one({"user_id": user_id})
        if user:
            status = "Success"
            return [status,user.get(variable, 0)]
        else:
            status = "Failed"
            return [status, 0]
    except Exception as e:
        print(f"Error getting user data: {e}")
        return ["Failed", 0]

def add_user_data(user_id, variable, value):
    try:
        collection = get_user_collection()
        user = collection.find_one({"user_id": user_id})
        if not user:
            user = {"user_id": user_id, variable: 0}
            collection.insert_one(user)
        if variable not in user:
            user[variable] = 0
        user[variable] += value
        collection.update_one({"user_id": user_id}, {"$set": {variable: user[variable]}}, upsert=True)
        return ["Success", user[variable]]
    except Exception as e:
        
        print(f"Error adding user data: {e}")
        return ["Failed", 0]
    
    # 
    