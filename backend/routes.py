from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})
    return ({"count": count}, 200)

@app.route("/song")
def songs():
    """finding all songs"""
    res = list(db.songs.find({}))
    return ({"songs": parse_json(res)}, 200)

@app.route("/song/<int:id>")
def get_song_by_id(id):
    """finding song with id"""
    res = db.songs.find_one({"id": id})

    if res:
        return ({"songs": parse_json(res)}, 200)
    else:
        return ({"message": f"song with {id} not found"},404)

@app.route("/song", methods=["POST"])
def create_song():
    """create one song"""
    data = request.json
    res = db.songs.find_one({"id": data["id"]})

    if res:
        return ({"Message": f"song with id {data['id']} already present"}, 302)
    else:
        inserted = db.songs.insert_one(data)
        return ({"inserted id": parse_json(inserted.inserted_id)}, 201)

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    """update a song"""
    data = request.json

    res = db.songs.find_one({"id": id})

    if res:
        updated = db.songs.update_one({"id": id}, {"$set": data})
        if updated.modified_count == 0:
            return {"message": "song found, but nothing updated"}, 200
        else:
            updated_res = db.songs.find_one({"id": id})
            return parse_json(updated_res), 200
    else:
        return ({"message": "song not found"}, 404)

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    """delete a song"""
    res = db.songs.delete_one({"id": id})

    if res.deleted_count == 0:
        return ({"message": "song not found"},404)
    elif res.deleted_count == 1:
        return ("",204)
    
    return {"message": "Internal server error"}, 500



