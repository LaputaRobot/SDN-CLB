"""
author:Yuegb
date:2021,05,06
"""
from pymongo import MongoClient
client = MongoClient('192.168.136.149', 27017)
#client = MongoClient('mongodb://18.219.185.25:27017/')
db = client.elastiCon #db name: elastiCon
controllers = db.controllers #Document name: controllers - To keep track of controller data
flags = db.flags #Document name: flags - To track various flags during migration
gen_id = db.gen_id
cmf = db.cmf

def get_gen_id(ofp,role):
    """
    Generates a gen_id to be used for Role Request
    """
    entry = gen_id.find_one()
    if not entry:
        # gen_id document doesn't exist, Creating one...
        id = {'value': '1'}
        gen_id.insert_one(id)
        value = 1
    else:
        value = entry['value']
    print("get gen_id returns {}".format(value))
    if(role!=ofp.OFPCR_ROLE_NOCHANGE):
        val_new = int(value) + 1
        gen_id.update_one({'value': str(value)}, {'$set': {'value': str(val_new)}})
        print("gen id val updated to {}".format(val_new))
    return int(value)