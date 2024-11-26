import os
import requests

def simple_uploader(target_ip, action_id, action_definition, service, playbook_yaml):
    epem_url = os.getenv('EPEM_ENDPOINT')  # Ensure this is set to ePEM's actual endpoint
    update_status_url = "http://your-fastapi-server/update_action_status"  # Replace with actual FastAPI server URL

    params = {
        "target_ip": target_ip,
        "port": None,
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
        response = requests.post(epem_url, params=params, headers=headers, data=playbook_content)

        if response.ok:
            print("Upload completed successfully!")
            print(f"Request body: {response.text}")
            # Notify FastAPI that action is now 'completed'
            update_status_payload = {
                "action_id": action_id,
                "status": "completed",
                "info": "Action processed by ePEM successfully"
            }
        else:
            print(f"Upload failed! Status code: {response.status_code}")
            update_status_payload = {
                "action_id": action_id,
                "status": "error",
                "info": f"Upload failed with status code: {response.status_code}, response: {response.text}"
            }
        # Send status update to FastAPI server
        requests.post(update_status_url, json=update_status_payload)

    except Exception as e:
        print(f"Error in simple_uploader: {e}")
        # Update status to error in case of exception
        update_status_payload = {
            "action_id": action_id,
            "status": "error",
            "info": f"Exception occurred: {str(e)}"
        }
        # Send status update to FastAPI server
        requests.post(update_status_url, json=update_status_payload)
