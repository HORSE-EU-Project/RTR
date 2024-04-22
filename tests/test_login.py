import requests

def test_login():
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
    if 'access_token' in response.json():
        print(f"Authentication token: {response.json()['access_token']}")
    #expected_items = [{"access_token":"created"},{"token_type":"bearer"}]
    #assert response.json() == expected_items