#!/bin/bash

# Get the host IP address
export HOST_IP=$(hostname -I | awk '{print $1}')
echo $HOST_IP
# Run Docker Compose
docker compose down && docker compose up -d