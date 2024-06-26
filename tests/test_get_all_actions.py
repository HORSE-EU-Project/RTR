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

    ###################### GET ALL ACTIONS REQUESTS ######################
    headers_for_actions = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    #GET REQUEST TO ACTIONS ENDPOINT
    response_actions = requests.get(f"{base_url}/actions", headers=headers_for_actions)

    # Assert that the response status code is 200 (OK)
    assert response_actions.status_code == 200

    # Assert that the response contains the expected list of items
    stored_actions = response_actions.json()['stored actions']
    for action in stored_actions:
        pprint(action)
    