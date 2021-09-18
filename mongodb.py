import pymongo
from datetime import datetime
from bson.objectid import ObjectId


def user_lookup(asurite):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    users = client.harmonizer.users
    finder = users.find_one({"asurite": asurite})
    if finder is not None:
        return finder
    else:
        new_user = {"asurite": asurite, "created": datetime.now()}
        result = users.insert_one(new_user)
        new_user["_id"] = result.inserted_id
        return new_user


def jobs_lookup(user_data):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    jobs = client.harmonizer.jobs
    finder = list(jobs.find({"user_id": user_data["_id"]}))
    for job in finder:
        job["id"] = str(job["_id"])
    return finder


def single_job_lookup(user_data, job_id):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    jobs = client.harmonizer.jobs
    try:
        found_job = jobs.find_one(
            {"user_id": user_data["_id"], "_id": ObjectId(job_id)}
        )
    except:
        return None
    else:
        if found_job is not None:
            return found_job
        else:
            return None


def insert_coll_job(user_package, meta_package, data_package):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    jobs = client.harmonizer.jobs
    splitsville = (data_package["col_id"]).split("||")
    new_job_rec = {
        "user_id": user_package["_id"],
        "created": datetime.now(),
        "collection_id": splitsville[0],
        "collection_name": splitsville[1],
        "repo": data_package["repo_name"],
        "docs": meta_package,
        "job_name": data_package["job_name"],
    }
    result = jobs.insert_one(new_job_rec)
    if result.acknowledged:
        new_job_rec["user_id"] = str(user_package["_id"])
        new_job_rec["_id"] = str(result.inserted_id)
        return {"status": "insert", "data": [new_job_rec]}
    else:
        return None


def insert_item_job(user_package, meta_package, data_package):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    jobs = client.harmonizer.jobs
    new_job_rec = {
        "user_id": user_package["_id"],
        "created": datetime.now(),
        "item_id": data_package["item_id"],
        "item_name": meta_package["title"],
        "repo": data_package["repo_name"],
        "docs": meta_package["headings"],
        "job_name": data_package["job_name"],
    }
    result = jobs.insert_one(new_job_rec)
    if result.acknowledged:
        new_job_rec["user_id"] = str(user_package["_id"])
        new_job_rec["_id"] = str(result.inserted_id)
        return {"status": "success", "data": [new_job_rec]}
    else:
        return None


def kill_job(user_package, data_package):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    jobs = client.harmonizer.jobs
    result = jobs.delete_one(
        {"_id": ObjectId(data_package["job_id"]), "user_id": user_package["_id"]}
    )
    if result.acknowledged:
        return True
    else:
        return False


def kill_rec_from_job(user_package, job_id, rec_id):
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    jobs = client.harmonizer.jobs
    job_package = single_job_lookup(user_package, job_id)
    updated_recs_list = [int(job_id) for job_id in job_package["docs"]]
    updated_recs_list.remove(int(rec_id))
    filter = {"user_id": user_package["_id"], "_id": job_package["_id"]}
    new_values = {"$set": {"docs": updated_recs_list}}
    result = jobs.update_one(filter, new_values)
    if result.acknowledged:
        return True
    else:
        return False


def get_tokens():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    tokens = client.harmonizer.tokens
    finder = list(tokens.find())
    temp = {}
    for token in finder:
        if "keep" in token:
            temp["keep"] = token["keep"]
        if "prism" in token:
            temp["prism"] = token["prism"]
    return temp
