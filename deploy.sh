#!/bin/bash

# Function to display usage
show_usage() {
  echo "Usage: $0 --deployment_domain <DOMAIN> [OPTIONS]"
  echo ""
  echo "Required arguments:"
  echo "  --deployment_domain <DOMAIN>    Deployment domain: CNIT, UPC, or UMU"
  echo ""
  echo "Optional arguments:"
  echo "  --port <PORT>                   Custom port number (default: 8000 for CNIT/UPC, 8003 for UMU)"
  echo "  --epem <URL>                    EPEM endpoint URL (e.g., http://192.168.130.233:5002)"
  echo "  --doc <URL>                     DOC endpoint URL (e.g., http://192.168.130.62:8001)"
  echo "  -h, --help                      Show this help message"
  echo ""
  echo "Examples:"
  echo "  $0 --deployment_domain CNIT"
  echo "  $0 --deployment_domain UMU --port 8080"
  echo "  $0 --deployment_domain UPC --epem http://10.19.2.20:5002 --doc http://10.19.2.19:8001"
  echo "  $0 --deployment_domain CNIT --port 8000 --epem http://10.0.0.1:5002 --doc http://10.0.0.2:8001"
  exit 1
}

# Initialize variables
TESTBED=""
PORT=""
EPEM_ENDPOINT=""
DOC_ENDPOINT=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --deployment_domain)
      TESTBED=$(echo "$2" | tr '[:lower:]' '[:upper:]')
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --epem)
      EPEM_ENDPOINT="$2"
      shift 2
      ;;
    --doc)
      DOC_ENDPOINT="$2"
      shift 2
      ;;
    -h|--help)
      show_usage
      ;;
    *)
      echo "❌ Error: Unknown option $1"
      show_usage
      ;;
  esac
done

# Check if deployment_domain is provided
if [ -z "$TESTBED" ]; then
  echo "❌ Error: --deployment_domain is required"
  show_usage
fi

# Validate testbed argument
if [ "$TESTBED" != "CNIT" ] && [ "$TESTBED" != "UPC" ] && [ "$TESTBED" != "UMU" ]; then
  echo "❌ Error: Invalid deployment domain '$TESTBED'"
  echo "Valid options: CNIT, UPC, UMU"
  exit 1
fi

echo "🚀 Deploying RTR API for testbed: $TESTBED"

# Set PORT based on testbed if not provided
if [ -z "$PORT" ]; then
  # Default port based on testbed
  if [ "$TESTBED" = "UMU" ]; then
    PORT=8003
  else
    PORT=8000
  fi
  echo "📝 Using default port for $TESTBED: $PORT"
else
  echo "📝 Using custom port: $PORT"
fi

# Handle EPEM endpoint
if [ -n "$EPEM_ENDPOINT" ]; then
  echo "📝 Setting custom EPEM endpoint: $EPEM_ENDPOINT"
else
  echo "📝 Using default EPEM endpoint from .env"
fi

# Handle DOC endpoint
if [ -n "$DOC_ENDPOINT" ]; then
  echo "📝 Setting custom DOC endpoint: $DOC_ENDPOINT"
else
  echo "📝 Using default DOC endpoint from .env"
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

# Detect the real IP address of the machine
echo "🔍 Detecting RTR host IP address..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  RTR_HOST=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
  # Windows Git Bash
  RTR_HOST=$(ipconfig | grep -A 5 "Ethernet adapter" | grep "IPv4" | head -n 1 | sed 's/.*: //' | tr -d '\r' || echo "localhost")
else
  # Linux
  RTR_HOST=$(hostname -I | awk '{print $1}' || echo "localhost")
fi

# Fallback to localhost if no IP detected
if [ -z "$RTR_HOST" ] || [ "$RTR_HOST" = " " ]; then
  RTR_HOST="localhost"
  echo "⚠️  Could not detect IP address, using localhost"
else
  echo "✅ Detected RTR_HOST: $RTR_HOST"
fi

# Set RTR_PORT to the same as PORT
RTR_PORT=$PORT

# Update RTR_HOST in .env file
if [ -f .env ]; then
  if grep -q "^RTR_HOST = " .env; then
    # RTR_HOST variable exists, update it
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/^RTR_HOST = .*$/RTR_HOST = \"$RTR_HOST\"/" .env
    else
      sed -i "s/^RTR_HOST = .*$/RTR_HOST = \"$RTR_HOST\"/" .env
    fi
  else
    # RTR_HOST variable doesn't exist, add it after PORT
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "/^PORT = /a\\
RTR_HOST = \"$RTR_HOST\"" .env
    else
      sed -i "/^PORT = /a RTR_HOST = \"$RTR_HOST\"" .env
    fi
  fi
fi

# Update RTR_PORT in .env file
if [ -f .env ]; then
  if grep -q "^RTR_PORT = " .env; then
    # RTR_PORT variable exists, update it
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s/^RTR_PORT = .*$/RTR_PORT = \"$RTR_PORT\"/" .env
    else
      sed -i "s/^RTR_PORT = .*$/RTR_PORT = \"$RTR_PORT\"/" .env
    fi
  else
    # RTR_PORT variable doesn't exist, add it after RTR_HOST
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "/^RTR_HOST = /a\\
RTR_PORT = \"$RTR_PORT\"" .env
    else
      sed -i "/^RTR_HOST = /a RTR_PORT = \"$RTR_PORT\"" .env
    fi
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

# Update EPEM endpoint if provided
if [ -n "$EPEM_ENDPOINT" ] && [ -f .env ]; then
  echo "📝 Updating EPEM_$TESTBED endpoint in .env file..."
  if grep -q "^EPEM_$TESTBED = " .env; then
    # EPEM variable exists, update it
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s|^EPEM_$TESTBED = .*$|EPEM_$TESTBED = \"$EPEM_ENDPOINT\"|" .env
    else
      sed -i "s|^EPEM_$TESTBED = .*$|EPEM_$TESTBED = \"$EPEM_ENDPOINT\"|" .env
    fi
    echo "✅ EPEM_$TESTBED set to: $EPEM_ENDPOINT"
  else
    echo "⚠️  Warning: EPEM_$TESTBED not found in .env file"
  fi
fi

# Update DOC endpoint if provided
if [ -n "$DOC_ENDPOINT" ] && [ -f .env ]; then
  echo "📝 Updating DOC_$TESTBED endpoint in .env file..."
  if grep -q "^DOC_$TESTBED = " .env; then
    # DOC variable exists, update it
    if [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i '' "s|^DOC_$TESTBED = .*$|DOC_$TESTBED = \"$DOC_ENDPOINT\"|" .env
    else
      sed -i "s|^DOC_$TESTBED = .*$|DOC_$TESTBED = \"$DOC_ENDPOINT\"|" .env
    fi
    echo "✅ DOC_$TESTBED set to: $DOC_ENDPOINT"
  else
    echo "⚠️  Warning: DOC_$TESTBED not found in .env file"
  fi
fi

# Display configuration
echo ""
echo "📋 Deployment Configuration:"
echo "  - Testbed: $TESTBED"
echo "  - Port: $PORT"
echo "  - RTR Host: $RTR_HOST"
echo "  - RTR Port: $RTR_PORT"
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
echo "� Callback URL: http://$RTR_HOST:$RTR_PORT/update_action_status"
echo "�📊 Check status with: docker compose ps"
echo "📜 View logs with: docker compose logs -f rtr-api"