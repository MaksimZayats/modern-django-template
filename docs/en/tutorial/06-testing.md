# Step 6: Testing

In this final step, you will write comprehensive tests for the Todo feature. The template provides test factories that enable isolated, type-safe testing with IoC override capabilities.

## What You Will Build

- A `TestTodoFactory` for creating test data
- HTTP API integration tests
- Celery task integration tests
- Examples of IoC override patterns for mocking

## Files Overview

| Action | File Path |
|--------|-----------|
| Modify | `tests/integration/factories.py` |
| Modify | `tests/integration/conftest.py` |
| Create | `tests/integration/http/test_v1_todos.py` |
| Create | `tests/integration/tasks/test_todo_cleanup_task.py` |

---

## Why Test Factories Matter

Test factories provide several benefits:

| Benefit | Description |
|---------|-------------|
| **Isolation** | Each test gets a fresh container and database state |
| **Defaults** | Sensible defaults reduce boilerplate in tests |
| **Type Safety** | IDE autocompletion and type checking for test data |
| **Flexibility** | Override any default value for specific test scenarios |
| **IoC Override** | Swap real services with mocks per-test |

---

## Step 6.1: Create the Test Todo Factory

Add a factory for creating test todos in `tests/integration/factories.py`.

```python title="tests/integration/factories.py" hl_lines="10 14 63-79"
from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any

from celery.contrib.testing import worker
from celery.worker import WorkController
from fastapi.testclient import TestClient

from core.todo.models import Todo
from core.todo.services import TodoService
from core.user.models import User
from delivery.http.factories import FastAPIFactory
from core.user.services.jwt import JWTService
from delivery.tasks.factories import CeleryAppFactory, TasksRegistryFactory
from delivery.tasks.registry import TasksRegistry
from infrastructure.punq.container import AutoRegisteringContainer


class BaseFactory(ABC):
    __test__ = False

    @abstractmethod
    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        pass


class ContainerBasedFactory(BaseFactory, ABC):
    def __init__(
            self,
            container: AutoRegisteringContainer,
    ) -> None:
        self._container = container


class TestClientFactory(ContainerBasedFactory):
    def __call__(
            self,
            auth_for_user: User | None = None,
            headers: dict[str, str] | None = None,
            **kwargs: Any,
    ) -> TestClient:
        api_factory = self._container.resolve(FastAPIFactory)
        jwt_service = self._container.resolve(JWTService)

        headers = headers or {}

        if auth_for_user is not None:
            token = jwt_service.issue_access_token(user_id=auth_for_user.pk)
            headers["Authorization"] = f"Bearer {token}"

        return TestClient(
            api_factory(),
            headers=headers,
            **kwargs,
        )


class TestUserFactory(ContainerBasedFactory):
    def __call__(
            self,
            username: str = "test_user",
            password: str = "password123",  # noqa: S107
            email: str = "user@test.com",
            *,
            is_staff: bool = False,
            **kwargs: Any,
    ) -> User:
        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=is_staff,
            **kwargs,
        )


class TestCeleryWorkerFactory(ContainerBasedFactory):
    def __call__(self) -> AbstractContextManager[WorkController]:
        celery_app_factory = self._container.resolve(CeleryAppFactory)

        return worker.start_worker(
            app=celery_app_factory(),
            perform_ping_check=False,
        )


class TestTasksRegistryFactory(ContainerBasedFactory):
    def __call__(self) -> TasksRegistry:
        factory = self._container.resolve(TasksRegistryFactory)
        return factory()


class TestTodoFactory(ContainerBasedFactory):
    """Factory for creating test Todo instances."""

    def __call__(
            self,
            user: User,
            title: str = "Test Todo",
            description: str = "Test description",
            is_completed: bool = False,
    ) -> Todo:
        todo_service = self._container.resolve(TodoService)

        todo = todo_service.create_todo(
            title=title,
            description=description,
            user_id=user.pk,
        )

        if is_completed:
            todo.is_completed = True
            todo.save()

        return todo
```

---

## Step 6.2: Register the Factory Fixture

Add the fixture to `tests/integration/conftest.py`.

```python title="tests/integration/conftest.py" hl_lines="3-4 14-16 41-46"
import pytest

from infrastructure.punq.container import AutoRegisteringContainer
from ioc.container import ContainerFactory
from tests.integration.factories import (
    TestCeleryWorkerFactory,
    TestClientFactory,
    TestTasksRegistryFactory,
    TestTodoFactory,
    TestUserFactory,
)


@pytest.fixture(scope="function")
def container() -> AutoRegisteringContainer:
    container_factory = ContainerFactory()
    return container_factory()


# region Factories


@pytest.fixture(scope="function")
def test_client_factory(container: AutoRegisteringContainer) -> TestClientFactory:
    return TestClientFactory(container=container)


@pytest.fixture(scope="function")
def user_factory(
    transactional_db: None,
    container: AutoRegisteringContainer,
) -> TestUserFactory:
    return TestUserFactory(container=container)


@pytest.fixture(scope="function")
def celery_worker_factory(container: AutoRegisteringContainer) -> TestCeleryWorkerFactory:
    return TestCeleryWorkerFactory(container=container)


@pytest.fixture(scope="function")
def tasks_registry_factory(container: AutoRegisteringContainer) -> TestTasksRegistryFactory:
    return TestTasksRegistryFactory(container=container)


@pytest.fixture(scope="function")
def todo_factory(
    transactional_db: None,
    container: AutoRegisteringContainer,
) -> TestTodoFactory:
    return TestTodoFactory(container=container)


# endregion Factories
```

!!! note "Function-Scoped Fixtures"
    All fixtures use `scope="function"` to ensure complete isolation between tests. Each test gets a fresh container and can override IoC registrations without affecting other tests.

---

## Step 6.3: Write HTTP API Tests

Create comprehensive tests for the Todo HTTP API.

```python title="tests/integration/http/test_v1_todos.py"
from http import HTTPStatus

import pytest

from core.todo.models import Todo
from core.user.models import User
from tests.integration.factories import (
    TestClientFactory,
    TestTodoFactory,
    TestUserFactory,
)


@pytest.fixture(scope="function")
def user(user_factory: TestUserFactory) -> User:
    return user_factory(username="todo_test_user")


@pytest.fixture(scope="function")
def todo(todo_factory: TestTodoFactory, user: User) -> Todo:
    return todo_factory(user=user, title="Existing Todo")


class TestCreateTodo:
    @pytest.mark.django_db(transaction=True)
    def test_create_todo_success(
        self,
        test_client_factory: TestClientFactory,
        user: User,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.post(
                "/v1/todos/",
                json={
                    "title": "Buy groceries",
                    "description": "Milk, eggs, bread",
                },
            )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["description"] == "Milk, eggs, bread"
        assert data["is_completed"] is False
        assert "id" in data

    @pytest.mark.django_db(transaction=True)
    def test_create_todo_requires_authentication(
        self,
        test_client_factory: TestClientFactory,
    ) -> None:
        with test_client_factory() as test_client:  # No auth_for_user
            response = test_client.post(
                "/v1/todos/",
                json={"title": "Test"},
            )

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.django_db(transaction=True)
    def test_create_todo_validation_error(
        self,
        test_client_factory: TestClientFactory,
        user: User,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.post(
                "/v1/todos/",
                json={"description": "Missing title"},  # title is required
            )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


class TestListTodos:
    @pytest.mark.django_db(transaction=True)
    def test_list_todos_returns_only_user_todos(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        todo_factory: TestTodoFactory,
    ) -> None:
        user1 = user_factory(username="user1", email="user1@test.com")
        user2 = user_factory(username="user2", email="user2@test.com")

        # Create todos for both users
        todo_factory(user=user1, title="User1 Todo")
        todo_factory(user=user2, title="User2 Todo")

        # User1 should only see their own todos
        with test_client_factory(auth_for_user=user1) as test_client:
            response = test_client.get("/v1/todos/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["count"] == 1
        assert data["items"][0]["title"] == "User1 Todo"

    @pytest.mark.django_db(transaction=True)
    def test_list_todos_empty(
        self,
        test_client_factory: TestClientFactory,
        user: User,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/todos/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["count"] == 0
        assert data["items"] == []


class TestGetTodo:
    @pytest.mark.django_db(transaction=True)
    def test_get_todo_success(
        self,
        test_client_factory: TestClientFactory,
        user: User,
        todo: Todo,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get(f"/v1/todos/{todo.id}")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["id"] == todo.id
        assert data["title"] == todo.title

    @pytest.mark.django_db(transaction=True)
    def test_get_todo_not_found(
        self,
        test_client_factory: TestClientFactory,
        user: User,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/todos/99999")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.django_db(transaction=True)
    def test_get_todo_from_another_user(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        todo_factory: TestTodoFactory,
    ) -> None:
        user1 = user_factory(username="owner", email="owner@test.com")
        user2 = user_factory(username="other", email="other@test.com")

        todo = todo_factory(user=user1, title="Private Todo")

        # User2 should not access User1's todo
        with test_client_factory(auth_for_user=user2) as test_client:
            response = test_client.get(f"/v1/todos/{todo.id}")

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestCompleteTodo:
    @pytest.mark.django_db(transaction=True)
    def test_complete_todo_success(
        self,
        test_client_factory: TestClientFactory,
        user: User,
        todo: Todo,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.post(f"/v1/todos/{todo.id}/complete")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["is_completed"] is True
        assert data["completed_at"] is not None

    @pytest.mark.django_db(transaction=True)
    def test_complete_todo_not_found(
        self,
        test_client_factory: TestClientFactory,
        user: User,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.post("/v1/todos/99999/complete")

        assert response.status_code == HTTPStatus.NOT_FOUND


class TestDeleteTodo:
    @pytest.mark.django_db(transaction=True)
    def test_delete_todo_success(
        self,
        test_client_factory: TestClientFactory,
        user: User,
        todo: Todo,
    ) -> None:
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.delete(f"/v1/todos/{todo.id}")

            # Verify deletion
            verify_response = test_client.get(f"/v1/todos/{todo.id}")

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert verify_response.status_code == HTTPStatus.NOT_FOUND
```

!!! tip "Test Class Organization"
    Group tests by endpoint/operation using test classes. This improves readability and allows shared fixtures via class-level setup.

---

## Step 6.4: Write Celery Task Tests

Create tests for the todo cleanup task.

```python title="tests/integration/tasks/test_todo_cleanup_task.py"
from datetime import timedelta

import pytest
from django.utils import timezone

from core.todo.models import Todo
from core.user.models import User
from delivery.tasks.tasks.todo_cleanup import TodoCleanupResult
from tests.integration.factories import (
    TestCeleryWorkerFactory,
    TestTasksRegistryFactory,
    TestTodoFactory,
    TestUserFactory,
)


@pytest.fixture(scope="function")
def user(user_factory: TestUserFactory) -> User:
    return user_factory(username="cleanup_test_user")


class TestTodoCleanupTask:
    @pytest.mark.django_db(transaction=True)
    def test_cleanup_deletes_old_completed_todos(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
        todo_factory: TestTodoFactory,
        user: User,
    ) -> None:
        # Create an old completed todo (should be deleted)
        old_todo = todo_factory(user=user, title="Old Todo", is_completed=True)
        old_todo.completed_at = timezone.now() - timedelta(days=10)
        old_todo.save(update_fields=["completed_at"])

        # Create a recent completed todo (should NOT be deleted)
        recent_todo = todo_factory(user=user, title="Recent Todo", is_completed=True)

        # Create an old incomplete todo (should NOT be deleted)
        # Note: incomplete todos don't have completed_at set
        incomplete_todo = todo_factory(user=user, title="Incomplete Todo")

        registry = tasks_registry_factory()

        with celery_worker_factory():
            result = registry.todo_cleanup.delay().get(timeout=5)

        assert result == TodoCleanupResult(deleted_count=1)

        # Verify correct todos remain
        remaining_ids = list(Todo.objects.values_list("id", flat=True))
        assert old_todo.id not in remaining_ids
        assert recent_todo.id in remaining_ids
        assert incomplete_todo.id in remaining_ids

    @pytest.mark.django_db(transaction=True)
    def test_cleanup_with_no_matching_todos(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
        todo_factory: TestTodoFactory,
        user: User,
    ) -> None:
        # Create only recent todos
        todo_factory(user=user, title="Recent Todo 1")
        todo_factory(user=user, title="Recent Todo 2", is_completed=True)

        registry = tasks_registry_factory()

        with celery_worker_factory():
            result = registry.todo_cleanup.delay().get(timeout=5)

        assert result == TodoCleanupResult(deleted_count=0)
        assert Todo.objects.count() == 2

    @pytest.mark.django_db(transaction=True)
    def test_cleanup_with_empty_database(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
    ) -> None:
        registry = tasks_registry_factory()

        with celery_worker_factory():
            result = registry.todo_cleanup.delay().get(timeout=5)

        assert result == TodoCleanupResult(deleted_count=0)
```

!!! info "Celery Worker Context Manager"
    The `celery_worker_factory()` returns a context manager that starts and stops a test worker. Tasks are executed synchronously within the `with` block.

---

## Step 6.5: IoC Override Pattern for Mocking

Override IoC registrations to mock services in specific tests.

```python title="tests/integration/http/test_v1_todos_with_mock.py"
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest

from core.todo.services import TodoNotFoundError, TodoService
from core.user.models import User
from infrastructure.punq.container import AutoRegisteringContainer
from tests.integration.factories import TestClientFactory, TestUserFactory


@pytest.fixture(scope="function")
def user(user_factory: TestUserFactory) -> User:
    return user_factory(username="mock_test_user")


class TestTodoControllerWithMockedService:
    """Example of mocking the service layer for edge case testing."""

    @pytest.mark.django_db(transaction=True)
    def test_get_todo_handles_service_exception(
        self,
        container: AutoRegisteringContainer,
        user: User,
    ) -> None:
        # Create a mock service that raises an exception
        mock_service = MagicMock(spec=TodoService)
        mock_service.get_todo_by_id.side_effect = TodoNotFoundError("Mocked error")

        # Override the IoC registration BEFORE creating the test client
        container.register(TodoService, instance=mock_service)

        # Now create the test client - it will use the mocked service
        test_client_factory = TestClientFactory(container=container)
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/todos/1")

        assert response.status_code == HTTPStatus.NOT_FOUND
        mock_service.get_todo_by_id.assert_called_once_with(todo_id=1, user_id=user.pk)

    @pytest.mark.django_db(transaction=True)
    def test_list_todos_with_custom_mock_data(
        self,
        container: AutoRegisteringContainer,
        user: User,
    ) -> None:
        # Create a mock that returns specific test data
        mock_todo = MagicMock()
        mock_todo.id = 999
        mock_todo.title = "Mocked Todo"
        mock_todo.description = "From mock"
        mock_todo.is_completed = False
        mock_todo.user_id = user.pk

        mock_service = MagicMock(spec=TodoService)
        mock_service.list_todos_for_user.return_value = [mock_todo]

        container.register(TodoService, instance=mock_service)

        test_client_factory = TestClientFactory(container=container)
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/todos/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Mocked Todo"
```

!!! warning "Override Before Creating Factories"
    Always override IoC registrations **before** creating `TestClientFactory`. The container is resolved when the factory creates the API instance.

---

## Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/integration/http/test_v1_todos.py -v

# Run specific test class
pytest tests/integration/http/test_v1_todos.py::TestCreateTodo -v

# Run with coverage
pytest --cov=src --cov-report=html
```

!!! tip "Coverage Requirement"
    The template requires 80% code coverage. Check `pyproject.toml` for coverage configuration.

---

## Test Markers Reference

| Marker | Purpose |
|--------|---------|
| `@pytest.mark.django_db` | Enable database access |
| `@pytest.mark.django_db(transaction=True)` | Use transactional database (required for integration tests) |
| `@pytest.mark.slow` | Mark slow tests (can be skipped with `-m "not slow"`) |

---

## Summary

You have learned how to:

- Create type-safe test factories for domain models
- Write isolated integration tests for HTTP APIs
- Test Celery tasks with the worker context manager
- Override IoC registrations to mock services
- Organize tests using test classes

---

## Congratulations!

You have completed the Todo List tutorial. You now have a fully functional feature with:

- Domain model and service layer
- IoC registration and dependency injection
- HTTP API with authentication
- Background task with scheduling
- Observability and tracing
- Comprehensive test coverage

---

## Next Steps

Explore more advanced topics:

- [Add a New Domain](../how-to/add-new-domain.md) - Build another feature
- [Custom Exception Handling](../how-to/custom-exception-handling.md) - Improve error responses
- [Override IoC in Tests](../how-to/override-ioc-in-tests.md) - Advanced mocking patterns

---

!!! abstract "See Also"
    - [Service Layer](../concepts/service-layer.md) - Understand the architecture
    - [IoC Container](../concepts/ioc-container.md) - Deep dive into dependency injection
    - [Controller Pattern](../concepts/controller-pattern.md) - Learn about controller design
