from pydantic import BaseModel, Field, model_validator
from typing import Optional, Literal, Dict, Any, List, Union


# Enhanced mitigation_action_model
class mitigation_action_model(BaseModel):
    
    command: str = Field(default="add", example="add")  # Example for Swagger UI
    intent_type: str = Field(default="mitigation", example="mitigation/prevention")
    intent_id: str = Field(..., example="ABC124")  # Made intent_id required (not optional)
    threat: str = Field(default="", example="ddos")
    target_domain: Union[str, List[str]] = Field(default="", example="UPC/CNIT/UMU")
    # Changed to Union[str, Dict[str, Any]] to accept either a string or a structured object
    action: Union[str, Dict[str, Any]] = Field(..., example=
        "Can use a string like 'rate limit DNS server at ip 10.10.2.1 at port 123, for 20 requests per second' "
        "or a dictionary with structured fields like:"
        '{"name": "dns_rate_limit", "intent_id": "30001", "fields": {"rate": 20, "duration": 60, "source_ip_filter": ["malicious_ips"]}}' 
    )
    
    attacked_host: Union[str, List[str]] =  Field(default="0.0.0.0", example="10.0.0.1")
    mitigation_host: Union[str, List[str]] = Field(default="0.0.0.0", example="172.16.2.1")    
    duration: int = Field(default=0, example=7000)    
    status: str = Field(default="pending", example="completed", description="Current status of the mitigation action")
    info: str = Field(default="to be enforced", example="Action successfully executed", description="Additional information about the action status")
    ansible_command: str = Field(default="", example="- hosts: [172.16.2.1]\n  tasks:\n...", description="The generated Ansible playbook command")

    # @model_validator(mode='before')
    # def normalize_action_name(cls, values):
    #     """Translate legacy action names in the incoming payload.

    #     If incoming `action` is a dict and contains a name of
    #     'block_pod_address' (either at action['name'] or action['fields']['name']),
    #     translate it to 'block_ip_addresses' before validation.
    #     """
    #     action = values.get('action')
    #     if isinstance(action, dict):
    #         # Check field-level name and translate from 'block_ip_address' -> 'block_pod_address'
    #         fields = action.get('fields')
    #         if isinstance(fields, dict) and fields.get('name') == 'block_ip_address':
    #             fields['name'] = 'block_pod_addresses'

    #         # write back the possibly-updated action
    #         values['action'] = action

    #     return values

    @model_validator(mode='before')
    def normalize_blocked_pod_and_fields(cls, values):
        """Normalize incoming action payloads:

        - For 'block_pod_address': rename 'blocked_pod' -> 'blocked_ips' and ensure it's a list
        - For 'block_ues_multidomain': extract domains, populate mitigation_host (as list) and target_domain
        This runs before validation so downstream logic sees normalized data.
        """
        action = values.get('action')
        if isinstance(action, dict):
            fields = action.get('fields') or {}

            # If action name is 'block_pod_address', translate field 'blocked_pod' -> 'blocked_ips'
            if action.get('name') == 'block_pod_address' and isinstance(fields, dict):
                if 'blocked_pod' in fields:
                    v = fields.pop('blocked_pod')
                    if isinstance(v, str):
                        v = [v]
                    fields['blocked_ips'] = v

            # If blocked_ips exists and is a string, convert to list
            if isinstance(fields, dict) and 'blocked_ips' in fields and isinstance(fields['blocked_ips'], str):
                fields['blocked_ips'] = [fields['blocked_ips']]

            # Handle 'block_ues_multidomain' actions: extract domains and populate mitigation_host & target_domain
            if action.get('name') == 'block_ues_multidomain' and isinstance(fields, dict):
                domains = fields.get('domains')
                if domains:
                    # Ensure domains is a list
                    if isinstance(domains, str):
                        domains = [domains]
                    # Populate mitigation_host with the domains list (if not already set)
                    if values.get('mitigation_host') in (None, '0.0.0.0', ''):
                        values['mitigation_host'] = domains
                    # Populate target_domain with the domains list (if not already set)
                    if values.get('target_domain') in (None, ''):
                        values['target_domain'] = domains

            # write back
            action['fields'] = fields
            values['action'] = action

        return values

    @model_validator(mode='after')
    def set_mitigation_host_and_duration_from_action(self):
        mit_host = getattr(self, 'mitigation_host', None)
        action = getattr(self, 'action', None)
        duration = getattr(self, 'duration', None)
        domain = getattr(self, 'domains', None)

        # Treat empty string or default placeholder as not set
        if mit_host in (None, '', '0.0.0.0'): 
            if isinstance(action, dict):
                fields = action.get('fields', {}) or {}
                # keys to check in order of preference
                for key in ('blocked_pod', 'pod', 'mitigation_host', 'source_ip_filter', 'dns_servers'):
                    if key in fields and fields[key]:
                        # coerce to string to match field type
                        self.mitigation_host = str(fields[key])
                        break
        if duration in (None, 0):
            if isinstance(action, dict):
                fields = action.get('fields', {}) or {}
                # keys to check in order of preference
                for key in ('duration', 'timeout'):
                    if key in fields and fields[key]:
                        self.duration = int(fields[key])
                        break
        if domain in (None, '', []):
            if isinstance(action, dict):
                fields = action.get('fields', {}) or {}
                # keys to check in order of preference
                for key in ('target_domain', 'domains'):
                    if key in fields and fields[key]:
                        self.target_domain = fields[key]
                        break
        
        return self

    class Config:
        schema_extra = {
            "examples": {
                "Add a DDoS Mitigation Action (Dictionary Format)": {
                    "summary": "Create an action to mitigate a DDoS attack using structured format",
                    "description": "This example creates a mitigation action using the recommended dictionary format.",
                    "value": {
                        "command": "add",
                        "intent_type": "mitigation", 
                        "intent_id": "30001",
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
                },
                "Add a DDoS Mitigation Action (String Format)": {
                    "summary": "Create an action to mitigate a DDoS attack using string format",
                    "description": "This example creates a mitigation action using the legacy string format.",
                    "value": {
                        "command": "add",
                        "intent_type": "mitigation", 
                        "intent_id": "ABC125",
                        "threat": "ddos",
                        "action": "rate limit DNS server at ip 10.10.2.1 at port 123, for 20 requests per second",
                        "attacked_host": "10.10.2.1",
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
