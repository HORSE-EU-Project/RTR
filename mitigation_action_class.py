from pydantic import BaseModel
from datetime import timedelta



class mitigation_action_model(BaseModel):
    command: str
    intent_type: str
    threat: str
    attacked_host: str
    mitigation_host: str
    action: str
    duration: int
    intent_id: str


class MitigationIdRequestBody(BaseModel):
    mitigation_id: str