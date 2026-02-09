# Reliable Trust Resilience (RTR)

RTR is an intent-based cybersecurity orchestration software developed for the HORSE project. It manages mitigation and prevention actions for network security threats through intelligent automation.

## Overview

RTR serves as a bridge between security intent and infrastructure enforcement. The software:

- **Accepts security actions** in both structured (JSON) and unstructured (natural language) formats
- **Translates intents** into infrastructure-as-code languages (currently Ansible playbooks)
- **Enriches actions** with necessary metadata including target domains, hosts, durations, and callback URLs
- **Distributes playbooks** to specified enforcement endpoints (ePEM or DOC) for execution on the network infrastructure

This approach enables security teams to express mitigation strategies in high-level terms while RTR handles the technical translation and orchestration required for actual implementation across distributed network environments.

## Installation

### Prerequisites
- Docker and Docker Compose installed
- Git
- Bash shell (Linux/macOS/WSL/Git Bash on Windows)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/HORSE-EU-Project/RTR.git
   cd RTR
   ```

2. **Choose your branch:**
   ```bash
   git checkout develop  # Development branch (latest features)
   # or
   git checkout main     # Stable release branch
   ```

3. **Configure environment variables:**
   - The `.env` file contains default configurations
   - Verify or update MongoDB credentials, testbed endpoints, and ports as needed

4. **Deploy using the deployment script:**
   ```bash
   ./deploy.sh --deployment_domain <DOMAIN>
   ```
   Where `<DOMAIN>` is one of: CNIT, UPC, or UMU

### Alternative: Manual Docker Compose Deployment

If you prefer manual control:
```bash
docker compose build
docker compose up -d  # -d runs in detached mode (background)
```

### Getting Help

For all deployment options and parameters:
```bash
./deploy.sh --help
```

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

## Container Architecture

### Docker
The Dockerfile sets up an environment for running the [RTR API](https://github.com/HORSE-EU-Project/RTR/blob/main/IBI-RTR_api.py). Key features:

- **Base Image**: Python 3.11.5
- **Working Directory**: /app
- **Dependencies**: Installed from requirements.txt via pip
- **Application Code**: Copied into container's working directory
- **Exposed Port**: 8000 for external access
- **Launch Command**: Uvicorn server binding to 0.0.0.0:8000

This provides a consistent and reproducible environment for deployment.

### Docker Compose
The [docker-compose.yml](https://github.com/HORSE-EU-Project/RTR/blob/main/docker-compose.yml) file defines a multi-container application with two services:

**1. rtr-api Service:**
- Builds the Docker image from the local Dockerfile
- Maps port 8000 (host) to 8000 (container) for API access
- Mounts the current directory to /app for live code reloading during development
- Depends on mongodb service (starts after MongoDB is ready)
- Connected to rtr-network

**2. mongodb Service:**
- Uses official MongoDB 4.4 image
- Container name: "mongodb"
- Auto-restart: enabled
- Port mapping: 27017 (host) to 27017 (container)
- Environment: Root username and password configured via .env
- Volumes:
  - **mongodb_data**: Persistent data storage
  - **[mongo-init.js](https://github.com/HORSE-EU-Project/RTR/blob/main/mongo-init.js)**: Database initialization with collection schemas for "mitigation_actions" and "users"
  - **[mongod.conf](https://github.com/HORSE-EU-Project/RTR/blob/main/db_confs/mongod.conf)**: Custom MongoDB configuration (storage path, network binding, authentication)
- Connected to rtr-network

The MongoDB collections enforce JSON schema validation to ensure data consistency and integrity for mitigation actions and user credentials.
  


## API Architecture

The application is powered by FastAPI and implements the following REST endpoints:

### Public Endpoints
- **root (GET)**: Welcome page and API information
- **user register (POST)**: Registration interface for new users
- **user login (POST)**: Authentication interface for existing users (OAuth 2.0)

### Protected Endpoints (OAuth 2.0 Required)
- **post an action (POST)**: Submit a new mitigation/prevention action to RTR
- **get actions (GET)**: Retrieve all actions currently stored in the system
- **get specific action (GET)**: Retrieve a specific action by its unique intent_id
- **update action status (POST)**: Update an action's status by its intent_id
- **reload configuration (POST)**: Reload mitigation action to playbook mappings without restart
- **get action mappings (GET)**: Retrieve all currently loaded action-to-playbook mappings

All endpoints except root, register, and login require OAuth 2.0 authentication.

## Authentication

### User Registration
To create a new user, provide:
- **username**: Unique identifier for the user
- **password**: Secure password for authentication
- **email**: Valid email address

User credentials are securely stored in the MongoDB users collection.

### User Login
Users must authenticate to interact with protected endpoints. Upon successful login with valid credentials, users receive an authentication token that must be included in the Authorization header for subsequent requests.

Authentication implementation follows the pattern described in [this article](https://manjeetkapil.medium.com/create-a-authentication-system-using-react-fastapi-and-mongodb-farm-stack-d2ea6a35bf47).

## Submitting Mitigation Actions
## Submitting Mitigation Actions

RTR accepts security actions from the Intent-Based Interface (IBI) component. Actions can be submitted in two formats:

### Structured Format (JSON)
A complete JSON action includes:

```json
{
    "command": "add",
    "intent_type": "mitigation",
    "threat": "ddos",
    "attacked_host": "10.0.0.1",
    "mitigation_host": "172.16.2.1",
    "action": {
        "name": "block_pod_address",
        "intent_id": "ABC123",
        "fields": {
            "blocked_ips": ["192.168.0.10"],
            "duration": 7000
        }
    },
    "duration": 7000,
    "intent_id": "ABC123",
    "target_domain": "CNIT",
    "status": "pending",
    "info": "Blocking spoofed packets in the specified IP range.",
    "ansible_command": ""
}
```

### Unstructured Format (Natural Language)
Alternatively, actions can be expressed in natural language:

```json
{
    "intent_id": "ABC124",
    "action": "Block potentially spoofed packets with destination 192.68.0.0/24 in interface wlan0"
}
```

### Processing Pipeline

1. **Validation**: The action is validated against schema requirements
2. **Translation**: The action is transformed into an Ansible playbook based on mappings defined in [mitigation_ansible_map.json](https://github.com/HORSE-EU-Project/RTR/blob/main/RTR_configurations/mitigation_ansible_map.json)
3. **Enrichment**: Metadata (callback URLs, timestamps, target domains) is added
4. **Storage**: The action is stored in MongoDB with status tracking
5. **Distribution**: The playbook is sent to the appropriate enforcement endpoint (ePEM or DOC)

## Retrieving Actions

RTR provides two GET endpoints for action retrieval:
- **GET /actions**: Returns all actions currently stored in the system
- **GET /actions/{intent_id}**: Returns a specific action by its unique intent_id

## Configuration Management

### Mitigation Action to Playbook Mapping

The RTR uses a configuration file [mitigation_ansible_map.json](https://github.com/HORSE-EU-Project/RTR/blob/main/RTR_configurations/mitigation_ansible_map.json) to map mitigation action types to their corresponding Ansible playbook files. This mapping file contains:

- **action_name_to_playbook**: A dictionary that maps action names (e.g., "DNS_RATE_LIMITING", "BLOCK_POD_ADDRESS") to their corresponding playbook paths (e.g., "ansible_playbooks/dns_rate_limiting.yaml")
- **metadata**: Version information, description, and last update timestamp

When a mitigation action is received, RTR extracts the action type from the JSON payload and uses this mapping to determine which Ansible playbook template to use. This design allows for easy addition of new mitigation actions by simply updating the configuration file without modifying the application code.

Example mapping:
```json
{
  "action_name_to_playbook": {
    "DNS_RATE_LIMITING": "ansible_playbooks/dns_rate_limiting.yaml",
    "BLOCK_POD_ADDRESS": "ansible_playbooks/block_pod_address.yaml",
    "API_RATE_LIMITING": "ansible_playbooks/api_rate_limiting.yaml"
  }
}
```

### Reload Configuration

The `/api/reload-config` endpoint (POST) allows authenticated users to reload the mitigation_ansible_map.json file without restarting the Docker container. This is useful when:
- New mitigation action mappings are added
- Existing mappings are updated
- Playbook paths are changed

The endpoint returns status information about the reload operation, including which configuration files were reloaded and any errors encountered.

### Get Action Mappings

The `/api/config/actions` endpoint (GET) allows authenticated users to retrieve all currently loaded mitigation action to playbook mappings. This is useful for:
- Verifying which mitigation actions are currently supported
- Debugging configuration issues
- Documenting available mitigation actions

The endpoint returns the total number of mappings and the complete action_name_to_playbook dictionary.

## Update Action Status

The `/update_action_status` endpoint allows enforcement endpoints to update the status of a previously submitted mitigation action. This operation reflects the current state of an action, such as when a mitigation process has been completed or encounters an issue. The endpoint accepts an intent_id, status, and optional info field to provide detailed status updates.