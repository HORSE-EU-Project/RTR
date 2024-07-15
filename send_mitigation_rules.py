import requests
import os



def simple_uploader(target_ip, action_id, action_definition, service, playbook_yaml):
    #test_file = open("mitigation_rules.yaml", "rb")

    
    receiver_url = f"http://{os.getenv('EPEM_ENDPOINT')}:{os.getenv('EPEM_PORT')}/v2/horse/rtr_request"
    
    print(f"Receiver url: {receiver_url}")
    
    
    params = {
        "target_ip": target_ip,
        "target_port": "8080",
        "service": service,
        "actionType": action_definition,
        "actionID": action_id
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/yaml"
    }
    

    #data = playbook_yaml
    playbook_content = playbook_yaml
    test_response = requests.post(receiver_url, params=params, headers = headers, data=playbook_content)
    
    if test_response.ok:
        print("Upload completed successfully!")
        print(f"Request body {test_response.text}")
        
    else:
        print(f"Something went wrong! Status code: {test_response.status_code}")

    return(test_response.status_code)


def simple_uploader_workaround(target_ip, action_id, action_definition, service, playbook_yaml):
    #test_file = open("mitigation_rules.yaml", "rb")

    
    receiver_url = f"http://{os.getenv('EPEM_ENDPOINT')}:{os.getenv('EPEM_PORT')}/v2/horse/rtr_request_workaround"
    print(f"Receiver url: {receiver_url}")
    #receiver_url = "http://httpbin.org/post"
    
    params = {
        "target": target_ip,
        "action_type": action_definition,
        "username": "ubuntu",
        "password": "testpwd",
        "forward_to_doc": False,
        "service": service,
        "actionID": action_id
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "text/yaml"
    }
    

    #data = playbook_yaml
    playbook_content = playbook_yaml
    test_response = requests.post(receiver_url, params=params, headers = headers, data=playbook_content)
    print("Headers:", headers)
    print("Params:", params)
    print(test_response)
    if test_response.ok:
        print("Upload completed successfully!")
        print(f"Request body {test_response.text}")
        
    else:
        print(f"Something went wrong! Status code: {test_response.status_code}")

    return(test_response.status_code)

if __name__ == '__main__':
    action_id = "123"
    action_definition = "Service Modification"
    service = "DNS"
    playbook_yaml = open("ansible_playbooks/dns_rate_limiting.yaml", "rb")
    playbook_content = playbook_yaml.read()
    #print(playbook_content)
    simple_uploader("127.0.0.1",action_id, action_definition, service, playbook_content)