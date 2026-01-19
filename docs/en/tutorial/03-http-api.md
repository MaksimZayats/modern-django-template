# Step 3: HTTP API & Admin

In this step, you will create the HTTP API endpoints for the Todo feature using FastAPI and set up the Django admin interface.

## Files Overview

| Action | File Path |
|--------|-----------|
| Create | `src/delivery/http/todo/__init__.py` |
| Create | `src/delivery/http/todo/controllers.py` |
| Create | `src/delivery/http/todo/admin.py` |
| Modify | `src/ioc/registries/delivery.py` |
| Modify | `src/delivery/http/factories.py` |

## Step 3.1: Create the Directory Structure

```bash
mkdir -p src/delivery/http/todo
touch src/delivery/http/todo/__init__.py
```

## Step 3.2: Create Pydantic Schemas and Controller

Create the controller with request/response schemas in `src/delivery/http/todo/controllers.py`.

!!! info "Sync Handlers"
    All handler methods should be **synchronous** (not `async`). FastAPI automatically runs sync handlers in a thread pool using `anyio.to_thread.run_sync()`, which provides proper parallelism for Django's synchronous ORM. You can configure the thread pool size via the `ANYIO_THREAD_LIMITER_TOKENS` environment variable (default: 40 concurrent threads per worker). See `src/infrastructure/anyio/configurator.py` for details.

```python title="src/delivery/http/todo/controllers.py"
from dataclasses import dataclass, field
from datetime import datetime
from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.todo.services import (
    TodoAccessDeniedError,
    TodoNotFoundError,
    TodoService,
)
from infrastructure.delivery.controllers import Controller
from delivery.http.auth.jwt import AuthenticatedRequest, JWTAuth, JWTAuthFactory


# ============================================================================
# Request Schemas
# ============================================================================


class CreateTodoRequestSchema(BaseModel):
    """Schema for creating a new todo item."""

    title: str
    description: str = ""


# ============================================================================
# Response Schemas
# ============================================================================


class TodoSchema(BaseModel):
    """Schema for a single todo item."""

    id: int
    title: str
    description: str
    is_completed: bool
    created_at: datetime
    completed_at: datetime | None


class TodoListSchema(BaseModel):
    """Schema for a list of todo items."""

    items: list[TodoSchema]
    count: int


# ============================================================================
# Controller
# ============================================================================


@dataclass
class TodoController(Controller):
    """HTTP controller for todo operations.

    All endpoints require JWT authentication. The controller uses the
    TodoService for all data operations and never accesses models directly.
    """

    _jwt_auth_factory: JWTAuthFactory
    _todo_service: TodoService
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()

    def register(self, registry: APIRouter) -> None:
        """Register all todo endpoints with the router."""
        registry.add_api_route(
            path="/v1/todos/",
            methods=["GET"],
            endpoint=self.list_todos,
            response_model=TodoListSchema,
            dependencies=[Depends(self._jwt_auth)],
        )

        registry.add_api_route(
            path="/v1/todos/",
            methods=["POST"],
            endpoint=self.create_todo,
            response_model=TodoSchema,
            dependencies=[Depends(self._jwt_auth)],
        )

        registry.add_api_route(
            path="/v1/todos/{todo_id}",
            methods=["GET"],
            endpoint=self.get_todo,
            response_model=TodoSchema,
            dependencies=[Depends(self._jwt_auth)],
        )

        registry.add_api_route(
            path="/v1/todos/{todo_id}/complete",
            methods=["POST"],
            endpoint=self.complete_todo,
            response_model=TodoSchema,
            dependencies=[Depends(self._jwt_auth)],
        )

        registry.add_api_route(
            path="/v1/todos/{todo_id}",
            methods=["DELETE"],
            endpoint=self.delete_todo,
            dependencies=[Depends(self._jwt_auth)],
        )

    def list_todos(
        self,
        request: AuthenticatedRequest,
    ) -> TodoListSchema:
        """List all todos for the authenticated user."""
        todos = self._todo_service.list_todos_for_user(user=request.state.user)
        return TodoListSchema(
            items=[
                TodoSchema.model_validate(todo, from_attributes=True)
                for todo in todos
            ],
            count=len(todos),
        )

    def create_todo(
        self,
        request: AuthenticatedRequest,
        body: CreateTodoRequestSchema,
    ) -> TodoSchema:
        """Create a new todo for the authenticated user."""
        todo = self._todo_service.create_todo(
            title=body.title,
            description=body.description,
            user=request.state.user,
        )
        return TodoSchema.model_validate(todo, from_attributes=True)

    def get_todo(
        self,
        request: AuthenticatedRequest,
        todo_id: int,
    ) -> TodoSchema:
        """Get a specific todo by ID."""
        todo = self._todo_service.get_todo_by_id(
            todo_id=todo_id,
            user=request.state.user,
        )
        return TodoSchema.model_validate(todo, from_attributes=True)

    def complete_todo(
        self,
        request: AuthenticatedRequest,
        todo_id: int,
    ) -> TodoSchema:
        """Mark a todo as completed."""
        todo = self._todo_service.complete_todo(
            todo_id=todo_id,
            user=request.state.user,
        )
        return TodoSchema.model_validate(todo, from_attributes=True)

    def delete_todo(
        self,
        request: AuthenticatedRequest,
        todo_id: int,
    ) -> None:
        """Delete a todo."""
        self._todo_service.delete_todo(
            todo_id=todo_id,
            user=request.state.user,
        )

    def handle_exception(self, exception: Exception) -> Any:
        """Convert domain exceptions to HTTP errors."""
        if isinstance(exception, TodoNotFoundError):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Todo with id {exception.todo_id} not found",
            ) from exception

        if isinstance(exception, TodoAccessDeniedError):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="You do not have permission to access this todo",
            ) from exception

        return super().handle_exception(exception)
```

### Controller Anatomy

Let's break down the key parts of the controller:

#### Dataclass with Dependency Injection

```python
@dataclass
class TodoController(Controller):
    _jwt_auth_factory: JWTAuthFactory
    _todo_service: TodoService
    _jwt_auth: JWTAuth = field(init=False)

    def __post_init__(self) -> None:
        self._jwt_auth = self._jwt_auth_factory()
```

The container automatically injects dependencies when creating the controller. Using `@dataclass` with `field(init=False)` allows us to create the JWT auth instance after injection.

#### Route Registration

```python
def register(self, registry: APIRouter) -> None:
    registry.add_api_route(
        path="/v1/todos/",
        methods=["GET"],
        endpoint=self.list_todos,
        response_model=TodoListSchema,
        dependencies=[Depends(self._jwt_auth)],
    )
```

Each endpoint specifies:

- **path**: The URL path
- **methods**: HTTP methods (GET, POST, etc.)
- **endpoint**: The handler method
- **response_model**: The Pydantic schema for the response (for API documentation)
- **dependencies**: FastAPI dependencies including authentication

#### Sync Handler Methods

```python
def list_todos(
    self,
    request: AuthenticatedRequest,  # User available via request.state.user
) -> TodoListSchema:
    """Sync handler - FastAPI runs in thread pool automatically."""
    todos = self._todo_service.list_todos_for_user(user=request.state.user)
    return TodoListSchema(...)
```

Use `AuthenticatedRequest` for endpoints that require authentication. The authenticated user is available via `request.state.user`.

!!! warning "Why Sync Handlers?"
    Django's ORM is synchronous. Using `async def` handlers with sync service calls blocks the event loop. FastAPI automatically runs sync handlers in `anyio.to_thread.run_sync()`, providing proper parallelism.

    **Thread pool configuration:** Set `ANYIO_THREAD_LIMITER_TOKENS` environment variable to control concurrent threads per worker (default: 40). See `src/infrastructure/anyio/configurator.py`.

!!! tip "Async Handlers (Advanced)"
    If you need async handlers (e.g., for external async HTTP clients), use `asgiref.sync_to_async` to call services:

    ```python
    from asgiref.sync import sync_to_async

    async def list_todos_async(self, request: AuthenticatedRequest) -> TodoListSchema:
        # thread_sensitive=False for read-only operations
        todos = await sync_to_async(
            self._todo_service.list_todos_for_user,
            thread_sensitive=False,  # Read-only: can run in any thread
        )(user=user)
        return TodoListSchema(...)

    async def create_todo_async(self, request: AuthenticatedRequest, body: CreateTodoRequestSchema) -> TodoSchema:
        # thread_sensitive=True for write operations (default)
        todo = await sync_to_async(
            self._todo_service.create_todo,
            thread_sensitive=True,  # Write: must run in same thread for transaction safety
        )(title=body.title, description=body.description, user=user)
        return TodoSchema.model_validate(todo, from_attributes=True)
    ```

#### Exception Handling

```python
def handle_exception(self, exception: Exception) -> Any:
    if isinstance(exception, TodoNotFoundError):
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Todo with id {exception.todo_id} not found",
        ) from exception
    # ...
    return super().handle_exception(exception)
```

The `handle_exception` method catches domain exceptions and converts them to HTTP exceptions. Always call `super().handle_exception(exception)` for unhandled exceptions.

!!! info "Automatic Exception Wrapping"
    The `Controller` base class automatically wraps all handler methods with exception handling. You don't need to add try/except blocks in your handlers.

## Step 3.3: Create the Admin Interface

Create the Django admin configuration in `src/delivery/http/todo/admin.py`:

```python title="src/delivery/http/todo/admin.py"
from django.contrib import admin

from core.todo.models import Todo


@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin[Todo]):
    """Admin interface for Todo model."""

    list_display = (
        "id",
        "title",
        "user",
        "is_completed",
        "created_at",
        "completed_at",
    )

    list_filter = (
        "is_completed",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "user__username",
    )

    readonly_fields = (
        "created_at",
        "completed_at",
    )

    raw_id_fields = ("user",)
```

!!! note "Admin and Models"
    Django admin is one of the acceptable places to import models directly, as documented in `CLAUDE.md`. The admin requires direct model access for its functionality.

## Step 3.4: Register the Controller in IoC

Add the controller registration in `src/ioc/registries/delivery.py`.

First, add the import:

```python title="src/ioc/registries/delivery.py" hl_lines="4"
from delivery.http.factories import AdminSiteFactory, FastAPIFactory, URLPatternsFactory
from delivery.http.controllers.health.controllers import HealthController
from delivery.http.controllers.user.controllers import UserController, UserTokenController
from delivery.http.todo.controllers import TodoController  # Add this import
```

Then add the registration in `_register_http_controllers`:

```python title="src/ioc/registries/delivery.py" hl_lines="5"
def _register_http_controllers(container: Container) -> None:
    container.register(HealthController, scope=Scope.singleton)
    container.register(UserController, scope=Scope.singleton)
    container.register(UserTokenController, scope=Scope.singleton)
    container.register(TodoController, scope=Scope.singleton)  # Add this line
```

## Step 3.5: Update the API Factory

Modify `src/delivery/http/factories.py` to include the todo controller.

First, add the import:

```python title="src/delivery/http/factories.py" hl_lines="4"
from delivery.http.controllers.health.controllers import HealthController
from delivery.http.controllers.user.controllers import UserController, UserTokenController
from delivery.http.todo.controllers import TodoController  # Add this import
```

Then update the `FastAPIFactory` class:

```python title="src/delivery/http/factories.py" hl_lines="8 14 30-31"
@dataclass
class FastAPIFactory:
    _settings: ApplicationSettings
    _health_controller: HealthController
    _user_token_controller: UserTokenController
    _user_controller: UserController
    _todo_controller: TodoController  # Add this field

    def __call__(self) -> FastAPI:
        app = FastAPI(
            title="Fast Django API",
            debug=self._settings.debug,
        )

        router = APIRouter()

        # Register controllers
        self._health_controller.register(registry=router)
        self._user_controller.register(registry=router)
        self._user_token_controller.register(registry=router)
        self._todo_controller.register(registry=router)  # Register todo controller

        app.include_router(router)

        return app
```

!!! note "Simplified Example"
    This example is simplified for clarity. The production implementation in `src/delivery/http/factories.py` includes additional configuration for middleware, CORS, telemetry, and lifespan management.

Finally, update the `AdminSiteFactory` to import the todo admin:

```python title="src/delivery/http/factories.py" hl_lines="4"
class AdminSiteFactory:
    def __call__(self) -> AdminSite:
        from delivery.http.controllers.user import admin as _user_admin
        from delivery.http.todo import admin as _todo_admin  # noqa: F401, PLC0415

        return default_site
```

## Step 3.6: Test the API

Start the development server:

```bash
make dev
```

### API Documentation

Visit http://localhost:8000/api/docs to see the Swagger UI with your new endpoints:

- `GET /api/v1/todos/` - List all todos
- `POST /api/v1/todos/` - Create a new todo
- `GET /api/v1/todos/{todo_id}` - Get a specific todo
- `POST /api/v1/todos/{todo_id}/complete` - Mark a todo as complete
- `DELETE /api/v1/todos/{todo_id}` - Delete a todo

### Test with curl

First, create a user and get a token:

```bash
# Create a user
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "SecurePass123!"
  }'

# Get an access token
curl -X POST http://localhost:8000/api/v1/users/me/token \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "SecurePass123!"}'
```

Save the `access_token` from the response, then test the todo endpoints:

```bash
# Set your token
TOKEN="your_access_token_here"

# Create a todo
curl -X POST http://localhost:8000/api/v1/todos/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title": "Learn FastAPI", "description": "Complete the tutorial"}'

# List todos
curl -X GET http://localhost:8000/api/v1/todos/ \
  -H "Authorization: Bearer $TOKEN"

# Complete a todo (replace 1 with actual todo ID)
curl -X POST http://localhost:8000/api/v1/todos/1/complete \
  -H "Authorization: Bearer $TOKEN"
```

### Django Admin

Visit http://localhost:8000/admin/ to manage todos through the admin interface. You'll need to create a superuser first:

```bash
python src/manage.py createsuperuser
```

## What's Next

You have created a complete HTTP API for the Todo feature:

- [x] Pydantic schemas for request/response validation
- [x] Controller with CRUD endpoints
- [x] JWT authentication on all endpoints
- [x] Exception handling
- [x] Django admin interface
- [x] IoC registration

In the next step, you will create a Celery task to clean up old completed todos.

[Continue to Step 4: Celery Tasks](04-celery-tasks.md){ .md-button .md-button--primary }

---

!!! abstract "See Also"
    - [Controller Pattern](../concepts/controller-pattern.md) - Deep dive into the controller pattern
