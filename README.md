# Reliable Trust Resilience

RTR is a software tool developed for the HORSE project. The purpose of the RTR is to accept a mitigation action for an attack targeting a network topology. This mitigation action is basically a JSON containing information both on the attack and the mitigation action that counters it. The RTR then extracts the useful information from this file and configures an Ansible Playbook. This Playbook is then sent to an enforcer, who uses it to configure parts of the network.

## Installation

Download and run the application:
- git clone https://github.com/HORSE-EU-Project/RTR.git
- cd RTR
- git checkout develop  # or main, depending on which branch you want to use
- Copy .env.example to .env and configure your environment variables (if .env.example exists)
- Deploy using the deployment script: `./deploy.sh --deployment_domain <DOMAIN>` where DOMAIN is CNIT, UPC, or UMU

Alternatively, you can run with Docker Compose directly:
- docker compose build
- docker compose up -d  # -d runs the application in the background

For more deployment options, run: `./deploy.sh --help` to see usage instructions.

## Deployment Script

The `deploy.sh` script provides automated deployment with named arguments for clarity and flexibility:

**Basic usage:**
```bash
./deploy.sh --deployment_domain <DOMAIN> [OPTIONS]
```

**Required arguments:**
- `--deployment_domain <DOMAIN>`: The testbed environment - CNIT, UPC, or UMU

**Optional arguments:**
- `--port <PORT>`: Custom port number (default: 8000 for CNIT/UPC, 8003 for UMU)
- `--epem <URL>`: EPEM endpoint URL (e.g., http://192.168.130.233:5002)
- `--doc <URL>`: DOC endpoint URL (e.g., http://192.168.130.62:8001)
- `-h, --help`: Show help message

**Examples:**
```bash
# Deploy to CNIT with default settings
./deploy.sh --deployment_domain CNIT

# Deploy to UMU with default settings (uses port 8003)
./deploy.sh --deployment_domain UMU

# Deploy to CNIT with custom port
./deploy.sh --deployment_domain CNIT --port 8080

# Deploy to UPC with custom EPEM endpoint
./deploy.sh --deployment_domain UPC --epem http://10.19.2.20:5002

# Deploy to CNIT with all custom settings
./deploy.sh --deployment_domain CNIT --port 8000 --epem http://10.0.0.1:5002 --doc http://10.0.0.2:8001
```

The script automatically:
- Detects your machine's IP address for callback URL configuration
- Updates the `.env` file with the specified configuration
- Sets RTR_HOST and RTR_PORT for status callback functionality
- Builds and starts the Docker containers
- Displays the deployment configuration summary

## Docker
This Dockerfile sets up an environment for running [rtr-api](https://github.com/HORSE-EU-Project/RTR/blob/main/IBI-RTR_api.py). It begins by specifying the base image as Python 3.11.5, establishing the working directory within the container as /app. Dependencies listed in requirements.txt are then installed using pip, ensuring the necessary packages are available. The FastAPI application code is copied into the container's working directory. Port 8000 is exposed to allow external access to the FastAPI application. Finally, the Dockerfile specifies the command to run the application, launching it with Uvicorn and binding to host 0.0.0.0 and port 8000. This Dockerfile encapsulates all the steps needed to build a Docker image capable of running the FastAPI application within a container, providing a consistent and reproducible environment for deployment.

## Docker-compose
This Docker Compose file [docker-compose.yml](https://github.com/HORSE-EU-Project/RTR/blob/main/docker-compose.yml) defines a multi-container application with two services: [rtr-api](https://github.com/HORSE-EU-Project/RTR/blob/main/IBI-RTR_api.py) and mongodb. Here's what each section does:
1. rtr-api Service:
Builds the Docker image for the rtr-api service using the Dockerfile in the current directory. We map port 8000 on the host to port 8000 in the container, allowing access to the FastAPI application running inside the container. We mount the current directory (where the Docker Compose file is located) to the /app directory inside the container, allowing live code reloading during development. This service depends on mongodb, meaning that the mongodb service needs to be up and running first. Finally, we connect the rtr-api service to the rtr-network network.
2. mongodb service:
We specify the Docker image to use for the mongodb service. We also set the container name to "mongodb" and configure the container to restart if it terminates unexpectedly. We  map default port 27017 on the host to port 27017 in the container, allowing access to the MongoDB server. The environment variables for configuring MongoDB are the root username and password for the MongoDB instance. We define volumes for persisting MongoDB data, initializing the database with [mongo-init.js](https://github.com/HORSE-EU-Project/RTR/blob/main/mongo-init.js), and providing a custom MongoDB configuration file [mongod.conf](https://github.com/HORSE-EU-Project/RTR/blob/main/db_confs/mongod.conf). Finally, we also connect 'mongodb' to the rtr-network.
 - [mongo-init.js](https://github.com/HORSE-EU-Project/RTR/blob/main/mongo-init.js) creates two collections, each with a predefined structure enforced by JSON schemas for validation. The "mitigation_actions" collection specifies requirements for documents representing mitigation actions, including fields like intent type, threat, and duration. Similarly, the "users" collection defines constraints for user documents, mandating fields such as username, email, and password, with email validation using a regular expression. These schemas ensure data consistency and integrity by validating documents against specified criteria upon insertion or update, enhancing the reliability and usability of the MongoDB database.
 - [mongod.conf](https://github.com/HORSE-EU-Project/RTR/blob/main/db_confs/mongod.conf) specifies the settings for running a MongoDB instance. In the storage section, the dbPath parameter indicates the directory where MongoDB will store its database files, set here to /data/db. The network settings define that MongoDB will bind to all available network interfaces (0.0.0.0) and listen on port 27017. Additionally, the security section enables access control and user authentication by setting authorization to enabled. This ensures that clients must authenticate themselves before accessing the database, enhancing the security of the MongoDB instance. Overall, this configuration file establishes a MongoDB environment with specified storage, network, and security settings.
  


## The main App

The application's functionality are fostered by FastAPI. The FastAPI application implements the following endpoints:
- root (GET): A welcome page.
- user register (POST): A registration interface for new users.
- user login (POST): A log-in interface for existing users. (OAuth 2.0)
- post an action (POST): Sends a new action to the RTR. (OAuth 2.0)
- get actions (GET): Requests all of the available actions currently stored inside the API. (OAuth 2.0)
- get specific action (GET): Requests a specific action based on the action's unique ID. (OAuth 2.0)
- update action status (POST): Updates an action's status based on the action's unique ID. (OAuth 2.0)
- reload configuration (POST): Reloads the mitigation action to playbook mappings without restarting the container. (OAuth 2.0)
- get action mappings (GET): Retrieves all currently loaded mitigation action to playbook mappings. (OAuth 2.0)

All endpoints except root, register, and login are protected with OAuth 2.0 authentication.


# User registration
In order to create a new user, we request 3 fields:
- username
- password
- email
The authentication uses the combination of the username and the password. The user's information are stored in our users collection inside our mongoDB database.

# User login
In order for the user to interact with the rest of the interfaces a Log-In is required. By logging in with their credentials users receive an authentication token. This authentication token is required as a header to the requests.

We followed the implementation in this article https://manjeetkapil.medium.com/create-a-authentication-system-using-react-fastapi-and-mongodb-farm-stack-d2ea6a35bf47 for the authorization aspects of the application.

# Post an action
The RTR was developed for the purposes of HORSE and it should receive input from IBI (Intent Based Interface). The partners from TUBS will provide us with JSONs describing mitigation actions in certain parts of the network topology. This is an example of such an action:

{
    "command": "add",
    "intent_type": "mitigation" or "prevention",
    "threat": e.g. "ddos",
    "attacked_host": e.g. "10.0.0.1",
    "mitigation_host": e.g. "172.16.2.1",
    "action": e.g. "Block potentially spoofed packets with destination 192.68.0.0/24 in interface wlan0",
    "duration": e.g. 7000,
    "intent_id": e.g. "ABC123",
    "target_domain": e.g. "CNIT" or "UPC",
    "status": e.g. "pending",
    "info": e.g. "Blocking spoofed packets in the specified IP range on wlan0 interface.",
    "ansible_command": e.g. ""
}

We validate the JSON against the schema requirements before processing. The mitigation action is then transformed into an Ansible playbook based on the mapping defined in [mitigation_ansible_map.json](https://github.com/HORSE-EU-Project/RTR/blob/main/RTR_configurations/mitigation_ansible_map.json). After successful creation, the action is stored in memory and its status is tracked throughout the execution lifecycle.

# Get actions
We expose 2 GET interfaces:
- The 1st interface returns every action currently stored in the application's in-memory storage
- The 2nd interface returns a specific action based on its unique intent_id

## Configuration Management

# Mitigation Action to Playbook Mapping
The RTR uses a configuration file [mitigation_ansible_map.json](https://github.com/HORSE-EU-Project/RTR/blob/main/RTR_configurations/mitigation_ansible_map.json) to map mitigation action types to their corresponding Ansible playbook files. This mapping file contains:

- **action_name_to_playbook**: A dictionary that maps action names (e.g., "DNS_RATE_LIMITING", "BLOCK_POD_ADDRESS") to their corresponding playbook paths (e.g., "ansible_playbooks/dns_rate_limiting.yaml")
- **metadata**: Version information, description, and last update timestamp

When a mitigation action is received, the RTR extracts the action type from the JSON payload and uses this mapping to determine which Ansible playbook template to use. This design allows for easy addition of new mitigation actions by simply updating the configuration file without modifying the application code.

Example mapping:
```json
{
  "action_name_to_playbook": {
    "DNS_RATE_LIMITING": "ansible_playbooks/dns_rate_limiting.yaml",
    "BLOCK_POD_ADDRESS": "ansible_playbooks/block_pod_address.yaml",
    "API_RATE_LIMITING": "ansible_playbooks/dns_rate_limiting.yaml"
  }
}
```

# Reload Configuration
The `/api/reload-config` endpoint (POST) allows authenticated users to reload the mitigation_ansible_map.json file without restarting the Docker container. This is useful when:
- New mitigation action mappings are added
- Existing mappings are updated
- Playbook paths are changed

The endpoint returns status information about the reload operation, including which configuration files were reloaded and any errors encountered.

# Get Action Mappings
The `/api/config/actions` endpoint (GET) allows authenticated users to retrieve all currently loaded mitigation action to playbook mappings. This is useful for:
- Verifying which mitigation actions are currently supported
- Debugging configuration issues
- Documenting available mitigation actions

The endpoint returns the total number of mappings and the complete action_name_to_playbook dictionary.

# Update Action Status
The `/update_action_status` endpoint allows you to update the status of a previously submitted mitigation action. This operation is useful for reflecting the current state of an action, such as when a mitigation process has been completed or encounters an issue. The endpoint accepts an intent_id, status, and optional info field to provide detailed status updates.