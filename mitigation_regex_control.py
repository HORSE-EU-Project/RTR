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
horse_topology_expressions = ['dns-c1', 'dns-c2', 'dns-c3', 'dns-c4', 'dns-c5', 'dns-c6', 'dns-c7', 'dns-c8', 'dns-c9', 'dns-c10', 'gnb', 'ceos1', 'ceos2', 'upf', 'dns-s', 'gateway', 'ausf', 'amf', 'smf', 'udm', 'nssf', 'udr', 'nrf', 'pcf']
horse_topology_patterns = '|'.join(horse_topology_expressions)
regex_patterns = {
    #'ipv4_and_subnet': r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b|\b({horse_topology_patterns})\b',#|\b({horse_topology_patterns})\b
    'ipv4_and_subnet' : fr'\b(?:{horse_topology_patterns})\b', 
    'protocol': r'\b(tcp|udp)\b',
    'requests_per_sec': r'\b(\d{1,3}\/s)\b',
    'port': rf'\b(?:{"|".join(expressions)})\b\s*(\d+(?:,\d+)*)',
    'interface_name': r'\b(eth\d+|en[pso]\w*|wlan\d+|lo)\b'
}



class playbook_creator:
    def __init__(self, action_from_IBI):
        self.current_patterns = [('dns_rate_limiting.yaml', r'\b(reduce|decrease|requests|number|rate|limit|dns|server|service|\d{1,3}\/s)\b', 'DNS_RATE_LIMIT'),
                            ('dns_service_disable.yaml', r'\b(disable|shut down|dns|server|service)\b','DNS_SERV_DISABLE'), 
                            ('dns_service_enable.yaml', r'\b(enable|dns|server|service)\b','DNS_SERV_ENABLE'),
                            ('dns_service_handover', r'\b(hand over|dns|server|service)\b'),
                            ('dns_firewall_spoofing_detection.yaml', r'\b(spoof|spoofed|destination|spoofing|packets|firewall|interface|block|stop|ip|ip range)\b','DNS_FIREWALL_SPOOF'),
                            ('anycast_blackhole', r'\b(redirect|direct|dns|server|service|traffic|igress|blackhole)\b')]
        self.mitigation_action = action_from_IBI
        self.chosen_playbook = self.match_mitigation_action_with_playbook()
        self.action_type = self.determine_action_type()
        print(self.chosen_playbook)

    
    def match_mitigation_action_with_playbook(self):
        high_level_mitigation_action = self.mitigation_action.action

        pattern_matches = []
        for pattern in self.current_patterns:
            matches = re.findall(pattern[1], high_level_mitigation_action)
            pattern_matches.append((pattern[0],len(matches)))
            print(pattern_matches)


        most_regex_matches = max(pattern_matches, key=lambda x: x[1])
        print(most_regex_matches)
        
        return most_regex_matches[0]
    
    def determine_action_type(self):
        playbook_tuple = list(filter(lambda t: self.chosen_playbook in t, self.current_patterns))
        action_type = playbook_tuple[0][2]
        return action_type
        
    
    def extract_variables_from_yaml(self,yaml_file):
        variables = []
        jinja2_pattern = r'\{\{(.+?)\}\}'  # Regular expression to match Jinja2 expressions
        print(f"Current dir {os.getcwd()}")
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
        print(variables)
        for variable in variables:
            if variable == 'mitigation_host':
                playbook_variables_dict['mitigation_host'] = os.getenv(self.mitigation_action.mitigation_host)
                print(playbook_variables_dict)
                continue
            
            
            variable_value = re.findall(regex_patterns[variable], self.mitigation_action.action)
            print(variable_value)
            if variable_value[0] in os.environ:
                playbook_variable_value = os.getenv(variable_value[0])
            else:
                playbook_variable_value = variable_value[0]
            #print(variable_value)
            playbook_variables_dict[variable] = playbook_variable_value
        
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
    mitigation_action = mitigation_action_model(command='add', intent_type='mitigation', threat='ddos', attacked_host='11.0.0.1', mitigation_host='udm', action='enable dns server', duration=4000,intent_id='ABC123')
    playbook = playbook_creator(mitigation_action)
    palybok_txt = playbook.fill_in_ansible_playbook()
    playbook.simple_uploader(playbook_text=palybok_txt)






