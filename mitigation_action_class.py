from pydantic import BaseModel, Field
from typing import Optional, Literal


# Enhanced mitigation_action_model
class mitigation_action_model(BaseModel):
    command: str = Field(..., example="add")  # Example for Swagger UI
    intent_type: str = Field(..., example="mitigation")
    threat: str = Field(..., example="ddos")
    attacked_host: str = Field(..., example="10.0.0.1")
    mitigation_host: str = Field(..., example="172.16.2.1")
    action: str = Field(..., example="Block potentially spoofed packets with destination 192.68.0.0/24 in interface wlan")
    duration: int = Field(..., example=7000)
    intent_id: Optional[str] = Field(None, example="ABC124")
    status: str = Field(default="pending", example="completed", description="Current status of the mitigation action")
    info: str = Field(default="to be enforced", example="Action successfully executed", description="Additional information about the action status")

    class Config:
        schema_extra = {
            "examples": {
                "Add a DDoS Mitigation Action": {
                    "summary": "Create an action to mitigate a DDoS attack",
                    "description": "This example creates a mitigation action to block spoofed packets.",
                    "value": {
                        "command": "add",
                        "intent_type": "mitigation",
                        "threat": "ddos",
                        "attacked_host": "10.0.0.1",
                        "mitigation_host": "172.16.2.1",
                        "action": "Block potentially spoofed packets with destination 192.68.0.0/24 in interface wlan",
                        "duration": 7000,
                        "intent_id": "ABC124",
                        "status": "pending",
                        "info": "to be enforced"
                    }
                }
            }
        }


class UpdateActionStatusRequest(BaseModel):
    action_id: str = Field(..., example="ABC123")
    status: str = Field(..., example="completed")
    info: str = Field(..., example="Action successfully executed")

    class Config:
        schema_extra = {
            "examples": {
                "Update to Completed": {
                    "summary": "Mark action as completed",
                    "description": "This marks the action as completed with additional info.",
                    "value": {
                        "action_id": "ABC123",
                        "status": "completed",
                        "info": "Action successfully executed"
                    }
                },
                "Update with Error": {
                    "summary": "Mark action as error",
                    "description": "This marks the action as failed due to an error.",
                    "value": {
                        "action_id": "ABC123",
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
