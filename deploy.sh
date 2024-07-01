#!/bin/bash

# Define environment variables
if [ -z "$1" ] || [ -z "$2" ] ; then
  echo "Usage: $0 <EPEM_ENDPOINT> <EPEM_PORT> "
  exit 1
fi

#Use provided aguments
EPEM_ENDPOINT=$1
EPEM_PORT=$2
#DNS_SERVER=$3
#NTP_SERVER=$4

# Check if environment variables are set
echo "Using EPEM_ENDPOINT: $EPEM_ENDPOINT"
echo "Using EPEM_PORT: $EPEM_PORT"
#echo "Using DNS_SERVER: $DNS_SERVER"
#echo "Using NTP_SERVER: $NTP_SERVER"

# Make env variables available to docker compose
export EPEM_ENDPOINT
export EPEM_PORT
#export DNS_SERVER
#export NTP_SERVER

# Build docker images
echo "Building docker images"
docker compose build

#Run docker compose images
echo "Running docker compose"
docker compose up -d