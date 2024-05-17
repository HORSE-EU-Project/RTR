import requests
from pprint import pprint
def test_login_and_get_all_actions():
    base_url = "http://127.0.0.1:8000"
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Send a GET request to the "/items/" endpoint
    
    data = {
        'grant_type': '',
        'username': 'user1',
        'password': 'user1',
        'scope': '',
        'client_id': '',
        'client_secret': ''
    }
    
    response = requests.post(f"{base_url}/login", headers=headers, data=data)
    
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected list of items
    access_token = ''
    if 'access_token' in response.json():
        access_token = response.json()['access_token']
        print(f"Authentication token: {access_token}")


    headers_for_action_post = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    data = {
        "command": "add",
        "intent_type": "mitigation",
        "threat": "ddos",
        "attacked_host": "198.2.19.0",
        "mitigation_host": "19.190.13.181",
        "action": "allow traffic from iprange 192.69.0.1/25 to interface wlan1",
        "duration": 800,
        "intent_id": "adfB3"
    }

    response_for_new_action = requests.post(f"{base_url}/actions", headers=headers_for_action_post, json=data)
    print(f"Response fom new action creation {response_for_new_action.json()}")
    assert response_for_new_action.status_code in [200,201]

    headers_for_action_get = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    #response_for_new_action = convert_id(response_for_new_action.json())
    #print(response_for_new_action.json()['New action unique id is'])
    #mitigation_id = response_for_new_action['New action unique id is']
    
    mitigation_id = response_for_new_action.json()['New action unique id is']
    print(type(mitigation_id))
    response_for_get_action = requests.get(f"{base_url}/action_by_id/{mitigation_id}", headers=headers_for_action_get)
    print(f"This is the response for the get request with id {mitigation_id}")
    pprint(response_for_get_action.json())
    assert response_for_get_action.status_code == 200

    # Testing for a non-existent ID
    invalid_mitigation_id = "invalid_id"
    response_for_invalid_action = requests.get(f"{base_url}/action_by_id/{invalid_mitigation_id}", headers=headers_for_action_get)
    print(f"Response for GET request with invalid action id {response_for_invalid_action}")
    assert response_for_invalid_action.status_code == 404

    headers_for_action_delete = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response_for_get_action = requests.delete(f"{base_url}/actions/{mitigation_id}", headers=headers_for_action_delete)
    print(f"Response for successful DELETE request {response_for_get_action}")
    assert response_for_get_action.status_code in [200,204]

    response_for_deleted_action = requests.get(f"{base_url}/action_by_id/{mitigation_id}", headers=headers_for_action_get)
    print(f"Response for GET request with deleted action id {response_for_deleted_action}")
    assert response_for_invalid_action.status_code == 404

def convert_id(action):
    """Convert MongoDB document for serialization."""
    # Convert ObjectId to string for serialization
    action["New action unique id is"] = str(action["New action unique id is"])
    return action