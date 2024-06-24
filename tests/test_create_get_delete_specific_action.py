import requests
from pprint import pprint
def test_login_and_get_all_actions():
    base_url = "http://127.0.0.1:8000"
    
    ###################### LOGIN REQUESTS ######################
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': '',
        'username': 'user1',
        'password': 'user1',
        'scope': '',
        'client_id': '',
        'client_secret': ''
    }
    #POST LOGIN REQUEST
    response = requests.post(f"{base_url}/login", headers=headers, data=data)
    
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected list of items
    access_token = ''
    if 'access_token' in response.json():
        access_token = response.json()['access_token']
        print(f"Authentication token: {access_token}")

    ###################### POST A NEW ACTION REQUEST ######################
    headers_for_action_post = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    data = {
        "command": "add",
        "intent_type": "mitigation",
        "threat": "ddos",
        "attacked_host": "193.2.19.0",
        "mitigation_host": "DNS_SERVER",
        "action": "Set the number of request to the dns server to a 5/s for port 55, protocol udp",
        "duration": 8400,
        "intent_id": "afsdB3"
    }
    # POST REQUEST FOR NEW ACTION
    response_for_new_action = requests.post(f"{base_url}/actions", headers=headers_for_action_post, json=data)
    
    # Assert that the response status code is 200 OR 201(OK)
    assert response_for_new_action.status_code in [200,201]
    print(f"Response fom new action creation {response_for_new_action.json()}")

    ###################### GET THE ACTION BASED ON ID ######################
    headers_for_action_get = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    
    #mitigation_id = response_for_new_action.json()['New action unique id is']
    #print(type(mitigation_id))

    #GET REQUEST WITH SPECIFIED ID
    response_for_get_action = requests.get(f"{base_url}/action_by_id/{data['intent_id']}", headers=headers_for_action_get)
    print(f"This is the response for the get request with id {data['intent_id']}")

    # Assert that the response status code is 200 OR 201(OK)
    assert response_for_get_action.status_code == 200
    pprint(response_for_get_action.json())

    ###################### TEST GET REQUEST FOR NON EXISTENT ID ######################
    invalid_mitigation_id = "invalid_id"
    response_for_invalid_action = requests.get(f"{base_url}/action_by_id/{invalid_mitigation_id}", headers=headers_for_action_get)
    print(f"Response for GET request with invalid action id {response_for_invalid_action}")
    assert response_for_invalid_action.status_code == 404

    ###################### TEST ACTION DELETE ######################
    headers_for_action_delete = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    delete_data = {
        "command": "delete",
        "intent_type": "mitigation",
        "threat": "ddos",
        "attacked_host": "193.2.19.0",
        "mitigation_host": "DNS_SERVER",
        "action": "Set the number of request to the dns server to a 5/s for port 55, protocol udp",
        "duration": 8400,
        "intent_id": "afsdB3"
    }
    #POST DELETE REQUEST WITH ACTION ID
    response_for_new_action = requests.post(f"{base_url}/actions", headers=headers_for_action_post, json=delete_data)
    
    # Assert that the response status code is 200 OR 201(OK)
    assert response_for_new_action.status_code in [200,201]
    print(f"Response fom new action creation {response_for_new_action.json()}")

    #CHECK THE ACTION WAS CORRECTLY DELETED
    print(delete_data['intent_id'])
    response_for_deleted_action = requests.get(f"{base_url}/action_by_id/{delete_data['intent_id']}", headers=headers_for_action_get)
    print(f"Response for GET request with deleted action id {response_for_deleted_action}")
    assert response_for_invalid_action.status_code == 404

def convert_id(action):
    """Convert MongoDB document for serialization."""
    # Convert ObjectId to string for serialization
    action["New action unique id is"] = str(action["New action unique id is"])
    return action