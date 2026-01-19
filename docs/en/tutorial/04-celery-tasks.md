# Step 4: Celery Tasks

In this step, we will create a background task that automatically cleans up completed todos. This demonstrates how to integrate Celery tasks with the service layer and IoC container.

## What You Will Build

- A `TodoCleanupTaskController` that removes completed todos older than 7 days
- A typed task registry entry for type-safe task invocation
- A scheduled task that runs daily at 3 AM

## Files Overview

| Action | File Path |
|--------|-----------|
| Create | `src/delivery/tasks/tasks/todo_cleanup.py` |
| Modify | `src/delivery/tasks/registry.py` |
| Modify | `src/ioc/registries/delivery.py` |
| Modify | `src/delivery/tasks/factories.py` |

---

## Step 4.1: Add the Task Name

First, add a new task name to the `TaskName` enum. This provides a centralized registry of all task names and prevents typos.

```python title="src/delivery/tasks/registry.py" hl_lines="10 15 23-25"
from enum import StrEnum
from typing import TYPE_CHECKING

from celery import Task

from infrastructure.celery.registry import BaseTasksRegistry

if TYPE_CHECKING:
    from delivery.tasks.tasks.ping import PingResult
    from delivery.tasks.tasks.todo_cleanup import TodoCleanupResult


class TaskName(StrEnum):
    PING = "ping"
    TODO_CLEANUP = "todo.cleanup"


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], PingResult]:
        return self._get_task_by_name(TaskName.PING)

    @property
    def todo_cleanup(self) -> Task[[], TodoCleanupResult]:
        return self._get_task_by_name(TaskName.TODO_CLEANUP)
```

!!! info "Type-Safe Task Registry"
    The `TasksRegistry` provides typed properties for each task. This enables IDE autocompletion and type checking when calling tasks, preventing runtime errors from typos in task names.

---

## Step 4.2: Create the Task Controller

Create the task controller that implements the cleanup logic. Notice how the controller receives `TodoService` through dependency injection.

```python title="src/delivery/tasks/tasks/todo_cleanup.py"
from typing import TypedDict

from celery import Celery

from core.todo.services import TodoService
from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class TodoCleanupResult(TypedDict):
    deleted_count: int


class TodoCleanupTaskController(Controller):
    def __init__(self, todo_service: TodoService) -> None:
        self._todo_service = todo_service

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.TODO_CLEANUP)(self.cleanup)

    def cleanup(self) -> TodoCleanupResult:
        """Delete completed todos older than 7 days."""
        deleted_count = self._todo_service.delete_completed_todos_older_than(days=7)

        return TodoCleanupResult(deleted_count=deleted_count)
```

!!! warning "Service Layer Required"
    Controllers must **never** import models directly. The `TodoCleanupTaskController` uses `TodoService` to perform database operations, following the service layer architecture.

---

## Step 4.3: Using the Service Method

The `TodoService` already has the `delete_completed_todos_older_than` method we need (from Step 1). The task controller simply calls this existing method:

```python
# This method already exists in TodoService from Step 1
def delete_completed_todos_older_than(self, days: int) -> int:
    """Delete completed todos older than the specified number of days."""
    cutoff = timezone.now() - timezone.timedelta(days=days)
    deleted_count, _ = Todo.objects.filter(
        is_completed=True,
        completed_at__lt=cutoff,
    ).delete()
    return deleted_count
```

!!! tip "Service Layer Benefit"
    Because we defined this method in Step 1, we can reuse it here. The service layer provides a clean interface that both HTTP controllers and Celery tasks can use.

---

## Step 4.4: Register the Controller in IoC

Register the new controller in the IoC container so it can be resolved with its dependencies.

```python title="src/ioc/registries/delivery.py" hl_lines="8 41"
from punq import Container, Scope

from delivery.http.factories import AdminSiteFactory, FastAPIFactory, URLPatternsFactory
from delivery.http.controllers.health.controllers import HealthController
from delivery.http.controllers.user.controllers import UserController, UserTokenController
from delivery.tasks.factories import CeleryAppFactory, TasksRegistryFactory
from delivery.tasks.settings import CelerySettings
from delivery.tasks.tasks.ping import PingTaskController
from delivery.tasks.tasks.todo_cleanup import TodoCleanupTaskController


def register_delivery(container: Container) -> None:
    _register_http(container)
    _register_http_controllers(container)

    _register_celery(container)
    _register_celery_controllers(container)


def _register_http(container: Container) -> None:
    container.register(FastAPIFactory, scope=Scope.singleton)
    container.register(AdminSiteFactory, scope=Scope.singleton)
    container.register(URLPatternsFactory, scope=Scope.singleton)


def _register_http_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)


def _register_celery(container: Container) -> None:
    container.register(CelerySettings, factory=lambda: CelerySettings(), scope=Scope.singleton)
    container.register(CeleryAppFactory, scope=Scope.singleton)
    container.register(TasksRegistryFactory, scope=Scope.singleton)


def _register_celery_controllers(container: Container) -> None:
    container.register(PingTaskController, scope=Scope.singleton)
    container.register(TodoCleanupTaskController, scope=Scope.singleton)
```

!!! note "Automatic Dependency Resolution"
    The IoC container automatically resolves `TodoService` when creating `TodoCleanupTaskController` because `TodoService` was registered in `src/ioc/registries/core.py` (Step 2).

---

## Step 4.5: Update the Tasks Registry Factory

Inject the new controller into `TasksRegistryFactory` and register it with Celery.

```python title="src/delivery/tasks/factories.py" hl_lines="8 10 58 65-66 74"
from celery import Celery
from celery.schedules import crontab

from configs import RedisSettings
from configs.django import application_settings
from delivery.tasks.registry import TaskName, TasksRegistry
from delivery.tasks.settings import CelerySettings
from delivery.tasks.tasks.ping import PingTaskController
from delivery.tasks.tasks.todo_cleanup import TodoCleanupTaskController


class CeleryAppFactory:
    def __init__(
            self,
            settings: CelerySettings,
            redis_settings: RedisSettings,
    ) -> None:
        self._instance: Celery | None = None
        self._settings = settings
        self._redis_settings = redis_settings

    def __call__(self) -> Celery:
        if self._instance is not None:
            return self._instance

        celery_app = Celery(
            "main",
            broker=self._redis_settings.redis_url.get_secret_value(),
            backend=self._redis_settings.redis_url.get_secret_value(),
        )

        self._configure_app(celery_app=celery_app)
        self._configure_beat_schedule(celery_app=celery_app)

        self._instance = celery_app
        return self._instance

    def _configure_app(self, celery_app: Celery) -> None:
        celery_app.conf.update(
            timezone=application_settings.time_zone,
            enable_utc=True,
            **self._settings.model_dump(),
        )

    def _configure_beat_schedule(self, celery_app: Celery) -> None:
        celery_app.conf.beat_schedule = {
            "ping-every-minute": {
                "task": TaskName.PING,
                "schedule": 60.0,
            },
            "todo-cleanup-daily": {
                "task": TaskName.TODO_CLEANUP,
                "schedule": crontab(hour=3, minute=0),
            },
        }


class TasksRegistryFactory:
    def __init__(
            self,
            celery_app_factory: CeleryAppFactory,
            ping_controller: PingTaskController,
            todo_cleanup_controller: TodoCleanupTaskController,
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app_factory = celery_app_factory
        self._ping_controller = ping_controller
        self._todo_cleanup_controller = todo_cleanup_controller

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        celery_app = self._celery_app_factory()
        registry = TasksRegistry(app=celery_app)
        self._ping_controller.register(celery_app)
        self._todo_cleanup_controller.register(celery_app)

        self._instance = registry
        return self._instance
```

---

## Understanding Celery Beat Schedule

The `crontab(hour=3, minute=0)` schedule runs the task daily at 3:00 AM (server timezone).

| Schedule Expression | Meaning |
|---------------------|---------|
| `crontab()` | Every minute |
| `crontab(minute=0)` | Every hour |
| `crontab(hour=3, minute=0)` | Daily at 3:00 AM |
| `crontab(hour=3, minute=0, day_of_week=1)` | Every Monday at 3:00 AM |
| `60.0` | Every 60 seconds |

!!! tip "Running Celery Beat"
    To run the scheduler, use:
    ```bash
    celery -A delivery.tasks.app beat --loglevel=info
    ```
    Or with the worker:
    ```bash
    celery -A delivery.tasks.app worker --beat --loglevel=info
    ```

---

## Invoking Tasks Manually

You can invoke the cleanup task manually using the typed registry:

```python
from ioc.container import get_container
from delivery.tasks.registry import TasksRegistry

container = get_container()
registry = container.resolve(TasksRegistry)

# Async invocation (returns immediately)
result = registry.todo_cleanup.delay()
print(f"Task ID: {result.id}")

# Sync invocation (blocks until complete)
result = registry.todo_cleanup.apply().get()
print(f"Deleted {result['deleted_count']} todos")
```

---

## Summary

You have learned how to:

- Create a Celery task controller that follows the service layer pattern
- Add typed properties to the task registry for type-safe invocation
- Register task controllers in the IoC container
- Configure scheduled tasks with Celery Beat

---

## Next Steps

Continue to [Step 5: Observability](05-observability.md) to add tracing and monitoring.

---

!!! abstract "See Also"
    - [Controller Pattern](../concepts/controller-pattern.md) - Deep dive into the controller architecture
    - [Add Celery Task](../how-to/add-celery-task.md) - Quick reference for adding new tasks
