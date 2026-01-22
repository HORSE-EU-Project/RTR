#!/bin/bash

# Define environment variables
if [ -z "$1" ]; then
  echo "Usage: $0 <TESTBED>"
  echo "  TESTBED: CNIT, UPC, or UMU"
  echo ""
  echo "Example: $0 CNIT"
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
echo "📊 Check status with: docker compose ps"
echo "📜 View logs with: docker compose logs -f rtr-api"