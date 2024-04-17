import re
import requests
from mitigation_action_class import mitigation_action_model
import os
#from ansible.parsing.dataloader import DataLoader
#from ansible.template import Templar
#from ansible.parsing.yaml.loader import load_yaml_from_io
from jinja2 import Environment, FileSystemLoader
#Find to what playbook the regular exression refers to

expressions = ['port','ports']
regex_patterns = {
    'ipv4_and_subnet': r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b',
    'protocol': r'\b(tcp|udp)\b',
    'requests_per_sec': r'\b(\d{1,3}\/s)\b',
    'port': rf'\b(?:{"|".join(expressions)})\b\s*(\d+(?:,\d+)*)',
    'interface_name': r'\b(eth\d+|en[pso]\w*|wlan\d+|lo)\b'
}



class playbook_creator:
    def __init__(self, action_from_IBI):
        self.current_patterns = [('dns_rate_limiting.yaml', r'\b(reduce|decrease|requests|number|rate|limit|dns|server|service|\d{1,3}\/s)\b'),
                            ('dns_service_disbale.yaml', r'\b(disable|shut down|dns|server|service)\b'), 
                            ('dns_service_handover', r'\b(hand over|dns|server|service)\b'),
                            ('dns_firewall_spoofing_detection.yaml', r'\b(spoof|spoofing|firewall|interface|block|stop|ip|ip range)\b'),
                            ('anycast_blackhole', r'\b(redirect|direct|dns|server|service|traffic|igress|blackhole)\b')]
        self.mitigation_action = action_from_IBI
        self.chosen_playbook = self.match_mitigation_action_with_playbook()
        print(self.chosen_playbook)

    
    def match_mitigation_action_with_playbook(self):
        high_level_mitigation_action = self.mitigation_action.action

        pattern_matches = []
        for pattern in self.current_patterns:
            matches = re.findall(pattern[1], high_level_mitigation_action)
            pattern_matches.append((pattern[0],len(matches)))


        most_regex_matches = max(pattern_matches, key=lambda x: x[1])


        return most_regex_matches[0]
    
    
    def extract_variables_from_yaml(self,yaml_file):
        variables = []
        jinja2_pattern = r'\{\{(.+?)\}\}'  # Regular expression to match Jinja2 expressions

        with open(yaml_file, 'r') as f:
            yaml_content = f.read()
            for line in yaml_content.split('\n'):
                matches = re.findall(jinja2_pattern, line)
                for match in matches:
                    variables.append(match.strip())

        return variables

    def fill_in_ansible_playbook(self):

        variables = self.extract_variables_from_yaml(os.path.join("ansible_playbooks", self.chosen_playbook))
        playbook_variables_dict = {}
        
       # print(f"hello {variables}")
        for variable in variables:
            #print(f"Current variable {variable}")
            if variable == 'mitigation_host':
                playbook_variables_dict['mitigation_host'] = self.mitigation_action.mitigation_host
                continue
            
            #print(f"Regex pattern {regex_patterns[variable]}")
            variable_value = re.findall(regex_patterns[variable], self.mitigation_action.action)
            #print(f"Variable value {variable_value}")
            playbook_variables_dict[variable] = variable_value[0]
        #print("Variables: ",playbook_variables_dict)
        # Load the template file
        
        env = Environment(loader=FileSystemLoader('ansible_playbooks'))

        template = env.get_template(self.chosen_playbook)
        # Render the template with the variables
        rendered_template = template.render(playbook_variables_dict)

        #Print the rendered template
        print(rendered_template)
        return rendered_template


    def simple_uploader(self, playbook_text):
        #test_file = open("mitigation_rules.yaml", "rb")


        receiver_url = "http://httpbin.org/post"

        test_response = requests.post(receiver_url, files = {"form_field_name": playbook_text})

        if test_response.ok:
            print("Upload completed successfully!")
            print(test_response.text)
        else:
            print("Something went wrong!")


        



if __name__ == "__main__":
    mitigation_action = mitigation_action_model(command='add', intent_type='mitigation', threat='ddos', attacked_host='10.0.0.1', mitigation_host='172.16.2.1', action='Allow traffic from iprange 192.69.0.1/24 to interface wlan1', duration=4000,intent_id='ABC123')
    playbook = playbook_creator(mitigation_action)
    palybok_txt = playbook.fill_in_ansible_playbook()
    playbook.simple_uploader(playbook_text=palybok_txt)






