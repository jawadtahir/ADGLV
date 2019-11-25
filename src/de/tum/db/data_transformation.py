'''
Created on Oct 29, 2019

@author: foobar
'''
import os

from pymongo.mongo_client import MongoClient

from de.tum.util.Constants import *


mapping = {
    "102.133.224.25": "AFNORTHSAFH00",
    "52.172.128.136": "APCENTINFH03",
    "40.126.246.254": "APEASTAUSFH01",
    "13.76.190.44": "APSEASTASFH02",
    "52.232.62.247": "EUWESTEUFH05",
    "52.168.130.56": "USEASTUS1FH04",
}

if __name__ == '__main__':
    mongo_host = os.environ.get(MONGO_HOST, "localhost")
    mongo_port = os.environ.get(MONGO_PORT, "27017")

    with MongoClient(mongo_host, int(mongo_port)) as db_client:
        db = db_client['thesis']
        collection = db['trans_data']
        for document in collection.find().batch_size(10000):
            dest_ip = document["dest_name"].strip()
            dest_name = mapping.get(dest_ip)
            if dest_name is not None:
                updated = collection.update_one({"_id": document["_id"]}, {
                    "$set": {
                        "dest_name": dest_name
                    }})
