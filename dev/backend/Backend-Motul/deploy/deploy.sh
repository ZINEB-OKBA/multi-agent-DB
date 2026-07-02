#!/bin/bash
echo "================================================================================"
echo "============================ Deploy Application ==========================="
echo "================================================================================"
echo "1- Stop container..."
docker stop capital-trust-app

echo "2- Remove container..."
docker rm --force capital-trust-app

echo "3- Remove image..."
docker image rm capital-trust-app

echo "4- Build image..."
docker build -t capital-trust-app .

echo "5- start container app..."
docker run  --name capital-trust-app --network airflow_network -d -v /opt/deploy/capital-trust/resources:/opt/deploy/capital-trust/resources -p 8081:8081 capital-trust-app