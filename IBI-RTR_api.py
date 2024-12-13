from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI,Body, Depends, status, HTTPException
from mitigation_action_class import mitigation_action_model, UpdateActionStatusRequest, User
from mitigation_regex_control import playbook_creator
from hashing import Hash
from oauth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jwttoken import create_access_token
from send_mitigation_rules import simple_uploader
from pymongo import MongoClient
from typing import Dict
import os
import uuid

# Load environment variables
load_dotenv(find_dotenv())

# Initialize FastAPI and CORS settings
rtr_api = FastAPI()
rtr_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the OAuth2 scheme for FastAPI to include it in Swagger documentation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# MongoDB Connection
db_username = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
db_password = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "qwerty1234")
mongo_client = MongoClient(f"mongodb://{db_username}:{db_password}@mongodb:27017/")
db = mongo_client["rtr_database"]  # Define database
users_collection = db["users"]  # Define users collection

# In-memory storage for mitigation actions
mitigation_actions: Dict[str, dict] = {}

@rtr_api.get("/")
def root():
    return {"message": "Welcome to RTR"}

@rtr_api.post('/register')
def create_user(request: User):
    # Check if user already exists in MongoDB
    if users_collection.find_one({"username": request.username}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    # Hash the password and store the user in MongoDB
    hashed_pass = Hash.bcrypt(request.password)
    user_object = dict(request)
    user_object["password"] = hashed_pass
    users_collection.insert_one(user_object)
    
    return {"res": "User created successfully"}

@rtr_api.post('/login')
def login(request: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found with this username")
    if not Hash.verify(user["password"], request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@rtr_api.get("/actions")
def get_all_mitigation_actions(token: str = Depends(oauth2_scheme)):
    # Verify the token by calling get_current_user (assuming it handles token verification)
    current_user = get_current_user(token)
    return {"stored_actions": list(mitigation_actions.values())}

@rtr_api.get("/action_by_id/{intent_id}")
def get_action_based_on_id(intent_id: str, token: str = Depends(oauth2_scheme)):
    # Verify the token by calling get_current_user
    current_user = get_current_user(token)
    action = mitigation_actions.get(intent_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action with ID {intent_id} not found")
    return {"Action details": action}

@rtr_api.post("/actions", status_code=status.HTTP_201_CREATED)
def register_new_action(
    new_action: mitigation_action_model,
    token: str = Depends(lambda: "dummy_token")  # Replace with oauth2_scheme
    ):
    current_user = {"username": "dummy_user"}  # Simulate user

    # Use intent_id directly since action_id is removed
    intent_id = new_action.intent_id

    if new_action.command == "add":
        if intent_id in mitigation_actions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An identical action already exists",
            )

        # Store action in memory with initial status
        mitigation_actions[intent_id] = {
            "intent_id": intent_id,
            "command": new_action.command,
            "intent_type": new_action.intent_type,
            "threat": new_action.threat,
            "attacked_host": new_action.attacked_host,
            "mitigation_host": new_action.mitigation_host,
            "action": new_action.action,
            "duration": new_action.duration,
            "status": "pending",
            "info": "Action created, pending execution",
        }

        return {"message": "Action created", "intent_id": intent_id}

@rtr_api.post("/update_action_status", status_code=status.HTTP_200_OK)
def update_action_status(status_update: UpdateActionStatusRequest):
    intent_id = status_update.intent_id  # Changed to use intent_id
    action_status = status_update.status
    additional_info = status_update.info

    if not intent_id or not action_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing intent_id or status")

    if intent_id not in mitigation_actions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    mitigation_actions[intent_id]["status"] = action_status
    mitigation_actions[intent_id]["info"] = additional_info

    return {"message": "Action status updated successfully"}