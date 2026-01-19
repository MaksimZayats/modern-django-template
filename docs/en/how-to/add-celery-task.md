# Add a Celery Task

This guide provides a quick reference for adding a new Celery background task to your application.

## Quick Reference

Adding a Celery task requires these steps:

1. Add `TaskName` enum value
2. Create `TypedDict` for result
3. Create `TaskController` class
4. Add typed property to `TasksRegistry`
5. Register controller in IoC
6. Update `TasksRegistryFactory`
7. (Optional) Add to beat schedule

## Step-by-Step Guide

### Step 1: Add TaskName Enum Value

Edit `src/delivery/tasks/registry.py`:

```python
from enum import StrEnum


class TaskName(StrEnum):
    PING = "ping"
    SEND_EMAIL = "send_email"  # Add your new task name
```

### Step 2: Create TypedDict for Result

Create a new file `src/delivery/tasks/tasks/send_email.py`:

```python
from typing import Literal, TypedDict

from celery import Celery

from core.notifications.services import NotificationService
from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class SendEmailResult(TypedDict):
    status: Literal["sent", "failed"]
    recipient: str


class SendEmailTaskController(Controller):
    def __init__(
        self,
        notification_service: NotificationService,
    ) -> None:
        self._notification_service = notification_service

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.SEND_EMAIL)(self.send_email)

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> SendEmailResult:
        try:
            self._notification_service.send_email(
                recipient=recipient,
                subject=subject,
                body=body,
            )
            return SendEmailResult(status="sent", recipient=recipient)
        except Exception:
            return SendEmailResult(status="failed", recipient=recipient)
```

!!! tip "TypedDict for Type Safety"
    Using `TypedDict` for task results enables type checking when calling `.get()` on task results.

### Step 3: Add Typed Property to TasksRegistry

Edit `src/delivery/tasks/registry.py`:

```python
from enum import StrEnum
from typing import TYPE_CHECKING

from celery import Task

from infrastructure.frameworks.celery import BaseTasksRegistry

if TYPE_CHECKING:
    from delivery.tasks.tasks.ping import PingResult
    from delivery.tasks.tasks.send_email import SendEmailResult


class TaskName(StrEnum):
    PING = "ping"
    SEND_EMAIL = "send_email"


class TasksRegistry(BaseTasksRegistry):
    @property
    def ping(self) -> Task[[], PingResult]:
        return self._get_task_by_name(TaskName.PING)

    @property
    def send_email(self) -> Task[[str, str, str], SendEmailResult]:
        return self._get_task_by_name(TaskName.SEND_EMAIL)
```

The type annotation `Task[[str, str, str], SendEmailResult]` specifies:

- `[str, str, str]` - the argument types (recipient, subject, body)
- `SendEmailResult` - the return type

### Step 4: Register Controller in IoC

Edit `src/ioc/registries/delivery.py`:

```python
from punq import Container, Scope

from delivery.tasks.tasks.send_email import SendEmailTaskController
# ... other imports ...


def _register_celery_controllers(container: Container) -> None:
    container.register(PingTaskController, scope=Scope.singleton)
    container.register(SendEmailTaskController, scope=Scope.singleton)  # Add this
```

### Step 5: Update TasksRegistryFactory

Edit `src/delivery/tasks/factories.py`:

```python
from delivery.tasks.tasks.send_email import SendEmailTaskController
# ... other imports ...


class TasksRegistryFactory:
    def __init__(
        self,
        celery_app_factory: CeleryAppFactory,
        ping_controller: PingTaskController,
        send_email_controller: SendEmailTaskController,  # Add parameter
    ) -> None:
        self._instance: TasksRegistry | None = None
        self._celery_app_factory = celery_app_factory
        self._ping_controller = ping_controller
        self._send_email_controller = send_email_controller  # Store reference

    def __call__(self) -> TasksRegistry:
        if self._instance is not None:
            return self._instance

        celery_app = self._celery_app_factory()
        registry = TasksRegistry(app=celery_app)

        self._ping_controller.register(celery_app)
        self._send_email_controller.register(celery_app)  # Register task

        self._instance = registry
        return self._instance
```

### Step 6: (Optional) Add to Beat Schedule

For periodic tasks, first import `crontab` at the top of `src/delivery/tasks/factories.py`:

```python
from celery.schedules import crontab
```

Then edit the `_configure_beat_schedule` method:

```python
def _configure_beat_schedule(self, celery_app: Celery) -> None:
    celery_app.conf.beat_schedule = {
        "ping-every-minute": {
            "task": TaskName.PING,
            "schedule": 60.0,
        },
        "send-daily-report": {
            "task": TaskName.SEND_EMAIL,
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
            "args": [
                "admin@example.com",
                "Daily Report",
                "Here is your daily report...",
            ],
        },
    }
```

## Calling the Task

### From Application Code

```python
from delivery.tasks.registry import TasksRegistry


class SomeService:
    def __init__(self, tasks_registry: TasksRegistry) -> None:
        self._tasks = tasks_registry

    def trigger_email(self, recipient: str) -> None:
        # Async execution
        self._tasks.send_email.delay(
            recipient,
            "Welcome!",
            "Thank you for signing up.",
        )
```

### From HTTP Controller

```python
from delivery.tasks.registry import TasksRegistry
from infrastructure.delivery.controllers import Controller


class NotificationController(Controller):
    def __init__(self, tasks_registry: TasksRegistry) -> None:
        self._tasks = tasks_registry

    def send_notification(
        self,
        request: AuthenticatedHttpRequest,
        body: SendNotificationRequest,
    ) -> dict:
        # Queue the task
        task = self._tasks.send_email.delay(
            body.recipient,
            body.subject,
            body.body,
        )
        return {"task_id": task.id, "status": "queued"}
```

## Testing Celery Tasks

```python
import pytest

from tests.integration.factories import (
    TestCeleryWorkerFactory,
    TestTasksRegistryFactory,
)


@pytest.mark.django_db(transaction=True)
def test_send_email_task(
    celery_worker_factory: TestCeleryWorkerFactory,
    tasks_registry_factory: TestTasksRegistryFactory,
) -> None:
    registry = tasks_registry_factory()

    with celery_worker_factory():
        result = registry.send_email.delay(
            "test@example.com",
            "Test Subject",
            "Test Body",
        ).get(timeout=5)

    assert result["status"] == "sent"
    assert result["recipient"] == "test@example.com"
```

## Summary Checklist

- [ ] Add task name to `TaskName` enum in `registry.py`
- [ ] Create `TypedDict` for result type
- [ ] Create `TaskController` class with `register()` method
- [ ] Add typed property to `TasksRegistry`
- [ ] Register controller in `ioc/registries/delivery.py`
- [ ] Update `TasksRegistryFactory` constructor and `__call__()` method
- [ ] (Optional) Add to beat schedule for periodic execution
- [ ] Write integration tests
