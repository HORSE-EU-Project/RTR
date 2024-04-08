from pydantic import BaseModel
from datetime import timedelta
from typing import Optional

class mitigation_action_model(BaseModel):
    command: str
    intent_type: str
    threat: str
    attacked_host: str
    mitigation_host: str
    action: str
    duration: int
    intent_id: str



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