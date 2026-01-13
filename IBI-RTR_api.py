from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI,Body, Depends, status, HTTPException
from mitigation_action_class import mitigation_action_model, UpdateActionStatusRequest, User
from mitigation_regex_control import playbook_creator
from hashing import Hash
from oauth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jwttoken import create_access_token
from pymongo import MongoClient
from typing import Dict
import os
import uuid
import asyncio
import threading
import requests
import re
from urllib.parse import urlparse
from config_loader import get_config_loader, reload_configurations

# Load environment variables
load_dotenv(find_dotenv())

# Initialize FastAPI and CORS settings
rtr_api = FastAPI(
    title="RTR API",
    version="1.0.0",
    description="Reliability, Trustworthiness & Resilience Framework API",
)
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

def configure_epem_doc_endpoint():
    """Configure ePEM with the DOC IP and port during startup"""
    try:
        # Get the current domain and determine which ePEM endpoint to configure
        current_domain = os.getenv('CURRENT_DOMAIN', 'CNIT').upper()
        
        if current_domain == 'CNIT':
            epem_endpoint = os.getenv('EPEM_CNIT', 'http://192.168.130.233:5002')
            doc_endpoint = os.getenv('DOC_CNIT', 'http://192.168.130.62:8001')
        elif current_domain == 'UPC':
            epem_endpoint = os.getenv('EPEM_UPC', 'http://10.19.2.20:5002')
            doc_endpoint = os.getenv('DOC_UPC', 'http://10.19.2.19:8001')
        else:
            epem_endpoint = os.getenv('EPEM_CNIT', 'http://192.168.130.233:5002')
            doc_endpoint = os.getenv('DOC_CNIT', 'http://192.168.130.62:8001')
        
        # Parse the DOC endpoint to extract IP and port
        parsed_url = urlparse(doc_endpoint)
        doc_ip = parsed_url.hostname
        doc_port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        doc_path = parsed_url.path or '/api/mitigate'
        
        # Ensure doc_path starts with /
        if not doc_path.startswith('/'):
            doc_path = '/' + doc_path
        
        print(f"🔧 Configuring ePEM at {epem_endpoint} with DOC endpoint...")
        print(f"   DOC IP: {doc_ip}, DOC Port: {doc_port}, DOC Path: {doc_path}")
        
        # Send the configuration to ePEM
        config_url = f"{epem_endpoint}/v2/horse/set_doc_ip_port"
        params = {
            'doc_ip': doc_ip,
            'doc_port': doc_port,
            'path': doc_path
        }
        
        response = requests.post(config_url, params=params, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ ePEM configured successfully with DOC endpoint")
            print(f"   Response: {response.text}")
            return True
        else:
            print(f"⚠️ ePEM configuration returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⚠️ Timeout when trying to configure ePEM - continuing anyway")
        return False
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Connection error when trying to configure ePEM - ePEM may not be running yet")
        return False
    except Exception as e:
        print(f"⚠️ Error configuring ePEM: {str(e)}")
        return False

@rtr_api.on_event("startup")
async def startup_event():
    """Run configuration tasks when the application starts"""
    print("🚀 RTR API starting up...")
    
    # Load configurations
    config_loader = get_config_loader()
    print(f"📋 Loaded {len(config_loader.get_all_action_mappings())} mitigation action mappings")
    
    configure_epem_doc_endpoint()
    print("✨ RTR API startup complete")

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

@rtr_api.post("/api/reload-config")
def reload_config(token: str = Depends(oauth2_scheme)):
    """
    Reload all RTR configuration files without restarting the Docker container
    Requires authentication
    """
    # Verify the token
    current_user = get_current_user(token)
    
    try:
        status_info = reload_configurations()
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reloading configurations: {str(e)}"
        )

@rtr_api.get("/api/config/actions")
def get_action_mappings(token: str = Depends(oauth2_scheme)):
    """
    Get all currently loaded mitigation action to playbook mappings
    Requires authentication
    """
    # Verify the token
    current_user = get_current_user(token)
    
    config_loader = get_config_loader()
    mappings = config_loader.get_all_action_mappings()
    
    return {
        "total_mappings": len(mappings),
        "action_mappings": mappings
    }

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
    token: str = Depends(oauth2_scheme)
    ):
    current_user = get_current_user(token)

    # Use intent_id directly
    intent_id = new_action.intent_id

    if new_action.command == "add":
        if intent_id in mitigation_actions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An identical action already exists",
            )

        # Store action in memory with initial status
        mitigation_actions[intent_id] = {
            "command": new_action.command,
            "intent_type": new_action.intent_type,
            "intent_id": intent_id,
            "threat": new_action.threat,
            "target_domain": new_action.target_domain,
            "action": new_action.action,
            "attacked_host": new_action.attacked_host,
            "mitigation_host": new_action.mitigation_host,
            "duration": new_action.duration,
            "status": "processing",  # Initial status while processing
            "info": "Playbook creation in progress",
            "ansible_command": new_action.ansible_command
        }
        
        try:
            # Create playbook using the mitigation action
            playbook = playbook_creator(new_action)
            
            if playbook.chosen_playbook and playbook.chosen_playbook != "UNKNOWN_ACTION_TYPE":
                # Generate the Ansible playbook content
                playbook_txt = playbook.fill_in_ansible_playbook()
                
                # Store the Ansible command in the mitigation action
                mitigation_actions[intent_id]["ansible_command"] = playbook_txt
                mitigation_actions[intent_id]["status"] = "playbook_created"
                mitigation_actions[intent_id]["info"] = "Playbook created, forwarding to ePEM in background"
                
                # Send the mitigation action to ePEM with a synchronous call
                playbook.simple_uploader(playbook_txt)
                mitigation_actions[intent_id]["status"] += ", " + playbook.mitigation_action.status
                mitigation_actions[intent_id]["info"] += ", " + playbook.mitigation_action.info 
                
            else:
                # No matching playbook found - use the detailed error message from playbook_creator
                error_info = getattr(playbook.mitigation_action, 'info', 'No matching playbook found for this action')
                mitigation_actions[intent_id]["status"] = "transform_failed"
                mitigation_actions[intent_id]["info"] = error_info
                # Return 404 for unknown action types to help clients identify configuration issues
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error_info
                )
                
        except HTTPException:
            # Re-raise HTTP exceptions to preserve status codes
            raise
        except ValueError as e:
            # Handle configuration/mapping errors with 404
            error_msg = f"Action mapping error: {str(e)}"
            mitigation_actions[intent_id]["status"] = "config_error"
            mitigation_actions[intent_id]["info"] = error_msg
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        except Exception as e:
            # Handle any other exceptions during playbook creation with 500
            error_msg = f"Error processing action: {str(e)}"
            mitigation_actions[intent_id]["status"] = "error"
            mitigation_actions[intent_id]["info"] = error_msg
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        return {
            "message": "Action created and being processed", 
            "intent_id": intent_id,
            "status": mitigation_actions[intent_id]["status"],
            "info": mitigation_actions[intent_id]["info"],
            "ansible_command": mitigation_actions[intent_id]["ansible_command"]
        }

@rtr_api.post("/update_action_status", status_code=status.HTTP_200_OK)
def update_action_status(status_update: UpdateActionStatusRequest):
    intent_id = status_update.intent_id  # Changed to use intent_id
    action_status = status_update.status
    additional_info = status_update.info

    if not intent_id or not action_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing intent_id or status")

    if intent_id not in mitigation_actions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found")

    # Update the status and info fields
    mitigation_actions[intent_id]["status"] = action_status
    mitigation_actions[intent_id]["info"] = additional_info

    # Return a consistent response that includes the action's details
    return {
        "message": "Action status updated successfully",
        "intent_id": intent_id,
        "status": mitigation_actions[intent_id]["status"],
        "info": mitigation_actions[intent_id]["info"],
        "ansible_command": mitigation_actions[intent_id].get("ansible_command", "")  # Include ansible_command if it exists
    }
    
# Add a background task function
def run_in_background(playbook, playbook_txt, intent_id):
    """Run the simple_uploader function in a background thread and update the mitigation_actions dict"""
    try:
        # Execute the simple_uploader
        playbook.simple_uploader(playbook_txt)
        
        # After uploading is done, update the in-memory storage with the latest status and info
        if hasattr(playbook.mitigation_action, 'status'):
            mitigation_actions[intent_id]["status"] = playbook.mitigation_action.status
        
        if hasattr(playbook.mitigation_action, 'info'):
            mitigation_actions[intent_id]["info"] = playbook.mitigation_action.info
            
        print(f"Background task completed for intent_id: {intent_id}")
        
    except Exception as e:
        # Update with error information if an exception occurs
        mitigation_actions[intent_id]["status"] = "error"
        mitigation_actions[intent_id]["info"] = f"Error in background task: {str(e)}"
        print(f"Error in background task for intent_id {intent_id}: {str(e)}")