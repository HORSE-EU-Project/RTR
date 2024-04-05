import yaml
import json

# Read YAML data from file
with open('ansible_playbooks/dns_rate_limiting.yaml', 'r') as file:
    yaml_data = yaml.safe_load(file)

# Convert YAML data to JSON format
json_data = json.dumps(yaml_data, indent=4)

# Write JSON data to a file
with open('data.json', 'w') as file:
    file.write(json_data)


with open('data.json', 'r') as file:
    json_data = json.load(file)
#print(json_data)
# Convert JSON data to YAML format
yaml_data = yaml.dump(json_data, default_flow_style=False, sort_keys=False)

# Write YAML data to a file
with open('data.yaml', 'w') as file:
    file.write(yaml_data)