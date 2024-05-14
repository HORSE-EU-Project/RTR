import requests



def simple_uploader(action_id, action_definition, service, playbook_yaml):
    #test_file = open("mitigation_rules.yaml", "rb")

    
    #receiver_url = "http://httpbin.org/post"
    receiver_url = "http://127.0.0.1:9000/rtr_request"
    params = {
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
    test_response = requests.post(receiver_url, params=params, headers = headers, data = playbook_content)

    if test_response.ok:
        print("Upload completed successfully!")
        print(test_response.text)
    else:
        print("Something went wrong!")


if __name__ == '__main__':
    action_id = "123"
    action_definition = "Service Modification"
    service = "DNS"
    playbook_yaml = open("ansible_playbooks/dns_rate_limiting.yaml", "rb")
    playbook_content = playbook_yaml.read()
    #print(content)
    simple_uploader(action_id, action_definition, service, playbook_content)