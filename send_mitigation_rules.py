import requests



def simple_uploader(action_id, action_definition, service, playbook_yaml):
    #test_file = open("mitigation_rules.yaml", "rb")


    receiver_url = "http://httpbin.org/post"

    params = {
        "actionID": action_id,
        "action_definition": action_definition,
        "service": service
    }

    headers = {
        "Content-Type": "text/yaml"
    }
    

    #data = playbook_yaml

    test_response = requests.post(receiver_url, params=params, headers = headers, data = playbook_yaml)

    if test_response.ok:
        print("Upload completed successfully!")
        print(test_response.text)
    else:
        print("Something went wrong!")


if __name__ == '__main__':
    simple_uploader()