import requests

def test_home_page():
    base_url = "http://127.0.0.1:8000"
    
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    
    data = {
        "username": "user1",
        "email": "user1@gmail.com",
        "password": "user1"
    }
    #POST REQUEST FOR USER REGISTER
    response = requests.post(f"{base_url}/register", headers=headers, json=data)

    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200

    # Assert that the response contains the expected list of items
    expected_items = {"res":"created"}
    assert response.json() == expected_items
    print(f"Result: {response.json()}")