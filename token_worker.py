from bson.objectid import ObjectId
import pymongo
import requests as r
import json
import os
from datetime import datetime


def initialize():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    return client.harmonizer.tokens


def token_lookup(token_id):
    tokens = initialize()
    found_job = tokens.find_one({"_id": ObjectId(token_id)})
    if found_job is not None:
        return found_job
    else:
        return None


def token_update(repo, token_package, token):
    tokens = initialize()
    filter = {"_id": token_package["_id"]}
    new_values = {"$set": {repo: token, "updated": datetime.now()}}
    result = tokens.update_one(filter, new_values)
    if result.acknowledged:
        return True
    else:
        return False


def main():
    auth_doc_dir_path = os.path.dirname(os.path.realpath(__file__))
    auth_doc = os.path.join(auth_doc_dir_path, "token_auth.json")
    with open(auth_doc, "r") as j:
        auth_doc_json = json.load(j)

    for repo in ["keep", "prism"]:
        with r.Session() as session:
            payload = {
                "name": auth_doc_json["name"],
                "pass": auth_doc_json["pass"],
                "form_build_id": auth_doc_json[repo]["form_build_id"],
                "form_id": auth_doc_json["form_id"],
                "op": auth_doc_json["op"],
            }
            x = session.post(
                f"https://{repo}.lib.asu.edu/user/external/login", data=payload
            )
            token = (session.get(f"https://{repo}.lib.asu.edu/jwt/token")).json()[
                "token"
            ]
        existing_token = token_lookup(auth_doc_json[repo]["_id"])
        result = token_update(repo, existing_token, token)
        if not result:
            print(
                f"{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} -- Token update not acknowledged"
            )


if __name__ == "__main__":
    main()
