from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, Response, status, HTTPException
import os
import pprint
from pymongo import MongoClient
from bson.objectid import ObjectId
from mitigation_action_class import mitigation_action_model, MitigationIdRequestBody
from mitigation_regex_control import playbook_creator
import socket

try:
    load_dotenv(find_dotenv())
    username = os.environ.get("MONGODB_USERNAME")
    password = os.environ.get("MONGODB_PWD")
    cluster_name = os.environ.get("MONGODB_CLUSTERNAME")
    app_name = os.environ.get("MONGODB_APPNAME")
    connection_str = f"""mongodb+srv://{username}:{password}@{cluster_name}.mongodb.net/?retryWrites=true&w=majority&appName={app_name}"""
    #connection_str = f"""mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.2.1"""
    client = MongoClient(connection_str)

    dbs = client.list_database_names()
    mitigations_db = client.mitigation_actions
    mitigation_actions_collection = mitigations_db.mitigation_actions
    collections = mitigations_db.list_collection_names()
except Exception as e:
    print(f"Something went wrong with the connection. Error {e}")

printer = pprint.PrettyPrinter()


rtr_api = FastAPI()


@rtr_api.get("/")
def root():
    return {"message": "Welcome to my API"}

@rtr_api.get("/actions")
def get_all_mitigation_actions():
    stored_mitigation_actions = mitigation_actions_collection.find({})
    #print(stored_mitigation_actions)
    actions = [convert_id(action) for action in stored_mitigation_actions]
    for action in stored_mitigation_actions:
        printer.pprint(action)
   
    return {"stored actions":actions}

@rtr_api.get("/action_by_id/{mitigation_id}")
def get_action_based_on_id(mitigation_id: str):
    print(mitigation_id)
    
    try:
        _id = ObjectId(mitigation_id)
        mitigation_action = mitigation_actions_collection.find_one({"_id": _id})
        print(mitigation_action)
        actions = convert_id(mitigation_action)
        return {"action detail": actions}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")


@rtr_api.post("/actions", status_code=status.HTTP_201_CREATED)
def register_new_action(new_action: mitigation_action_model):
    #print(f"Command : {new_action.command}, Intent type: {new_action.intent_type}, Threat: {new_action.threat}, Attacked Host: {new_action.attacked_host}, Mitigation Host: {new_action.mitigation_host}, Action: {new_action.action}, Duration: {new_action.duration}, Intent_id: {new_action.intent_id}")

    try:
        if new_action.command == 'add':
            existing_document = mitigation_actions_collection.find_one(new_action.dict())
            if existing_document:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"An identical document was found")
                
            inserted_action = mitigation_actions_collection.insert_one(new_action.dict())
            playbook = playbook_creator(new_action)
            playbook.fill_in_ansible_playbook()
            inserted_action_id = str(inserted_action.inserted_id)
            return {"New action unique id is":inserted_action_id}
    except Exception as e:
        print(f"I could not store a new action to the database. Error {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Document failed validation")


@rtr_api.delete("/actions/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_action(id: str):
    
    try:
        _id = ObjectId(id)
        deleted_mitigation_action = mitigation_actions_collection.find_one_and_delete({"_id": _id})
        if deleted_mitigation_action == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
        return "Action deleted from RTR database"
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Something went wrong")


def convert_id(action):
    """Convert MongoDB document for serialization."""
    # Convert ObjectId to string for serialization
    action["_id"] = str(action["_id"])
    return action


