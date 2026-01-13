// Create the "mitigation_actions" collection
db.createCollection("mitigation_actions");

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
