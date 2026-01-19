# Override IoC in Tests

This guide explains how to mock services and dependencies in integration tests by overriding IoC container registrations.

## How Test Isolation Works

Each test function receives a fresh IoC container through the `container` fixture. This allows you to override specific registrations without affecting other tests.

```python
# tests/integration/conftest.py
from ioc.container import ContainerFactory
from infrastructure.frameworks.punq import AutoRegisteringContainer


@pytest.fixture(scope="function")
def container() -> AutoRegisteringContainer:
    container_factory = ContainerFactory()
    return container_factory()
```

The `scope="function"` ensures a new container is created for each test.

## Basic Pattern

### Step 1: Create a Mock Service

```python
from unittest.mock import MagicMock

import pytest

from core.products.services import ProductService


@pytest.fixture
def mock_product_service() -> MagicMock:
    mock = MagicMock(spec=ProductService)
    mock.get_product_by_id.return_value = MagicMock(
        id=1,
        name="Mocked Product",
        description="This is a mock",
        price=99.99,
    )
    return mock
```

### Step 2: Override the Registration

```python
from infrastructure.frameworks.punq import AutoRegisteringContainer


def test_with_mocked_service(
        container: AutoRegisteringContainer,
        mock_product_service: MagicMock,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
) -> None:
    # Override the service registration BEFORE creating factories
    container.register(ProductService, instance=mock_product_service)

    # Now create the test client - it will use the mocked service
    user = user_factory()
    with test_client_factory(auth_for_user=user) as test_client:
        response = test_client.get("/v1/products/1")

    assert response.status_code == 200
    assert response.json()["name"] == "Mocked Product"

    # Verify the mock was called
    mock_product_service.get_product_by_id.assert_called_once_with(1)
```

## Complete Example: Mocking JWTService

Here is a full example that mocks the JWT service to test authentication behavior:

```python
from http import HTTPStatus
from unittest.mock import MagicMock

import pytest

from core.user.services.jwt import JWTService
from infrastructure.frameworks.punq import AutoRegisteringContainer
from tests.integration.factories import TestClientFactory, TestUserFactory


@pytest.fixture
def mock_jwt_service() -> MagicMock:
    mock = MagicMock(spec=JWTService)
    # Configure the mock to return a specific payload
    mock.decode_token.return_value = {"sub": 1, "exp": 9999999999}
    mock.issue_access_token.return_value = "mocked-access-token"
    return mock


@pytest.mark.django_db(transaction=True)
def test_jwt_decoding_with_mock(
        container: AutoRegisteringContainer,
        mock_jwt_service: MagicMock,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
) -> None:
    # Register the mock BEFORE creating factories
    container.register(JWTService, instance=mock_jwt_service)

    # Create user and test client
    user = user_factory()
    with test_client_factory() as test_client:
        # Make authenticated request
        response = test_client.get(
            "/v1/users/me",
            headers={"Authorization": "Bearer any-token-will-work"},
        )

    # The mock returns sub=1, but our test user might have a different ID
    # This test verifies the JWT decoding flow, not the user lookup
    mock_jwt_service.decode_token.assert_called_once_with(token="any-token-will-work")
```

## Testing Error Scenarios

Override services to simulate error conditions:

```python
from core.products.services import ProductNotFoundError, ProductService
from infrastructure.frameworks.punq import AutoRegisteringContainer


@pytest.mark.django_db(transaction=True)
def test_product_not_found_error(
        container: AutoRegisteringContainer,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
) -> None:
    # Create a mock that raises an exception
    mock_service = MagicMock(spec=ProductService)
    mock_service.get_product_by_id.side_effect = ProductNotFoundError("Product 999 not found")

    container.register(ProductService, instance=mock_service)

    user = user_factory()
    with test_client_factory(auth_for_user=user) as test_client:
        response = test_client.get("/v1/products/999")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "not found" in response.json()["detail"].lower()
```

## Mocking External Services

For services that make external API calls:

```python
from unittest.mock import MagicMock, patch

import pytest

from infrastructure.frameworks.punq import AutoRegisteringContainer


class PaymentGateway:
    def charge(self, amount: float, card_token: str) -> dict:
        # Real implementation calls external API
        ...


@pytest.fixture
def mock_payment_gateway() -> MagicMock:
    mock = MagicMock(spec=PaymentGateway)
    mock.charge.return_value = {
        "transaction_id": "txn_123",
        "status": "success",
    }
    return mock


@pytest.mark.django_db(transaction=True)
def test_payment_processing(
        container: AutoRegisteringContainer,
        mock_payment_gateway: MagicMock,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
) -> None:
    container.register(PaymentGateway, instance=mock_payment_gateway)

    user = user_factory()
    with test_client_factory(auth_for_user=user) as test_client:
        response = test_client.post(
            "/v1/payments/",
            json={"amount": 100.00, "card_token": "tok_test"},
        )

    assert response.status_code == HTTPStatus.OK
    mock_payment_gateway.charge.assert_called_once_with(100.00, "tok_test")
```

## Important Considerations

!!! warning "Order Matters"
    Always override IoC registrations **before** creating factories or test clients. The factories resolve dependencies at creation time.

```python
# Correct order
container.register(ProductService, instance=mock_service)  # 1. Override first
with test_client_factory() as test_client:  # 2. Then create client
    response = test_client.get("/v1/products/1")

# Wrong order - mock will not be used
with test_client_factory() as test_client:  # Client created with real service
    container.register(ProductService, instance=mock_service)  # Too late!
```

!!! tip "Use spec Parameter"
    Always use `MagicMock(spec=ServiceClass)` to ensure your mock has the same interface as the real service. This catches typos in method names.

## Testing Celery Tasks with Mocks

Override services for Celery task tests:

```python
from unittest.mock import MagicMock

import pytest

from core.notifications.services import NotificationService
from infrastructure.frameworks.punq import AutoRegisteringContainer
from tests.integration.factories import TestCeleryWorkerFactory, TestTasksRegistryFactory


@pytest.mark.django_db(transaction=True)
def test_notification_task_with_mock(
        container: AutoRegisteringContainer,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
) -> None:
    # Mock the notification service
    mock_notification = MagicMock(spec=NotificationService)
    mock_notification.send_email.return_value = True
    container.register(NotificationService, instance=mock_notification)

    # Create registry and start worker
    registry = tasks_registry_factory()

    with celery_worker_factory():
        result = registry.send_notification.delay(
            user_id=1,
            message="Hello",
        ).get(timeout=5)

    assert result["status"] == "sent"
    mock_notification.send_email.assert_called_once()
```

## Summary

1. Use function-scoped `container` fixture for test isolation
2. Override registrations with `container.register(Service, instance=mock)`
3. Always override **before** creating factories or test clients
4. Use `MagicMock(spec=ServiceClass)` for type-safe mocks
5. Configure mock return values and side effects for different scenarios
6. Use `assert_called_once()` and similar methods to verify interactions
