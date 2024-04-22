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

    headers_for_actions = {
        'accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response_actions = requests.get(f"{base_url}/actions", headers=headers_for_actions)
    assert response_actions.status_code == 200
    print(response_actions.json())
    #expected_items = [{"access_token":"created"},{"token_type":"bearer"}]
    #assert response.json() == expected_items