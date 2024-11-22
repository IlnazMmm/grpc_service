import os
import time
import uuid
from concurrent import futures

import docker
import grpc
import pytest

import todo_pb2
from ToDoService import ITodoService
from docker_function import pull_image, DOCKER
from get_env import CONFIG

from todo_pb2_grpc import (
    TodoServiceServicer,
    TodoServiceStub,
    add_TodoServiceServicer_to_server,
    TodoService
)

# Загрузка переменных из .env
# load_dotenv()

# Инициализация конфигурации из .env в виде словаря

@pytest.fixture(scope="module")
def grpc_docker_service():

    pull_image(CONFIG["DOCKER_IMAGE"])

    container = DOCKER.containers.run(
        image=CONFIG["DOCKER_IMAGE"],
        name=CONFIG["DOCKER_CONTAINER_NAME"],
        ports={f"{CONFIG['DOCKER_PORT']}/tcp": CONFIG["DOCKER_PORT"]},
        detach=True,
    )

    time.sleep(2)  # Ожидание, пока контейнер полностью запустится
    yield container

    # try:
    #     container = DOCKER.containers.get(CONFIG["DOCKER_IMAGE"])
    #     if container.status == 'running':
    #         print(f"Stopping container: {CONFIG["DOCKER_IMAGE"]}")
    #         container.stop()
    #     print(f"Removing container: {CONFIG["DOCKER_IMAGE"]}")
    #     container.remove()
    # except docker.errors.NotFound:
    #     print(f"Container {CONFIG["DOCKER_IMAGE"]} not found.")


class TestData:
    def __init__(self, task, description):
        self.task = task
        self.description = description


data = TestData(str(uuid.uuid4()), "Desc")
# # Реализация мок-сервиса
class MockTodoService(TodoServiceServicer):

    def __init__(self):
        self.tasks = {}

    def AddTask(self, request, context):
        task_id = data.task  # Генерация уникального ID
        self.tasks[task_id] = request.description
        return todo_pb2.AddTaskResponse(id=task_id)

    def GetTask(self, request, context):
        description = self.tasks.get(request.id)
        if not description:
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        return todo_pb2.GetTaskResponse(id=request.id, description=description)

    def ListTasks(self, request, context):
        tasks = [
            todo_pb2.GetTaskResponse(id=task_id, description=desc)
            for task_id, desc in self.tasks.items()
        ]
        return todo_pb2.ListTasksResponse(tasks=tasks)

    # def AddTask(self, request, context):
    #     return AddTaskResponse(id="mock-task-id")
    #
    # def GetTask(self, request, context):
    #     if request.id == "mock-task-id":
    #         return GetTaskResponse(id="mock-task-id", description="Mock task description")
    #     context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
    #
    # def ListTasks(self, request, context):
    #     return ListTasksResponse(
    #         tasks=[
    #             GetTaskResponse(id="mock-task-id", description="Mock task description")
    #         ]
    #     )


# Фикстура для запуска мок-сервера
@pytest.fixture(scope="module")
def grpc_mock_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    add_TodoServiceServicer_to_server(MockTodoService(), server)
    port = 50052  # Используем тестовый порт
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    yield f"localhost:{port}"
    server.stop(0)


# Тесты с моками
@pytest.fixture(scope="module")
def grpc_client(grpc_docker_service):
    """Фикстура для создания клиента TodoService."""
    connection = f"{CONFIG['DOCKER_HOST']}:{CONFIG['DOCKER_PORT']}"
    client = ITodoService(connection)
    time.sleep(5)  # Даем время контейнеру для инициализации
    return client


def test_add_task(grpc_docker_service, grpc_client):
    """Тестирует добавление задачи через сервис в Docker."""
    task_id = grpc_client.add_task("Test task description")
    assert task_id is not None
    assert len(task_id) > 0


def test_get_task(grpc_docker_service, grpc_client):
    """Тестирует получение задачи по ID."""
    # Сначала добавляем задачу
    task_id = grpc_client.add_task("Test task description")
    task = grpc_client.get_task(task_id)

    assert task["id"] == task_id
    assert task["description"] == "Test task description"


def test_get_task_not_found(grpc_docker_service, grpc_client):
    """Тестирует обработку ситуации, когда задача не найдена."""
    with pytest.raises(Exception, match="Task not found"):
        grpc_client.get_task("non-existent-id")


def test_list_tasks(grpc_docker_service, grpc_client):
    """Тестирует получение списка задач."""
    # Сначала добавляем задачи
    grpc_client.add_task("Task 1")
    grpc_client.add_task("Task 2")

    tasks = grpc_client.list_tasks()

    assert len(tasks) >= 2  # Учитываем, что могли быть старые задачи
    descriptions = [task["description"] for task in tasks]
    assert "Task 1" in descriptions
    assert "Task 2" in descriptions


# Параметризованный тест
# @pytest.mark.parametrize(
#     "task_id, expected_description",
#     [
#         (data.task, data.description),  # Существующая задача
#         ("non-existent-id", None),                # Несуществующая задача
#     ]
# )
# def test_param_get_task(grpc_client, task_id, expected_description):
#     if expected_description:
#         response = grpc_client.GetTask(GetTaskRequest(id=task_id))
#         assert response.description == expected_description
#     else:
#         with pytest.raises(grpc.RpcError) as excinfo:
#             grpc_client.GetTask(GetTaskRequest(id=task_id))
#         assert excinfo.value.code() == grpc.StatusCode.NOT_FOUND
