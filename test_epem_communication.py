#!/usr/bin/env python3
"""
Test script to check if mitigation actions are sent to the EPEM endpoint.
This script will trace the flow from action registration to EPEM communication.
"""

import requests
import time
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://10.19.2.19:8000"
EPEM_ENDPOINT = os.getenv('EPEM_ENDPOINT', 'http://10.19.2.20:5002')

def create_test_user():
    """Create a test user for authentication"""
    print("🔧 Creating test user...")
    user_data = {
        "username": "test_user_epem",
        "email": "test_epem@example.com",
        "password": "test_password"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=user_data)
        if response.status_code == 200:
            print("✅ Test user created successfully")
            return True
        elif response.status_code == 409:
            print("ℹ️  Test user already exists")
            return True
        else:
            print(f"❌ Failed to create user: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating user: {e}")
        return False

def login_test_user():
    """Login and get authentication token"""
    print("🔐 Logging in test user...")
    login_data = {
        'grant_type': '',
        'username': 'test_user_epem',
        'password': 'test_password',
        'scope': '',
        'client_id': '',
        'client_secret': ''
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", data=login_data)
        if response.status_code == 200:
            token = response.json()['access_token']
            print("✅ Login successful")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error logging in: {e}")
        return None

def create_mitigation_action(token):
    """Create a mitigation action and trace the EPEM communication"""
    print("🎯 Creating mitigation action...")
    
    # Test with a dictionary-based action (modern format)
    action_data = {
        "command": "add",
        "intent_type": "mitigation",
        "intent_id": f"TEST_EPEM_{int(time.time())}",
        "threat": "ddos",
        "target_domain": "example.com",
        "action": {
            "name": "DNS_RATE_LIMIT",
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
        "info": "to be enforced"
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"📤 Sending action with intent_id: {action_data['intent_id']}")
        response = requests.post(f"{BASE_URL}/actions", json=action_data, headers=headers)
        
        if response.status_code in [200, 201]:
            print("✅ Action created successfully")
            result = response.json()
            print(f"📊 Initial response: {json.dumps(result, indent=2)}")
            return action_data['intent_id']
        else:
            print(f"❌ Failed to create action: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error creating action: {e}")
        return None

def monitor_action_status(token, intent_id, max_wait_time=30):
    """Monitor the action status to see if it's sent to EPEM"""
    print(f"👀 Monitoring action {intent_id} for EPEM communication...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    start_time = time.time()
    previous_status = None
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{BASE_URL}/action_by_id/{intent_id}", headers=headers)
            
            if response.status_code == 200:
                action_details = response.json()["Action details"]
                current_status = action_details.get("status", "unknown")
                current_info = action_details.get("info", "no info")
                
                if current_status != previous_status:
                    print(f"📈 Status update: {current_status} - {current_info}")
                    previous_status = current_status
                    
                    # Check if it reached EPEM-related statuses
                    if current_status in ["sent_to_epem", "epem_forward_failed", "epem_request_error"]:
                        print(f"🎯 EPEM communication detected! Status: {current_status}")
                        print(f"📝 Details: {current_info}")
                        return True, current_status, current_info
                
                # Wait a bit before checking again
                time.sleep(2)
            else:
                print(f"❌ Error checking action status: {response.status_code}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error monitoring action: {e}")
            break
    
    print(f"⏰ Monitoring timeout reached after {max_wait_time} seconds")
    return False, previous_status, "Timeout reached"

def check_epem_endpoint_availability():
    """Check if the EPEM endpoint is reachable"""
    print(f"🌐 Checking EPEM endpoint availability: {EPEM_ENDPOINT}")
    
    try:
        # Try to connect to the EPEM endpoint
        test_url = f"{EPEM_ENDPOINT}/v2/horse/"
        response = requests.get(test_url, timeout=5)
        
        if response.status_code == 200:
            print("✅ EPEM endpoint is reachable")
            return True
        else:
            print(f"⚠️  EPEM endpoint returned status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ EPEM endpoint not reachable: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 RTR -> EPEM Communication Test")
    print("=" * 60)
    print(f"🔗 RTR API URL: {BASE_URL}")
    print(f"🎯 EPEM Endpoint: {EPEM_ENDPOINT}")
    print("-" * 60)
    
    # Check RTR API availability
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code != 200:
            print(f"❌ RTR API not available at {BASE_URL}")
            return
        print("✅ RTR API is available")
    except requests.exceptions.RequestException as e:
        print(f"❌ RTR API not reachable: {e}")
        return
    
    # Check EPEM endpoint availability
    epem_available = check_epem_endpoint_availability()
    
    print("-" * 60)
    
    # Create user and login
    if not create_test_user():
        return
    
    token = login_test_user()
    if not token:
        return
    
    print("-" * 60)
    
    # Create mitigation action
    intent_id = create_mitigation_action(token)
    if not intent_id:
        return
    
    print("-" * 60)
    
    # Monitor action status
    epem_contacted, final_status, final_info = monitor_action_status(token, intent_id)
    
    print("-" * 60)
    print("📊 TEST RESULTS:")
    print(f"📋 Action ID: {intent_id}")
    print(f"📈 Final Status: {final_status}")
    print(f"📝 Final Info: {final_info}")
    print(f"🎯 EPEM Contacted: {'✅ YES' if epem_contacted else '❌ NO'}")
    print(f"🌐 EPEM Reachable: {'✅ YES' if epem_available else '❌ NO'}")
    
    if epem_contacted:
        print("\n🎉 SUCCESS: Mitigation action was sent to EPEM endpoint!")
    elif not epem_available:
        print("\n⚠️  WARNING: EPEM endpoint not reachable - this may be expected in test environment")
    else:
        print("\n❌ ISSUE: Mitigation action was not sent to EPEM endpoint")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
