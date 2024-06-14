from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI, Depends, Response, status, HTTPException, Depends
import os
import pprint
from pymongo import MongoClient
from bson.objectid import ObjectId
from mitigation_action_class import mitigation_action_model, MitigationIdRequestBody, User
from mitigation_regex_control import playbook_creator
import socket
from hashing import Hash
from oauth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jwttoken import create_access_token
from send_mitigation_rules import simple_uploader

try:
    load_dotenv(find_dotenv())
    db_username = os.environ.get("MONGODB_USERNAME")
    db_password = os.environ.get("MONGODB_PWD")
    db_name = os.environ.get("MONGODB_IP")
    db_port = os.environ.get("MONGODB_PORT")
    db_auth = os.environ.get("MONGODB_AUTH")
    db_direct_conn = os.environ.get("MONGODB_CONN")
    db_timeout = os.environ.get("MONGODB_TIMEOUT")
    cluster_name = os.environ.get("MONGODB_CLUSTERNAME")
    app_name = os.environ.get("MONGODB_APPNAME")

    #connection_str = f"""mongodb+srv://{username}:{password}@{cluster_name}.mongodb.net/?retryWrites=true&w=majority&appName={app_name}"""
    #connection_str = f"""mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.2.1"""
    connection_str = f"""mongodb://{db_username}:{db_password}@{db_name}:{db_port}/?authSource={db_auth}&directConnection={db_direct_conn}&serverSelectionTimeoutMS={db_timeout}"""

    client = MongoClient(connection_str)

    #dbs = client.list_database_names()
    mitigations_db = client.mitigation_actions
    users_db = client.users
    mitigation_actions_collection = mitigations_db.mitigation_actions
    users_collections = users_db.users
    #collections = mitigations_db.list_collection_names()
except Exception as e:
    print(f"Something went wrong with the connection. Error {e}")

printer = pprint.PrettyPrinter()


rtr_api = FastAPI()

rtr_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@rtr_api.get("/")
def root():
    return {"message": "Welcome to RTR"}

@rtr_api.post('/register')
def create_user(request:User):
	hashed_pass = Hash.bcrypt(request.password)
	user_object = dict(request)
	user_object["password"] = hashed_pass
	user_id = users_collections.insert_one(user_object)
	# print(user)
	return {"res":"created"}

@rtr_api.post('/login')
def login(request:OAuth2PasswordRequestForm = Depends()):
	user = users_collections.find_one({"username":request.username})
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f'No user found with this {request.username} username')
	if not Hash.verify(user["password"],request.password):
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail = f'Wrong Username or password')
	access_token = create_access_token(data={"sub": user["username"] })
	return {"access_token": access_token, "token_type": "bearer"}


@rtr_api.get("/actions")
def get_all_mitigation_actions(token : OAuth2PasswordRequestForm = Depends(get_current_user)):
    stored_mitigation_actions = mitigation_actions_collection.find({}, {'_id': 0})
    #print(stored_mitigation_actions)
    actions = [action for action in stored_mitigation_actions]
    for action in stored_mitigation_actions:
        printer.pprint(action)
   
    return {"stored actions":actions}

@rtr_api.get("/action_by_id/{intent_id}")
def get_action_based_on_id(intent_id: str, token:OAuth2PasswordRequestForm = Depends(get_current_user)):
    #print(mitigation_id)
    
    try:
        #_id = ObjectId(mitigation_id)
        mitigation_action = mitigation_actions_collection.find_one({"intent_id": intent_id}, {'_id': 0})
        if mitigation_action is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action with id: {intent_id} was not found")
        print(mitigation_action)
        #actions = convert_id(mitigation_action)
        return {"Action details": mitigation_action}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action with id: {intent_id} was not found")


@rtr_api.post("/actions", status_code=status.HTTP_201_CREATED)
def register_new_action(new_action: mitigation_action_model, token:OAuth2PasswordRequestForm = Depends(get_current_user)):
    #print(f"Command : {new_action.command}, Intent type: {new_action.intent_type}, Threat: {new_action.threat}, Attacked Host: {new_action.attacked_host}, Mitigation Host: {new_action.mitigation_host}, Action: {new_action.action}, Duration: {new_action.duration}, Intent_id: {new_action.intent_id}")

    try:
        if new_action.command == 'add':
            existing_document = mitigation_actions_collection.find_one(new_action.dict())
            if existing_document:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"An identical document was found")
                
            inserted_action = mitigation_actions_collection.insert_one(new_action.dict())
            inserted_action_id = new_action.intent_id
            playbook = playbook_creator(new_action)
            complete_playbook = playbook.fill_in_ansible_playbook()
            action_definition = "Service Modification"
            service = "DNS"

            #simple_uploader(inserted_action_id, action_definition, service, complete_playbook)
            #return {"New action unique id is":inserted_action_id}

            simple_uploader(new_action.mitigation_host, inserted_action_id, action_definition, service, complete_playbook)
            #return {"New action unique id is":inserted_action_id}
            return "action created successfully"
        
        if new_action.command == 'delete':
            
                #_id = ObjectId(id)
            deleted_mitigation_action = mitigation_actions_collection.find_one_and_delete({"intent_id": new_action.intent_id})
            if deleted_mitigation_action == None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action with id: {new_action.intent_id} was not found")
            return "action deleted successfully"
            
    except Exception as e:
            print(f"I could not store or delete a new action to the database. Error {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Document failed validation")


#@rtr_api.delete("/actions/{id}", status_code=status.HTTP_204_NO_CONTENT)
#def delete_action(id: str, token:OAuth2PasswordRequestForm = Depends(get_current_user)):
#    
#    try:
#        _id = ObjectId(id)
#        deleted_mitigation_action = mitigation_actions_collection.find_one_and_delete({"_id": _id})
#        if deleted_mitigation_action == None:
#            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"post with id: {id} was not found")
#        return "Action deleted from RTR database"
#        
#    except Exception as e:
#        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Something went wrong")


def convert_id(action):
    """Convert MongoDB document for serialization."""
    # Convert ObjectId to string for serialization
    action["_id"] = str(action["_id"])
    return action
