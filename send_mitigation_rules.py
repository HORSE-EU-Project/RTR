import os
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def simple_uploader(target_ip, action_id, action_definition, service, playbook_yaml):
    epem_url = os.getenv('EPEM_ENDPOINT')  # Ensure this is set to ePEM's actual endpoint
    if not epem_url:
        logging.error("EPEM_ENDPOINT environment variable is not set.")
        return
    
    update_status_url = "http://your-fastapi-server/update_action_status"  # Replace with actual FastAPI server URL

    params = {
        "target_ip": target_ip,
        "port": None,  # Ensure this is updated if port is required
        "service": service,
        "actionType": action_definition,
        "actionID": action_id
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/yaml"
    }

    # Send request to ePEM component
    playbook_content = playbook_yaml
    try:
        response = requests.post(epem_url, params=params, headers=headers, data=playbook_content, timeout=30)  # Added timeout

        if response.ok:
            logging.info("Upload completed successfully!")
            logging.debug(f"Request body: {response.text}")
            update_status_payload = {
                "action_id": action_id,
                "status": "completed",
                "info": "Action processed by ePEM successfully"
            }
        else:
            logging.error(f"Upload failed! Status code: {response.status_code}")
            update_status_payload = {
                "action_id": action_id,
                "status": "error",
                "info": f"Upload failed with status code: {response.status_code}, response: {response.text}"
            }
        
        # Send status update to FastAPI server
        status_response = requests.post(update_status_url, json=update_status_payload, timeout=10)
        if not status_response.ok:
            logging.error(f"Failed to update status on FastAPI server: {status_response.status_code}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error in simple_uploader: {e}")
        update_status_payload = {
            "action_id": action_id,
            "status": "error",
            "info": f"Exception occurred: {str(e)}"
        }
        # Send status update to FastAPI server
        requests.post(update_status_url, json=update_status_payload, timeout=10)
