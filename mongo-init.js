
db.createCollection("mitigation_actions", {
        $jsonSchema: {
          bsonType: 'object',
          required: [
            'intent_type',
            'threat',
            'attacked_host',
            'mitigation_host',
            'action',
            'duration',
            'intent_id'
          ],
          properties: {
            intent_type: {
              'enum': [
                'mitigation',
                'prevention'
              ],
              description: 'must be either mitigation or prevention'
            },
            threat: {
              'enum': [
                'ddos',
                'dos',
                'api_vul'
              ],
              description: 'must be either ddos, dos or api_vul'
            },
            attacked_host: {
              bsonType: 'string',
              description: 'the ip must be passed as a string'
            },
            mitigation_host: {
              bsonType: 'string',
              description: 'the ip must be passed as a string'
            },
            action: {
              bsonType: 'string',
              description: 'Sentence describing the high level mitigation action'
            },
            duration: {
              bsonType: 'int',
              description: 'The duration is measured in seconds'
            },
            intent_id: {
              bsonType: 'string',
              description: 'The group of this action'
            }
          }
        }
      });
  
  db.createCollection("users", {
    validator: {
      $jsonSchema: {
        bsonType: "object",
        required: ["username", "email", "password"],
        properties: {
          username: {
            bsonType: "string",
            description: "must be a string and is required"
          },
          email: {
            bsonType: "string",
            pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
            description: "must be a valid email address and is required"
          },
          password: {
            bsonType: "string",
            description: "must be a valid email address and is required"
          }
        }
      }
    }
  });