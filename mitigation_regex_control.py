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
        self.action_type, self.chosen_playbook = self.match_mitigation_action_with_playbook()
        
        # Fill in the Ansible playbook with actual values if the playbook was found
        if self.chosen_playbook != "UNKNOWN_ACTION_TYPE":
            # Try to fill in the playbook with actual values
            self.fill_in_ansible_playbook()
        
        
        # Get the EPEM endpoint from environment variables
        # The .env file already includes the protocol, so we don't need to add it
        self.epem_endpoint = os.getenv('EPEM_ENDPOINT', 'http://httpbin.org/post')
            
        print(f"EPEM endpoint: {self.epem_endpoint}")
        print(self.chosen_playbook)

    
    def dict_ansible_transformation(self):
        """
        Handle dictionary-based action transformation to playbook mapping.
        Returns tuple of (action_name, playbook_filename)
        """
        # If it's a dictionary, use the action name as the primary criteria
        action_obj = self.mitigation_action.action
        action_name = action_obj.get("name", "").upper() # maybe need to add control for uppercase
        
        # Map action names directly to playbooks if possible
        action_name_to_playbook = {
            #ePEM action Types:
            "DNS_RATE_LIMIT": "dns_rate_limiting.yaml",
            "DNS_SERV_DISABLE": "dns_service_disable.yaml",
            "DNS_SERV_ENABLE": "dns_service_enable.yaml",
            "TEST": "test_1.yaml",
            
            #other action types:
            "DNS_RATE_LIMITING": "dns_rate_limiting.yaml",
            "DNS_SERVICE_DISABLE": "dns_service_disable.yaml",
            "DNS_SERVICE_HANDOVER": "dns_service_handover.yaml",
            "DNS_FIREWALL_SPOOFING_DETECTION": "dns_firewall_spoofing_detection.yaml",
            "TEST_2": "test_2.yaml"
        }
        
        # If we have a direct mapping, return it immediately
        if action_name in action_name_to_playbook:
            return action_name, action_name_to_playbook[action_name]
        else:
            error_msg = f"No matching playbook found for action name: {action_name}. Allowed action names (case insensitive) are: {', '.join(action_name_to_playbook.keys())}"
            print(error_msg)  # Keep for server logs
            # Store the error message in the mitigation action for API response
            self.mitigation_action.info = error_msg
            return action_name, "UNKNOWN_ACTION_TYPE"

    def string_ansible_transformation(self):
        """
        Handle string-based action transformation using regex patterns.
        Returns tuple of (action_type, playbook_filename)
        """
        high_level_mitigation_action = self.mitigation_action.action
        
        # Use regex patterns to match the string action to a playbook
        best_match = None
        best_match_count = 0
        
        for playbook_file, pattern, action_type in self.current_patterns:
            matches = re.findall(pattern, high_level_mitigation_action, re.IGNORECASE)
            match_count = len(matches)
            
            if match_count > best_match_count:
                best_match_count = match_count
                best_match = (action_type, playbook_file)
        
        if best_match:
            return best_match
        else:
            error_msg = f"No matching playbook found for string action: '{high_level_mitigation_action}'"
            print(error_msg)
            self.mitigation_action.info = error_msg
            return "UNKNOWN_ACTION_TYPE", "UNKNOWN_ACTION_TYPE"

    def match_mitigation_action_with_playbook(self):
        # Check if action is a string or a dictionary
        if isinstance(self.mitigation_action.action, str):
            return self.string_ansible_transformation()
        else:
            # Use the new dict_ansible_transformation method
            return self.dict_ansible_transformation()

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
        # Extracts the variables from the yaml file, that need to be replaced with actual values
        variables = self.extract_variables_from_yaml(os.path.join("ansible_playbooks", self.chosen_playbook))
        playbook_variables_dict = {}

        # Loops through the variables and replaces them with the actual values
        for variable in variables:
            if variable == 'mitigation_host':
                playbook_variables_dict['mitigation_host'] = self.mitigation_action.mitigation_host
                continue
            
            if variable == 'target_domain' and self.mitigation_action.target_domain:
                # Use target_domain from the main model if available
                playbook_variables_dict['target_domain'] = self.mitigation_action.target_domain
                continue
            
            # Check if action is a string or dictionary
            if isinstance(self.mitigation_action.action, str):
                # Original string-based processing with regex
                variable_value = re.findall(regex_patterns.get(variable, r''), self.mitigation_action.action)
                playbook_variables_dict[variable] = variable_value[0] if variable_value else "UNKNOWN_VALUE"
            else:
                # Dictionary-based processing - extract from fields
                fields = self.mitigation_action.action.get("fields", {})
                
                # Map playbook variables to action fields
                if variable == 'rate' and 'rate' in fields:
                    playbook_variables_dict[variable] = str(fields['rate'])
                elif variable == 'requests_per_sec' and 'rate' in fields:
                    playbook_variables_dict[variable] = f"{fields['rate']}/s"
                elif variable == 'duration' and 'duration' in fields:
                    playbook_variables_dict[variable] = str(fields['duration'])
                elif variable == 'target_domain' and 'target_domain' in fields:
                    playbook_variables_dict[variable] = fields['target_domain']
                elif variable == 'protocol' and 'protocol' in fields:
                    playbook_variables_dict[variable] = fields['protocol']
                elif variable == 'ipv4_and_subnet' and 'ip_range' in fields:
                    playbook_variables_dict[variable] = fields['ip_range']
                elif variable == 'interface_name' and 'interface' in fields:
                    playbook_variables_dict[variable] = fields['interface']
                elif variable == 'port' and 'port' in fields:
                    playbook_variables_dict[variable] = str(fields['port'])
                else:
                    playbook_variables_dict[variable] = "UNKNOWN_VALUE"

        # Using the jinja2 library, the variables are replaced with the actual values
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
            "target_ip": self.mitigation_action.mitigation_host,  # Already has default "0.0.0.0"
            "target_port": "22",  # Default SSH port for Ansible
            "service": "DNS",
            "actionType": self.action_type,
            "actionID": self.mitigation_action.intent_id  # Required field
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
                
                # Update mitigation action status and info
                self.mitigation_action.status = "sent_to_epem"
                self.mitigation_action.info = f"Action successfully transformed and sent to ePEM. Response: {response.text[:100]}..."
                return True
            else:
                print(f"Request failed with status code: {response.status_code}")
                print(f"Response: {response.text if hasattr(response, 'text') else 'No response text'}")
                
                # Update mitigation action status and info for failure
                self.mitigation_action.status = "epem_forward_failed"
                self.mitigation_action.info = f"Failed to forward to ePEM endpoint. Status code: {response.status_code}. Response: {response.text[:100] if hasattr(response, 'text') else 'No response'}"
                return False
                
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            
            # Update mitigation action status and info for error
            self.mitigation_action.status = "epem_request_error"
            self.mitigation_action.info = f"Error when communicating with ePEM: {str(e)}"
            return False


if __name__ == "__main__":
    mitigation_action = mitigation_action_model(
        command='add',
        intent_type='mitigation',
        intent_id='ABC123',
        action='disable dns server',
        # Optional fields with defaults
        threat='ddos',          # defaults to "unknown"
        attacked_host='11.0.0.1',  # defaults to "0.0.0.0"
        mitigation_host='172.16.2.1',  # defaults to "0.0.0.0"
        duration=4000,          # defaults to 0
        # These fields have defaults, no need to specify unless you want to override
        # status defaults to "pending"
        # info defaults to "to be enforced"
        # ansible_command defaults to ""
    )
    playbook = playbook_creator(mitigation_action)
    playbook_txt = playbook.fill_in_ansible_playbook()
    playbook.simple_uploader(playbook_text=playbook_txt)
