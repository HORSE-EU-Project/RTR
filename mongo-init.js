// Create the "mitigation_actions" collection with updated schema validation
db.createCollection("mitigation_actions", {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: [
        'intent_type',
        'threat',
        'attacked_host',
        'mitigation_host',
        'action',
        'duration',
        'intent_id',  // Ensure intent_id is required
        'command',
        'status',
        'info'
      ],
      properties: {
        intent_type: {
          bsonType: 'string',
          enum: ['mitigation', 'prevention'],
          description: 'Must be either mitigation or prevention'
        },
        threat: {
          bsonType: 'string',
          enum: ['ddos', 'dos', 'api_vul'],
          description: 'Must be either ddos, dos, or api_vul'
        },
        attacked_host: {
          bsonType: 'string',
          description: 'The IP address of the attacked host as a string'
        },
        mitigation_host: {
          bsonType: 'string',
          description: 'The IP address of the mitigation host as a string'
        },
        action: {
          bsonType: 'string',
          description: 'High-level description of the mitigation action'
        },
        duration: {
          bsonType: 'int',
          description: 'Duration in seconds'
        },
        intent_id: {
          bsonType: 'string',
          description: 'The unique identifier for this action',
        },
        command: {
          bsonType: 'string',
          enum: ['add', 'delete'],
          description: 'Command specifying if the action is to be added or deleted'
        },
        status: {
          bsonType: 'string',
          enum: ['pending', 'completed', 'error'],
          description: 'Current status of the action'
        },
        info: {
          bsonType: 'string',
          description: 'Additional information or status message for the action'
        }
      }
    }
  }
});

// Add a unique index on "intent_id" to avoid duplicate intent_ids
db.mitigation_actions.createIndex({ "intent_id": 1 }, { unique: true });


// Create the "users" collection with updated schema validation
db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["username", "email", "password"],
      properties: {
        username: {
          bsonType: "string",
          description: "Must be a string and is required"
        },
        email: {
          bsonType: "string",
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
          description: "Must be a valid email address and is required"
        },
        password: {
          bsonType: "string",
          description: "Must be a valid password and is required"
        }
      }
    }
  }
});
