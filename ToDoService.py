import grpc
from todo_pb2 import (
    AddTaskRequest,
    AddTaskResponse,
    GetTaskRequest,
    GetTaskResponse,
    ListTasksResponse,
    Empty,
)
from todo_pb2_grpc import TodoServiceStub


def get_channel(connect):
    """
    Создает gRPC-канал и возвращает клиентский интерфейс (стаб).
    :param connect: Строка подключения (например, 'localhost:50051').
    :return: Экземпляр TodoServiceStub.
    """
    channel = grpc.insecure_channel(connect)
    sb = TodoServiceStub(channel)
    return sb


class ITodoService:
    def __init__(self, connection):
        """
        Инициализирует обертку для работы с gRPC-сервисом.
        :param connection: Строка подключения (например, 'localhost:50051').
        """
        self.connection = connection
        self.sb = get_channel(connection)

    def add_task(self, description):
        """
        Добавляет задачу.
        :param description: Описание задачи.
        :return: ID созданной задачи.
        """
        request = AddTaskRequest(description=description)
        response = self.sb.AddTask(request)
        return response.id

    def get_task(self, task_id):
        """
        Получает задачу по ID.
        :param task_id: ID задачи.
        :return: Словарь с ID и описанием задачи.
        """
        request = GetTaskRequest(id=task_id)
        try:
            response = self.sb.GetTask(request)
            return {"id": response.id, "description": response.description}
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                print(f"Task with ID {task_id} not found.")
            raise

    def list_tasks(self):
        """
        Возвращает список всех задач.
        :return: Список словарей с ID и описанием задач.
        """
        request = Empty()
        response = self.sb.ListTasks(request)
        return [{"id": task.id, "description": task.description} for task in response.tasks]
