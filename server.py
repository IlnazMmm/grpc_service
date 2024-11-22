import grpc
from concurrent import futures
import uuid
import todo_pb2
import todo_pb2_grpc

# Реализация сервиса ToDo
class TodoService(todo_pb2_grpc.TodoServiceServicer):
    def __init__(self):
        self.tasks = {}

    def AddTask(self, request, context):
        task_id = str(uuid.uuid4())  # Генерация уникального ID
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


# Функция для запуска gRPC сервера
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    todo_pb2_grpc.add_TodoServiceServicer_to_server(TodoService(), server)
    server.add_insecure_port('[::]:50051')  # Привязка к порту 50051
    server.start()
    yield server
    print("Server started on port 50051...")
    server.stop()


if __name__ == "__main__":
    serve()
