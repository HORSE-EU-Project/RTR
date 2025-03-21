from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List


# Enhanced mitigation_action_model
class mitigation_action_model(BaseModel):
    
    command: str = Field(..., example="add")  # Example for Swagger UI
    intent_type: str = Field(..., example="mitigation")
    intent_id: str = Field(..., example="ABC124")  # Made intent_id required (not optional)
    threat: str = Field(default="", example="ddos")
    target_domain: str = Field(default="", example="example.com")
    # Changed from str to Union[str, ActionObject] to accept either a string or a structured object
    action: Dict[str, Any] = Field(..., example={
        "name": "dns_rate_limit", 
        "intent_id": "30001", 
        "fields": {
            "rate": 20, 
            "duration": 60, 
            "source_ip_filter": ["malicious_ips"]
        }
    })
    
    attacked_host: str = Field(default="0.0.0.0", example="10.0.0.1")
    mitigation_host: str = Field(default="0.0.0.0", example="172.16.2.1")    
    duration: int = Field(default=0, example=7000)    
    status: str = Field(default="pending", example="completed", description="Current status of the mitigation action")
    info: str = Field(default="to be enforced", example="Action successfully executed", description="Additional information about the action status")
    ansible_command: str = Field(default="", example="- hosts: [172.16.2.1]\n  tasks:\n...", description="The generated Ansible playbook command")

    class Config:
        schema_extra = {
            "examples": {
                "Add a DDoS Mitigation Action": {
                    "summary": "Create an action to mitigate a DDoS attack",
                    "description": "This example creates a mitigation action to block spoofed packets.",
                    "value": {
                        "command": "add",
                        "intent_type": "mitigation", 
                        "intent_id": "ABC124",
                        "threat": "ddos",
                        "action": { 
                            "name": "dns_rate_limit",
                            "intent_id": "30001",
                            "fields": {
                                "rate": 20,
                                "duration": 60,
                                "source_ip_filter": ["malicious_ips"]
                            }
                        },
                        "attacked_host": "10.0.0.1",
                        "mitigation_host": "172.16.2.1",
                        "duration": 7000,
                        "status": "pending",
                        "info": "to be enforced",
                        "ansible_command": ""
                    }
                }
            }
        }


# UpdateActionStatusRequest now uses intent_id instead of action_id
class UpdateActionStatusRequest(BaseModel):
    intent_id: str = Field(..., example="ABC124")  # Replaced action_id with intent_id
    status: str = Field(..., example="completed")
    info: str = Field(..., example="Action successfully executed")

    class Config:
        schema_extra = {
            "examples": {
                "Update to Completed": {
                    "summary": "Mark action as completed",
                    "description": "This marks the action as completed with additional info.",
                    "value": {
                        "intent_id": "ABC124",  # Using intent_id instead of action_id
                        "status": "completed",
                        "info": "Action successfully executed"
                    }
                },
                "Update with Error": {
                    "summary": "Mark action as error",
                    "description": "This marks the action as failed due to an error.",
                    "value": {
                        "intent_id": "ABC124",  # Using intent_id instead of action_id
                        "status": "error",
                        "info": "Execution failed due to timeout"
                    }
                }
            }
        }



class User(BaseModel):
    username: str
    email: str
    password: str

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class MitigationIdRequestBody(BaseModel):
    mitigation_id: str
