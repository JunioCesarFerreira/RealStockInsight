# Docker Infrastructure

In this directory we have the following files:

`docker-compose.yaml`: Script for composing the Docker infrastructure to be provided in the VM.

`load.sh`: Automation script to create Docker images in the VM.

### Prerequisites
- Docker and Docker Compose

### How to use

Run the `load.sh` script to generate the Docker images.

Then run `docker-compose up -d` to create the containers and the Docker network.

To remove the containers use `docker-compose down`.