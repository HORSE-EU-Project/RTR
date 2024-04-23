import requests

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
        "attacked_host": "198.2.191.7",
        "mitigation_host": "194.19.13.181",
        "action": "Set the number of request to the dns server to a 5/s for port 55, protocol udp",
        "duration": 9000,
        "intent_id": "B123"
    }

    response_for_new_action = requests.post(f"{base_url}/actions", headers=headers_for_action_post, json=data)
    assert response_for_new_action.status_code in [200,201]

    headers_for_action_get = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response_for_new_action = convert_id(response_for_new_action.json())
    mitigation_id = response_for_new_action['_id']
    response_for_get_action = requests.get(f"{base_url}/actions/{mitigation_id}", headers=headers_for_action_get)
    assert response_for_get_action.status_code == 200

    # Testing for a non-existent ID
    invalid_mitigation_id = "invalid_id"
    response_for_invalid_action = requests.get(f"{base_url}/actions/{invalid_mitigation_id}", headers=headers_for_action_get)
    assert response_for_invalid_action.status_code == 404

    headers_for_action_delete = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response_for_get_action = requests.delete(f"{base_url}/actions/{mitigation_id}", headers=headers_for_action_delete)
    assert response_for_get_action.status_code == 200


def convert_id(action):
    """Convert MongoDB document for serialization."""
    # Convert ObjectId to string for serialization
    action["_id"] = str(action["_id"])
    return action