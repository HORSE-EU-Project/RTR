#!/bin/bash

# Define environment variables
if [ -z "$1" ]; then
  echo "Usage: $0 <TESTBED> [PORT]"
  echo "  TESTBED: CNIT, UPC, or UMU"
  echo "  PORT: Optional port number (default: 8000 for CNIT/UPC, 8003 for UMU)"
  echo ""
  echo "Examples:"
  echo "  $0 CNIT        # Uses port 8000"
  echo "  $0 UMU         # Uses port 8003"
  echo "  $0 CNIT 8080   # Uses custom port 8080"
  exit 1
fi

# Get testbed argument and convert to uppercase
TESTBED=$(echo "$1" | tr '[:lower:]' '[:upper:]')

# Validate testbed argument
if [ "$TESTBED" != "CNIT" ] && [ "$TESTBED" != "UPC" ] && [ "$TESTBED" != "UMU" ]; then
  echo "❌ Error: Invalid testbed '$1'"
  echo "Valid options: CNIT, UPC, UMU"
  exit 1
fi

echo "🚀 Deploying RTR API for testbed: $TESTBED"

# Set PORT based on testbed or use custom port from argument
if [ -n "$2" ]; then
  # Custom port provided as second argument
  PORT=$2
  echo "📝 Using custom port: $PORT"
else
  # Default port based on testbed
  if [ "$TESTBED" = "UMU" ]; then
    PORT=8003
  else
    PORT=8000
  fi
  echo "📝 Using default port for $TESTBED: $PORT"
fi

# Update PORT in .env file
if [ -f .env ]; then
  if grep -q "^PORT = " .env; then
    # PORT variable exists, update it
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/^PORT = .*$/PORT = \"$PORT\"/" .env
    else
      sed -i "s/^PORT = .*$/PORT = \"$PORT\"/" .env
    fi
  else
    # PORT variable doesn't exist, add it
    echo "" >> .env
    echo "# RTR API Port" >> .env
    echo "PORT = \"$PORT\"" >> .env
  fi
fi

# Update CURRENT_DOMAIN in .env file
if [ -f .env ]; then
  echo "📝 Updating CURRENT_DOMAIN in .env file..."
  # Use sed to replace the CURRENT_DOMAIN line
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^CURRENT_DOMAIN = .*$/CURRENT_DOMAIN = \"$TESTBED\"/" .env
  else
    # Linux
    sed -i "s/^CURRENT_DOMAIN = .*$/CURRENT_DOMAIN = \"$TESTBED\"/" .env
  fi
  echo "✅ CURRENT_DOMAIN set to: $TESTBED"
else
  echo "⚠️  Warning: .env file not found"
fi

# Display configuration
echo ""
echo "📋 Deployment Configuration:"
echo "  - Testbed: $TESTBED"
echo "  - Port: $PORT"
grep "CURRENT_DOMAIN" .env 2>/dev/null || echo "  - CURRENT_DOMAIN: Not found in .env"
grep "EPEM_$TESTBED" .env 2>/dev/null || echo "  - EPEM endpoint: Not configured"
grep "DOC_$TESTBED" .env 2>/dev/null || echo "  - DOC endpoint: Not configured"
echo ""

# Build docker images
echo "🔨 Building docker images..."
docker compose build

# Run docker compose images
echo "🐳 Starting docker containers..."
docker compose up -d

echo ""
echo "✨ Deployment complete!"
echo "🌐 RTR API accessible at: http://localhost:$PORT"
echo "📊 Check status with: docker compose ps"
echo "📜 View logs with: docker compose logs -f rtr-api"