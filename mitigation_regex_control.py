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
        
        # Get the DOC endpoint from environment variables (fallback when ePEM is unresponsive)
        self.doc_endpoint = os.getenv('DOC_ENDPOINT', 'http://192.168.130.62:8001')
            
        print(f"EPEM endpoint: {self.epem_endpoint}")
        print(f"DOC endpoint (fallback): {self.doc_endpoint}")
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
            "TEST_2": "test_2.yaml",
            
            #Demo_0 mitigation type block_pod_address
            #"BLOCK_POD_ADDRESS": "dns_rate_limiting.yaml"
            "BLOCK_POD_ADDRESS": "block_pod_address.yaml",
            "BLOCK_POD_ADDRESSES": "block_pod_address.yaml",
            "BLOCK_IP_ADDRESSES": "block_pod_address.yaml",
            
            #Demo_10 API rate limiting mitigation type
            "API_RATE_LIMITING": "dns_rate_limiting.yaml",
            "API_RATE_LIMIT": "dns_rate_limiting.yaml",
            
            
            #Multidomain demo mitigation type
            "BLOCK_UES_MULTIDOMAIN": "block_pod_address.yaml"
            

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

        # Loops through the variables and replaces them with actual values.
        # Provide compact, sensible defaults for any missing variables.
        defaults = {
            'mitigation_host': getattr(self.mitigation_action, 'mitigation_host', '0.0.0.0') or '0.0.0.0',
            'target_domain': getattr(self.mitigation_action, 'target_domain', 'unknown') or 'unknown',
            'rate': '1',
            'requests_per_sec': '1/second',
            'duration': '0',
            'protocol': 'tcp',
            'ipv4_and_subnet': '0.0.0.0/32',
            'interface_name': 'eth0',
            'port': '53'
        }

        def _get_field(name):
            if isinstance(self.mitigation_action.action, dict):
                return self.mitigation_action.action.get('fields', {}).get(name)
            return None

        for variable in variables:
            # Direct substitutions with priority: explicit attribute -> action.fields -> regex/string -> default
            if variable == 'mitigation_host':
                playbook_variables_dict['mitigation_host'] = getattr(self.mitigation_action, 'mitigation_host', None) or defaults['mitigation_host']
                continue

            if variable == 'target_domain':
                playbook_variables_dict['target_domain'] = (
                    getattr(self.mitigation_action, 'target_domain', None)
                    or _get_field('target_domain')
                    or defaults['target_domain']
                )
                continue

            if isinstance(self.mitigation_action.action, str):
                # Try regex extraction first, then fall back to default
                variable_value = re.findall(regex_patterns.get(variable, r''), self.mitigation_action.action)
                playbook_variables_dict[variable] = variable_value[0] if variable_value else defaults.get(variable, 'UNKNOWN_VALUE')
            else:
                # Dictionary-based processing - extract from fields with defaults
                if variable == 'rate':
                    v = _get_field('rate') or _get_field('limit')
                    playbook_variables_dict[variable] = str(v) if v is not None else defaults['rate']
                elif variable == 'requests_per_sec':
                    v = _get_field('rate') or _get_field('limit')
                    playbook_variables_dict[variable] = f"{v}/second" if v is not None else defaults['requests_per_sec']
                elif variable == 'duration':
                    v = _get_field('duration')
                    playbook_variables_dict[variable] = str(v) if v is not None else defaults['duration']
                elif variable == 'protocol':
                    v = _get_field('protocol')
                    playbook_variables_dict[variable] = v if v is not None else defaults['protocol']
                elif variable == 'ipv4_and_subnet':
                    v = _get_field('ip_range')
                    playbook_variables_dict[variable] = v if v is not None else defaults['ipv4_and_subnet']
                elif variable == 'interface_name':
                    v = _get_field('interface')
                    playbook_variables_dict[variable] = v if v is not None else defaults['interface_name']
                elif variable == 'port':
                    v = _get_field('port')
                    playbook_variables_dict[variable] = str(v) if v is not None else defaults['port']
                else:
                    playbook_variables_dict[variable] = defaults.get(variable, 'UNKNOWN_VALUE')

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
        # Build the JSON payload according to the expected schema
        payload = {
            "command": self.mitigation_action.command,
            "intent_type": self.mitigation_action.intent_type,
            "intent_id": self.mitigation_action.intent_id,
            "threat": self.mitigation_action.threat,
            "target_domain": self.mitigation_action.target_domain,
            "action": self.mitigation_action.action,
            "attacked_host": self.mitigation_action.attacked_host,
            "mitigation_host": self.mitigation_action.mitigation_host,
            "duration": self.mitigation_action.duration,
            "status": self.mitigation_action.status,
            "info": self.mitigation_action.info,
            "ansible_command": playbook_text
        }

        headers = {
            "Content-Type": "application/json"
        }

        # Try ePEM first, then fallback to DOC if ePEM is unresponsive
        endpoints = [
            (self.epem_endpoint + "/v2/horse/rtr_request", "ePEM"),
            (self.doc_endpoint + "/api/mitigate", "DOC")
        ]
        
        for api_url, endpoint_name in endpoints:
            print(f"Attempting to send request to {endpoint_name} endpoint: {api_url}")
            print(f"Payload: {payload}")

            try:
                # Send the request to the API with JSON payload and timeout
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=10  # 10 second timeout for connection
                )

                # Handle different response status codes with concise information
                if response.status_code == 200:
                    print(f"Upload completed successfully to {endpoint_name}!")
                    print(response.text)

                    # Update mitigation action status and info for success
                    self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                    self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} sent to DOC → DOC successfully enforced action"
                    return True
                elif response.status_code == 201:
                    print(f"Action created successfully at {endpoint_name}!")
                    print(response.text)

                    # Update mitigation action status and info for created
                    self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                    self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} created action → DOC processing enforcement"
                    return True
                elif response.status_code == 202:
                    print(f"Action accepted by {endpoint_name} for processing!")
                    print(response.text)

                    # Update mitigation action status and info for accepted
                    self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                    self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} accepted and queued → Waiting for DOC enforcement"
                    return True
                elif response.status_code == 400:
                    print(f"Bad request to {endpoint_name} - invalid payload: {response.status_code}")
                    print(f"Response: {response.text}")
                    # Don't return False yet, try next endpoint
                    if endpoint_name == "DOC":
                        self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                        self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} rejected (400 Bad Request) → DOC enforcement failed"
                        return False
                    continue  # Try next endpoint
                elif response.status_code == 401:
                    print(f"Unauthorized request to {endpoint_name}: {response.status_code}")
                    print(f"Response: {response.text}")
                    # Don't return False yet, try next endpoint
                    if endpoint_name == "DOC":
                        self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                        self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} rejected (401 Unauthorized) → DOC enforcement failed"
                        return False
                    continue  # Try next endpoint
                elif response.status_code == 404:
                    print(f"{endpoint_name} endpoint not found: {response.status_code}")
                    print(f"Response: {response.text}")
                    # Don't return False yet, try next endpoint
                    if endpoint_name == "DOC":
                        self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                        self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} endpoint not found (404) → DOC enforcement failed ({response.text})"
                        return False
                    continue  # Try next endpoint
                elif response.status_code >= 500:
                    print(f"{endpoint_name} server error: {response.status_code}")
                    print(f"Response: {response.text}")
                    # Don't return False yet, try next endpoint
                    if endpoint_name == "DOC":
                        self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                        self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} server error ({response.status_code}) → DOC enforcement failed ({response.text})"
                        return False
                    continue  # Try next endpoint
                else:
                    print(f"Unexpected response status code from {endpoint_name}: {response.status_code}")
                    print(f"Response: {response.text}")
                    # Don't return False yet, try next endpoint
                    if endpoint_name == "DOC":
                        self.mitigation_action.status = f"sent_to_{endpoint_name.lower()}"
                        self.mitigation_action.info = f"Sent to {endpoint_name} → {endpoint_name} unexpected response ({response.status_code}) → DOC enforcement failed ({response.text})"
                        return False
                    continue  # Try next endpoint

            except requests.exceptions.Timeout:
                print(f"Timeout when connecting to {endpoint_name}")
                # If this is the last endpoint (DOC), update status and return False
                if endpoint_name == "DOC":
                    self.mitigation_action.status = "all_endpoints_failed"
                    self.mitigation_action.info = f"ePEM unresponsive (timeout) → Tried DOC fallback but also timed out"
                    return False
                # Otherwise, continue to next endpoint
                print(f"Trying fallback to DOC...")
                continue
                
            except requests.exceptions.ConnectionError:
                print(f"Connection error when connecting to {endpoint_name}")
                # If this is the last endpoint (DOC), update status and return False
                if endpoint_name == "DOC":
                    self.mitigation_action.status = "all_endpoints_failed"
                    self.mitigation_action.info = f"ePEM unresponsive (connection error) → Tried DOC fallback but also failed to connect"
                    return False
                # Otherwise, continue to next endpoint
                print(f"Trying fallback to DOC...")
                continue
                
            except Exception as e:
                print(f"An error occurred when connecting to {endpoint_name}: {str(e)}")
                # If this is the last endpoint (DOC), update status and return False
                if endpoint_name == "DOC":
                    self.mitigation_action.status = "all_endpoints_failed"
                    self.mitigation_action.info = f"ePEM unresponsive ({str(e)}) → Tried DOC fallback but also failed: {str(e)}"
                    return False
                # Otherwise, continue to next endpoint
                print(f"Trying fallback to DOC...")
                continue
        
        # If we get here, all endpoints failed
        self.mitigation_action.status = "all_endpoints_failed"
        self.mitigation_action.info = "Failed to send action to both ePEM and DOC endpoints"
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
