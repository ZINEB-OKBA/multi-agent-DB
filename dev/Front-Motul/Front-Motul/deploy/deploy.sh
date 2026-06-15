#!/bin/bash

echo "---------------------------------------"
echo "Deploying CT_chatbot"
echo "---------------------------------------"

echo "Stopping container if running..."
docker stop CT_chatbot || true

echo "Removing old container if exists..."
docker rm CT_chatbot || true

echo "Building Docker image: ct_chatbot ..."
docker build --no-cache -t ct_chatbot .

echo "Starting new container..."
docker run -d \
  --name CT_chatbot \
  --network airflow_network \
  -p 80:80 \
  ct_chatbot

echo "---------------------------------------"
echo "Deployment finished!"
echo "App running on: http://localhost:80"
echo "Container name: CT_chatbot"
echo "---------------------------------------"
