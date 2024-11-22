from pathlib import Path

import docker

DOCKER = docker.DockerClient(base_url="npipe://\\.\pipe\docker_cli")

"""
Загружает Docker-образ, если он не существует или требуется обновление.
:param image: Имя образа (например, 'todo-service:latest').
:param force: Если True, принудительно перезагружает образ.
"""
def pull_image(image, force=False):
    images = DOCKER.images.list(name=image)
    if force or len(images) < 1:
        print(f"Pulling Docker image: {image}")
        DOCKER.images.pull(image)
        return


"""
Возвращает корневую папку проекта.
"""
def get_project_root() -> Path:
    return Path(__file__).parent.parent
