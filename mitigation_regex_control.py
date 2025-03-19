import re
import requests
from mitigation_action_class import mitigation_action_model
import os
from jinja2 import Environment, FileSystemLoader

# Define regex patterns
expressions = ['port', 'ports']
regex_patterns = {
    'ipv4_and_subnet': r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b',
    'protocol': r'\b(tcp|udp)\b',
    'requests_per_sec': r'\b(\d{1,3}\/s)\b',
    'port': rf'\b(?:{"|".join(expressions)})\b\s*(\d+(?:,\d+)*)',
    'interface_name': r'\b(eth\d+|en[pso]\w*|wlan\d+|lo)\b'
}


class playbook_creator:
    def __init__(self, action_from_IBI):
        self.current_patterns = [
            ('dns_rate_limiting.yaml', r'\b(reduce|decrease|requests|number|rate|limit|dns|server|service|\d{1,3}\/s)\b', 'DNS_RATE_LIMIT'),
            ('dns_service_disable.yaml', r'\b(disable|shut down|dns|server|service)\b', 'DNS_SERV_DISABLE'),
            ('dns_service_handover', r'\b(hand over|dns|server|service)\b', 'DNS_HANDOVER'),
            ('dns_firewall_spoofing_detection.yaml', r'\b(spoof|spoofed|destination|spoofing|packets|firewall|interface|block|stop|ip|ip range)\b', 'DNS_FIREWALL_SPOOF'),
            ('anycast_blackhole', r'\b(redirect|direct|dns|server|service|traffic|igress|blackhole)\b', 'ANYCAST_BLACKHOLE')
        ]
        self.mitigation_action = action_from_IBI
        self.chosen_playbook = self.match_mitigation_action_with_playbook()
        self.action_type = self.determine_action_type()
        
        # Get the EPEM endpoint from environment variables
        # The .env file already includes the protocol, so we don't need to add it
        self.epem_endpoint = os.getenv('EPEM_ENDPOINT', 'http://httpbin.org/post')
            
        print(f"EPEM endpoint: {self.epem_endpoint}")
        print(self.chosen_playbook)

    # Loops through the regex patterns and checks if the action matches any of them
    # If it does, it adds the pattern and the number of matches to a list
    # Then it returns the pattern with the most matches (The category of the mitigation action)
    def match_mitigation_action_with_playbook(self):
        high_level_mitigation_action = self.mitigation_action.action

        pattern_matches = []
        for pattern in self.current_patterns:
            matches = re.findall(pattern[1], high_level_mitigation_action)
            pattern_matches.append((pattern[0], len(matches)))

        most_regex_matches = max(pattern_matches, key=lambda x: x[1], default=(None, 0))

        if most_regex_matches[1] == 0:
            print(f"No regex match found for action: {high_level_mitigation_action}")
            return None

        return most_regex_matches[0]

    def determine_action_type(self):
        playbook_tuple = list(filter(lambda t: self.chosen_playbook in t, self.current_patterns))

        if not playbook_tuple:
            print(f"No matching playbook found for chosen_playbook: {self.chosen_playbook}")
            return "UNKNOWN_ACTION_TYPE"

        return playbook_tuple[0][2]

    def extract_variables_from_yaml(self, yaml_file):
        variables = []
        jinja2_pattern = r'\{\{(.+?)\}\}'
        print(f"Current dir {os.getcwd()}")
        with open(yaml_file, 'r') as f:
            yaml_content = f.read()
            for line in yaml_content.split('\n'):
                matches = re.findall(jinja2_pattern, line)
                for match in matches:
                    variables.append(match.strip())

        return variables

    
    def fill_in_ansible_playbook(self):
        # Extracts the variables from the yaml file, that need to be replaced with actual values of the mitigation action
        variables = self.extract_variables_from_yaml(os.path.join("ansible_playbooks", self.chosen_playbook))
        playbook_variables_dict = {}

        # Loops through the variables and replaces them with the actual values of the mitigation action
        for variable in variables:
            if variable == 'mitigation_host':
                playbook_variables_dict['mitigation_host'] = self.mitigation_action.mitigation_host
                continue

            variable_value = re.findall(regex_patterns[variable], self.mitigation_action.action)
            playbook_variables_dict[variable] = variable_value[0] if variable_value else "UNKNOWN_VALUE"

        #Using the jinja2 library, the variables are replaced with the actual values of the mitigation action
        env = Environment(loader=FileSystemLoader('ansible_playbooks'))
        template = env.get_template(self.chosen_playbook)
        rendered_template = template.render(playbook_variables_dict)

        # Store the rendered template in the mitigation action's ansible_command field
        if hasattr(self.mitigation_action, 'ansible_command'):
            self.mitigation_action.ansible_command = rendered_template
        else:
            # For backward compatibility if the field doesn't exist
            setattr(self.mitigation_action, 'ansible_command', rendered_template)

        print(rendered_template)
        return rendered_template

    def simple_uploader(self, playbook_text):
        # Use the EPEM endpoint from the class initialization for the API URL
        api_url = self.epem_endpoint
        function_url = "/v2/horse/rtr_request"
        api_url = api_url + function_url
        # Set up the query parameters required by the API
        params = {
            "target_ip": self.mitigation_action.mitigation_host,  # Use the mitigation host as target IP
            "target_port": "22",  # Default SSH port for Ansible
            "service": "DNS",  # As specified in the documentation
            "actionType": self.action_type,  # Use the determined action type
            "actionID": self.mitigation_action.intent_id  # Use the intent_id as actionID
        }
        
        # Set up the headers
        headers = {
            "Content-Type": "application/yaml"
        }
        
        print(f"Sending playbook to endpoint: {api_url}")
        print(f"With parameters: {params}")
        
        try:
            # Send the request to the API
            response = requests.post(
                api_url,
                params=params,
                headers=headers,
                data=playbook_text
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                print("Upload completed successfully!")
                print(response.text)
                
                # Update mitigation action status and info to reflect success
                if hasattr(self.mitigation_action, 'status'):
                    self.mitigation_action.status = "sent_to_epem"
                else:
                    setattr(self.mitigation_action, 'status', "sent_to_epem")
                    
                if hasattr(self.mitigation_action, 'info'):
                    self.mitigation_action.info = f"Action successfully transformed and sent to ePEM. Response: {response.text[:100]}..."
                else:
                    setattr(self.mitigation_action, 'info', f"Action successfully transformed and sent to ePEM. Response: {response.text[:100]}...")
                
                return True
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response: {response.text if hasattr(response, 'text') else 'No response text'}")
                
                # Update mitigation action status and info to reflect failure
                if hasattr(self.mitigation_action, 'status'):
                    self.mitigation_action.status = "epem_forward_failed"
                else:
                    setattr(self.mitigation_action, 'status', "epem_forward_failed")
                    
                if hasattr(self.mitigation_action, 'info'):
                    self.mitigation_action.info = f"Failed to forward to ePEM endpoint. Status code: {response.status_code}. Response: {response.text[:100] if hasattr(response, 'text') else 'No response'}"
                else:
                    setattr(self.mitigation_action, 'info', f"Failed to forward to ePEM endpoint. Status code: {response.status_code}. Response: {response.text[:100] if hasattr(response, 'text') else 'No response'}")
                
                return False
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            
            # Update mitigation action status and info to reflect error
            if hasattr(self.mitigation_action, 'status'):
                self.mitigation_action.status = "epem_request_error"
            else:
                setattr(self.mitigation_action, 'status', "epem_request_error")
                
            if hasattr(self.mitigation_action, 'info'):
                self.mitigation_action.info = f"Error when communicating with ePEM: {str(e)}"
            else:
                setattr(self.mitigation_action, 'info', f"Error when communicating with ePEM: {str(e)}")
            
            return False


if __name__ == "__main__":
    mitigation_action = mitigation_action_model(
        command='add',
        intent_type='mitigation',
        threat='ddos',
        attacked_host='11.0.0.1',
        mitigation_host='172.16.2.1',
        action='disable dns server',
        duration=4000,
        intent_id='ABC123'
    )
    playbook = playbook_creator(mitigation_action)
    playbook_txt = playbook.fill_in_ansible_playbook()
    playbook.simple_uploader(playbook_text=playbook_txt)
