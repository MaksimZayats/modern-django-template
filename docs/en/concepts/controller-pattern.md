# Controller Pattern

Controllers provide a unified pattern for handling requests from any source: HTTP, Celery, CLI, etc.

## The Core Abstraction

All controllers inherit from the base `Controller` class:

```python
# src/infrastructure/delivery/controllers.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Controller(ABC):
    @abstractmethod
    def register(self, registry: Any) -> None:
        """Register this controller with the appropriate registry."""
        ...

    def handle_exception(self, exception: Exception) -> Any:
        """Handle exceptions raised by controller methods."""
        raise exception
```

## Key Features

### 1. The `register()` Method

Every controller implements `register()` to connect to its delivery mechanism:

```python
# HTTP Controller
def register(self, registry: APIRouter) -> None:
    registry.add_api_route("/v1/users", self.list_users, methods=["GET"])

# Celery Task Controller
def register(self, registry: Celery) -> None:
    registry.task(name=TaskName.PING)(self.ping)
```

### 2. Automatic Exception Handling

The `__post_init__` method wraps all public methods with exception handling:

```python
def __post_init__(self) -> None:
    self._wrap_methods()

def _wrap_methods(self) -> None:
    for name in dir(self):
        if name.startswith("_"):
            continue
        method = getattr(self, name)
        if callable(method):
            setattr(self, name, self._add_exception_handler(method))
```

This means every public method automatically goes through `handle_exception()` if it raises.

### 3. Custom Exception Handling

Override `handle_exception()` to map domain exceptions to responses:

```python
def handle_exception(self, exception: Exception) -> Any:
    if isinstance(exception, TodoNotFoundError):
        raise HTTPException(status_code=404, detail=str(exception))
    if isinstance(exception, TodoAccessDeniedError):
        raise HTTPException(status_code=403, detail=str(exception))
    return super().handle_exception(exception)
```

## TransactionController

For database operations, use `TransactionController`:

```python
# src/infrastructure/delivery/controllers.py
@dataclass
class TransactionController(Controller):
    def __post_init__(self) -> None:
        super().__post_init__()
        self._wrap_with_transactions()

    def _wrap_with_transactions(self) -> None:
        for name in dir(self):
            if name.startswith("_"):
                continue
            method = getattr(self, name)
            if callable(method):
                setattr(self, name, self._add_transaction(method))
```

This wraps methods with:

- `@transaction.atomic` - Database transaction management
- Logfire spans - Tracing with controller/method names

## HTTP Controller Example

```python
# src/delivery/http/controllers/user/controllers.py
from dataclasses import dataclass, field
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from core.user.services.user import UserService
from delivery.http.auth.jwt import JWTAuth, JWTAuthFactory
from infrastructure.delivery.controllers import TransactionController


@dataclass(kw_only=True)
class UserController(TransactionController):
    """HTTP controller for user operations."""

    _user_service: UserService
    _jwt_auth_factory: JWTAuthFactory

    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()
        super().__post_init__()

    def register(self, registry: APIRouter) -> None:
        registry.add_api_route(
            path="/v1/users/me",
            endpoint=self.get_me,
            methods=["GET"],
            response_model=UserSchema,
            dependencies=[Depends(self._jwt_auth)],
        )

    def get_me(self, request: AuthenticatedRequest) -> UserSchema:
        user = request.state.user
        return UserSchema.model_validate(user, from_attributes=True)

    def handle_exception(self, exception: Exception) -> Any:
        if isinstance(exception, UserNotFoundError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exception),
            ) from exception
        return super().handle_exception(exception)
```

### Key Patterns

1. **Dataclass with `kw_only=True`**: Explicit named parameters
2. **Dependencies as fields**: `_user_service`, `_jwt_auth_factory`
3. **Non-init fields**: `_jwt_auth = field(init=False)` for computed values
4. **`__post_init__`**: Initialize computed fields, call `super().__post_init__()`

## Celery Task Controller Example

```python
# src/delivery/tasks/tasks/ping.py
from dataclasses import dataclass
from typing import TypedDict

from celery import Celery

from delivery.tasks.registry import TaskName
from infrastructure.delivery.controllers import Controller


class PingResult(TypedDict):
    result: str


@dataclass(kw_only=True)
class PingTaskController(Controller):
    """Task controller for ping operation."""

    def register(self, registry: Celery) -> None:
        registry.task(name=TaskName.PING)(self.ping)

    def ping(self) -> PingResult:
        return PingResult(result="pong")
```

## Sync vs Async Handlers

### Prefer Sync Handlers

FastAPI runs sync handlers in a thread pool automatically:

```python
# ✅ Recommended - sync handler
def get_user(self, request: AuthenticatedRequest, user_id: int) -> UserSchema:
    user = self._user_service.get_user_by_id(user_id)
    return UserSchema.model_validate(user, from_attributes=True)
```

### Async When Needed

For truly async operations (external APIs, etc.):

```python
from asgiref.sync import sync_to_async

async def get_user_async(self, request: AuthenticatedRequest, user_id: int) -> UserSchema:
    user = await sync_to_async(
        self._user_service.get_user_by_id,
        thread_sensitive=False,  # Read-only = parallel OK
    )(user_id)
    return UserSchema.model_validate(user, from_attributes=True)
```

Thread sensitivity:

| `thread_sensitive` | Use Case |
|-------------------|----------|
| `False` | Read-only operations (SELECT) |
| `True` | Write operations (INSERT/UPDATE/DELETE) |

## Controller Registration

Controllers are registered in the factory:

```python
# src/delivery/http/factories.py
class FastAPIFactory:
    def _register_controllers(self, router: APIRouter) -> None:
        self._container.resolve(HealthController).register(router)
        self._container.resolve(UserController).register(router)
        self._container.resolve(UserTokenController).register(router)
        self._container.resolve(TodoController).register(router)
```

## Benefits

### 1. Consistent Pattern

Same structure for HTTP and Celery:

```python
# Both have:
# - Dependencies as fields
# - register() method
# - handle_exception() for errors
```

### 2. Automatic Tracing

`TransactionController` adds Logfire spans automatically.

### 3. Exception Isolation

Exceptions are caught and handled uniformly.

### 4. Easy Testing

Mock dependencies, test business logic:

```python
def test_get_user():
    mock_service = MagicMock()
    controller = UserController(_user_service=mock_service, ...)
    # Test controller methods directly
```

## Summary

The controller pattern:

- **Unifies** request handling across HTTP and Celery
- **Enforces** consistent structure via `register()`
- **Wraps** methods with exception handling
- **Provides** `TransactionController` for database operations
- **Enables** easy testing through dependency injection
