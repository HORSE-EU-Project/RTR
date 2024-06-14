import requests

def test_home_page():
    base_url = "http://127.0.0.1:8000"
    
    # Send a GET request to the "/items/" endpoint
    response = requests.get(f"{base_url}")
    
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    
    # Assert that the response contains the expected list of items
    expected_items = {"message":"Welcome to RTR"}
    assert response.json() == expected_items
    print(response.json())