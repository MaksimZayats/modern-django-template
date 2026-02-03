# Test Scenarios Reference

This reference provides complete test patterns for common scenarios.

## Contents

- [User-Scoped Resource Tests](#user-scoped-resource-tests)
- [Error Handling Tests](#error-handling-tests)
- [Pagination Tests](#pagination-tests)
- [Authentication Tests](#authentication-tests)
- [Celery Task Tests](#celery-task-tests)
- [Empty State Tests](#empty-state-tests)
- [Update Tests](#update-tests)
- [Delete Tests](#delete-tests)

## User-Scoped Resource Tests

When resources belong to specific users and should not be accessible by others:

```python
class TestUserScopedResources:
    @pytest.mark.django_db(transaction=True)
    def test_list_returns_only_user_items(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        # Create two users
        user1 = user_factory(username="user1", email="user1@test.com")
        user2 = user_factory(username="user2", email="user2@test.com")

        # Create items for each user
        item_factory(user=user1, name="User1 Item")
        item_factory(user=user2, name="User2 Item")

        # User1 should only see their items
        with test_client_factory(auth_for_user=user1) as test_client:
            response = test_client.get("/v1/items/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "User1 Item"

    @pytest.mark.django_db(transaction=True)
    def test_cannot_access_other_user_item(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        owner = user_factory(username="owner", email="owner@test.com")
        other = user_factory(username="other", email="other@test.com")

        item = item_factory(user=owner, name="Private Item")

        # Other user should not access owner's item
        with test_client_factory(auth_for_user=other) as test_client:
            response = test_client.get(f"/v1/items/{item.id}")

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.django_db(transaction=True)
    def test_cannot_update_other_user_item(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        owner = user_factory(username="owner", email="owner@test.com")
        other = user_factory(username="other", email="other@test.com")

        item = item_factory(user=owner, name="Private Item")

        with test_client_factory(auth_for_user=other) as test_client:
            response = test_client.patch(
                f"/v1/items/{item.id}",
                json={"name": "Hacked"},
            )

        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.django_db(transaction=True)
    def test_cannot_delete_other_user_item(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        owner = user_factory(username="owner", email="owner@test.com")
        other = user_factory(username="other", email="other@test.com")

        item = item_factory(user=owner, name="Private Item")

        with test_client_factory(auth_for_user=other) as test_client:
            response = test_client.delete(f"/v1/items/{item.id}")

        assert response.status_code == HTTPStatus.NOT_FOUND
```

## Error Handling Tests

Testing that domain exceptions are properly converted to HTTP responses:

```python
class TestErrorHandling:
    @pytest.mark.django_db(transaction=True)
    def test_not_found_returns_404(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
    ) -> None:
        user = user_factory()
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/items/99999")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.django_db(transaction=True)
    def test_validation_error_returns_422(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
    ) -> None:
        user = user_factory()
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.post("/v1/items/", json={})

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.django_db(transaction=True)
    def test_service_exception_with_mock(
        self,
        container: Container,
        user_factory: TestUserFactory,
    ) -> None:
        mock_service = MagicMock(spec=ItemService)
        mock_service.get_by_id.side_effect = ItemNotFoundError("Mocked error")

        container.register(ItemService, instance=mock_service)

        user = user_factory()
        test_client_factory = TestClientFactory(container=container)
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/items/1")

        assert response.status_code == HTTPStatus.NOT_FOUND
        mock_service.get_by_id.assert_called_once()
```

## Pagination Tests

Testing paginated endpoints:

```python
class TestPagination:
    @pytest.mark.django_db(transaction=True)
    def test_pagination_defaults(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        user = user_factory()

        # Create 25 items
        for i in range(25):
            item_factory(user=user, name=f"Item {i}")

        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/items/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()

        # Check pagination metadata
        assert "count" in data or "total" in data
        assert "items" in data or isinstance(data, list)

    @pytest.mark.django_db(transaction=True)
    def test_pagination_with_limit(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        user = user_factory()
        for i in range(10):
            item_factory(user=user, name=f"Item {i}")

        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/items/?limit=5")

        assert response.status_code == HTTPStatus.OK
        data = response.json()

        if "items" in data:
            assert len(data["items"]) == 5
        else:
            assert len(data) == 5
```

## Authentication Tests

Testing authentication requirements:

```python
class TestAuthentication:
    @pytest.mark.django_db(transaction=True)
    def test_endpoint_requires_auth(
        self,
        test_client_factory: TestClientFactory,
    ) -> None:
        with test_client_factory() as test_client:  # No auth
            response = test_client.get("/v1/protected/")

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.django_db(transaction=True)
    def test_invalid_token_rejected(
        self,
        test_client_factory: TestClientFactory,
    ) -> None:
        with test_client_factory() as test_client:
            response = test_client.get(
                "/v1/protected/",
                headers={"Authorization": "Bearer invalid-token"},
            )

        assert response.status_code == HTTPStatus.UNAUTHORIZED

    @pytest.mark.django_db(transaction=True)
    def test_valid_token_accepted(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
    ) -> None:
        user = user_factory()
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/protected/")

        assert response.status_code == HTTPStatus.OK
```

## Celery Task Tests

### Basic Task Test

```python
class TestPingTask:
    @pytest.mark.django_db(transaction=True)
    def test_ping_returns_pong(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
    ) -> None:
        registry = tasks_registry_factory()

        with celery_worker_factory():
            result = registry.ping.delay().get(timeout=5)

        assert result.result == "pong"
```

### Task with Side Effects

```python
class TestCleanupTask:
    @pytest.mark.django_db(transaction=True)
    def test_cleanup_deletes_old_items(
        self,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
        item_factory: TestItemFactory,
        user_factory: TestUserFactory,
    ) -> None:
        user = user_factory()

        # Create old item (should be deleted)
        old_item = item_factory(user=user, name="Old")
        old_item.created_at = timezone.now() - timedelta(days=30)
        old_item.save()

        # Create recent item (should NOT be deleted)
        recent_item = item_factory(user=user, name="Recent")

        registry = tasks_registry_factory()

        with celery_worker_factory():
            result = registry.cleanup.delay().get(timeout=5)

        assert result.deleted_count == 1

        # Verify correct items remain
        remaining = list(Item.objects.values_list("id", flat=True))
        assert old_item.id not in remaining
        assert recent_item.id in remaining
```

### Task with Mocked Service

```python
class TestNotificationTask:
    @pytest.mark.django_db(transaction=True)
    def test_task_calls_service(
        self,
        container: Container,
        celery_worker_factory: TestCeleryWorkerFactory,
        tasks_registry_factory: TestTasksRegistryFactory,
    ) -> None:
        mock_service = MagicMock(spec=NotificationService)
        mock_service.send.return_value = True
        container.register(NotificationService, instance=mock_service)

        registry = tasks_registry_factory()

        with celery_worker_factory():
            result = registry.send_notification.delay(
                user_id=1,
                message="Hello",
            ).get(timeout=5)

        assert result["status"] == "sent"
        mock_service.send.assert_called_once()
```

## Empty State Tests

Testing behavior when no data exists:

```python
class TestEmptyState:
    @pytest.mark.django_db(transaction=True)
    def test_list_empty_returns_empty_array(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
    ) -> None:
        user = user_factory()
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.get("/v1/items/")

        assert response.status_code == HTTPStatus.OK
        data = response.json()

        if isinstance(data, list):
            assert data == []
        elif "items" in data:
            assert data["items"] == []
            assert data["count"] == 0
```

## Update Tests

Testing partial updates:

```python
class TestUpdate:
    @pytest.mark.django_db(transaction=True)
    def test_partial_update(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        user = user_factory()
        item = item_factory(user=user, name="Original", description="Desc")

        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.patch(
                f"/v1/items/{item.id}",
                json={"name": "Updated"},  # Only update name
            )

        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Desc"  # Unchanged

    @pytest.mark.django_db(transaction=True)
    def test_update_with_empty_body(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        user = user_factory()
        item = item_factory(user=user, name="Original")

        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.patch(
                f"/v1/items/{item.id}",
                json={},  # Empty update
            )

        # Should succeed with no changes
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["name"] == "Original"
```

## Delete Tests

Testing deletion behavior:

```python
class TestDelete:
    @pytest.mark.django_db(transaction=True)
    def test_delete_success(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
        item_factory: TestItemFactory,
    ) -> None:
        user = user_factory()
        item = item_factory(user=user, name="ToDelete")

        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.delete(f"/v1/items/{item.id}")

            # Verify item is gone
            verify_response = test_client.get(f"/v1/items/{item.id}")

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert verify_response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.django_db(transaction=True)
    def test_delete_nonexistent_returns_404(
        self,
        test_client_factory: TestClientFactory,
        user_factory: TestUserFactory,
    ) -> None:
        user = user_factory()
        with test_client_factory(auth_for_user=user) as test_client:
            response = test_client.delete("/v1/items/99999")

        assert response.status_code == HTTPStatus.NOT_FOUND
```
