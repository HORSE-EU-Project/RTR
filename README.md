# Reliable Trust Resilience

RTR is a software tool developed for the HORSE project. The purpose of the RTR is to accept a mitigation action for an attack targeting a network topology. This mitigation action is basically a JSON containing information both on the attack and the mitigation action that counters it. The RTR then extracts the useful information from this file and configures an Ansible Playbook. This Playbook is then sent to an enforcer, who uses it to configure parts of the network.

## Installation

Downlad and run the application:
- git clone [https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR.git](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR.git)
- cd Reliability-Trust-Resilience-RTR
- git pull origin master
- docker-compose build
- docker-compose up -d (-d: runs the application in the background)

## Docker
This Dockerfile sets up an environment for running [rtr-api](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR/blob/main/IBI-RTR_api.py). It begins by specifying the base image as Python 3.11.5, establishing the working directory within the container as /app. Dependencies listed in requirements.txt are then installed using pip, ensuring the necessary packages are available. The FastAPI application code is copied into the container's working directory. Port 8000 is exposed to allow external access to the FastAPI application. Finally, the Dockerfile specifies the command to run the application, launching it with Uvicorn and binding to host 0.0.0.0 and port 8000. This Dockerfile encapsulates all the steps needed to build a Docker image capable of running the FastAPI application within a container, providing a consistent and reproducible environment for deployment.

## Docker-compose
This Docker Compose file [docker-compose.yml](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR/blob/main/docker-compose.yml) defines a multi-container application with two services: [rtr-api](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR/blob/main/IBI-RTR_api.py) and mongodb. Here's what each section does:
1. rtr-api Service:
Builds the Docker image for the rtr-api service using the Dockerfile in the current directory. We map port 8000 on the host to port 8000 in the container, allowing access to the FastAPI application running inside the container. We mount the current directory (where the Docker Compose file is located) to the /app directory inside the container, allowing live code reloading during development. This service depends on mongodb, meaning that the mongodb service needs to be up and running first. Finally, we connect the rtr-api service to the rtr-network network.
2. mongodb service:
We specify the Docker image to use for the mongodb service. We also set the container name to "mongodb" and configure the container to restart if it terminates unexpectedly. We  map default port 27017 on the host to port 27017 in the container, allowing access to the MongoDB server. The environment variables for configuring MongoDB are the root username and password for the MongoDB instance. We define volumes for persisting MongoDB data, initializing the database with [mongo-init.js](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR/blob/main/mongo-init.js), and providing a custom MongoDB configuration file [mongod.conf](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR/blob/main/mongod.conf). Finally, we also connect 'mongodb' to the rtr-network.
 - [mongo-init.js](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR/blob/main/mongo-init.js) creates two collections, each with a predefined structure enforced by JSON schemas for validation. The "mitigation_actions" collection specifies requirements for documents representing mitigation actions, including fields like intent type, threat, and duration. Similarly, the "users" collection defines constraints for user documents, mandating fields such as username, email, and password, with email validation using a regular expression. These schemas ensure data consistency and integrity by validating documents against specified criteria upon insertion or update, enhancing the reliability and usability of the MongoDB database.
 - [mongod.conf](https://github.com/Eight-Bells-Ltd/Reliability-Trust-Resilience-RTR/blob/main/mongod.conf) specifies the settings for running a MongoDB instance. In the storage section, the dbPath parameter indicates the directory where MongoDB will store its database files, set here to /data/db. The network settings define that MongoDB will bind to all available network interfaces (0.0.0.0) and listen on port 27017. Additionally, the security section enables access control and user authentication by setting authorization to enabled. This ensures that clients must authenticate themselves before accessing the database, enhancing the security of the MongoDB instance. Overall, this configuration file establishes a MongoDB environment with specified storage, network, and security settings.
  


## The main App

The application's functionality are fostered by fastAPI. The fastAPI implements 7 functionalities:
- root (GET): A welcome page.
- user register (POST): A registration interface for new users.
- user login (POST): A log-in interface for existing users. (OAuth 2.0)
- post an action (POST): Sends a new action to the RTR. (OAuth 2.0)
- get actions (GET): Requests all of the available actions currently stored inside the API. (OAuth 2.0)
- get specific action (GET): Requests a specific action based on the action's unique ID. (OAuth 2.0)
- delete action (POST): Deletes a specific action based on the action's unique ID. (OAuth 2.0)

All of the above are protected with OAuth 2.0 authentication.


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
The RTR was developed for the purposes of HORSE and it should receive input from IBI(Intent Based Interface). The partners from TUBS will provide us with JSONs describing mitigation action's in certain parts of the network topology. This is an example of such an action:

{
    "command": "add" or "delete", 
    "intent_type": "mitigation" or "prevention",
    "threat": "ddos", "dos" or "api_vul",
    "attacked_host": "120.2.191.7",
    "mitigation_host": "194.159.13.181",
    "action": "Reduce the number of request to the dns server to a 45/s for port 55, protocol udp",
    "duration": 4000,
    "intent_id": "ABC123"
}

We check inside the App if the JSON they provide us with meets the criteria of the schema above. Another check is done intrenally inside the database to confirm the validity of the JSON. This 2nd check is performed by the validation schema of the db.
After an action is stored inside the db, we provide the sender with ID the db assigned to the new object.

# Get actions
We expose 2 get interfaces:
- The 1st interface returns every action currently residing inside our database
- The 2nd interface retuerns a secific action based on the unique ID of this action.
- Maybe we will enhance that by gettig actions from a specific time frame.

# Delete actions
We have also exposed a delete interface. IBI will be able to request the deletion of deprecated and old mitigation actions. The deletion is done again based on the ID we have sent to the IBI when the mtigation action was stored inside our db. We may not include this interface evebtually because of the command field inside the JSON. This 'command' will instruct us to either add an action or delete an existing on or maybe even update. TBD