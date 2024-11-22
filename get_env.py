import os

CONFIG = {
    "DOCKER_IMAGE": os.getenv("DOCKER_IMAGE", "grpc-service:latest"),
    "DOCKER_CONTAINER_NAME": os.getenv("DOCKER_CONTAINER_NAME", "grpc-service-container"),
    "DOCKER_PORT": int(os.getenv("DOCKER_PORT", 50051)),
    "DOCKER_HOST": os.getenv("DOCKER_HOST", "localhost"),
    "GRPC_TIMEOUT": int(os.getenv("GRPC_TIMEOUT", 5)),
}