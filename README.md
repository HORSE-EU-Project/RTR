# Reliable Trust Resilience

RTR is a software tool developed for the HORSE project. The purpose of the RTR is to accept a mitigation action for an attack targeting a network topology. This mitigation action is basically a JSON containing information both on the attack and the mitigation action that counters it. The RTR then extracts the useful information from this file and configures an Ansible Playbook. This Playbook is then sent to an enforcer, who uses it to configure parts of the network.

## Installation

Since this is a prototype you can download the repository and run the following command:
- pip install -r requirements.txt
- uvicorn IBI-RTR_api:rtr_api


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