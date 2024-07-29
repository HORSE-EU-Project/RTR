from threading import Thread
from typing import Union
from fastapi import FastAPI,APIRouter, status, Body, Query, HTTPException
from typing_extensions import Annotated
from pydantic import BaseModel
from enum import Enum

class RTRActionType(str, Enum):
    DNS_RATE_LIMIT = "DNS_RATE_LIMIT"
    DNS_SERV_DISABLE = "DNS_SERV_DISABLE"
    DNS_SERV_ENABLE = "DNS_SERV_ENABLE"
    TEST = "TEST"


ansible_router = APIRouter(
    prefix="/v2/horse",
    tags=["Horse"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}},
)


class AnsibleRestAnswer(BaseModel):
    description: str = 'operation submitted'
    status: str = 'submitted'
    status_code: int = 202 # OK


@ansible_router.get("/")
def root():
    
    return {"message": "Welcome to mock ePEM"}


@ansible_router.post("/rtr_request_workaround", response_model=AnsibleRestAnswer)
async def run_playbook(target: str, action_type: RTRActionType, username: str, password: str, forward_to_doc: bool, payload: str = Body(None, media_type="application/yaml"), service: str | None = None, actionID: str | None = None):
    """
    Integration for NEPHELE Project. Allow applying mitigation action on a target managed by the NFVCL (ePEM).
    Allows running an ansible playbook on a remote host. The host NEEDS to be managed by nfvcl.

    Args:

        target: The host on witch the playbook is applied ('host:port' format)

        payload: The ansible playbook in yaml format to be applied on the remote target
    """
    print(f"Target: {target}")
    print(f"Action type: {action_type}")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Forward to doc: {forward_to_doc}")
    print(f"Action ID: {actionID}")
    print(f"Payload: {payload}")
    
    
    return AnsibleRestAnswer(description="Mock up ePEM received the RTR request", status="submitted", status_code=202)


mock_epem = FastAPI()
mock_epem.include_router(ansible_router)