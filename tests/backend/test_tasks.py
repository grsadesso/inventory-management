"""
Tests for task API endpoints.
"""
import pytest


@pytest.fixture
def new_task():
    """Valid payload as sent by the frontend TasksModal."""
    return {"title": "Check pallets", "priority": "high", "dueDate": "2025-10-20"}


class TestTaskEndpoints:
    """Test suite for task-related endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that the task list starts empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client, new_task):
        """Test creating a task returns a pending task with an id."""
        response = client.post("/api/tasks", json=new_task)
        assert response.status_code == 201

        task = response.json()
        assert isinstance(task["id"], int)
        assert task["title"] == "Check pallets"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-10-20"
        assert task["status"] == "pending"

    def test_created_task_is_listed_newest_first(self, client, new_task):
        """Test that created tasks appear in the list, newest first."""
        first = client.post("/api/tasks", json=new_task).json()
        second = client.post("/api/tasks", json={**new_task, "title": "Second"}).json()
        assert first["id"] != second["id"]

        data = client.get("/api/tasks").json()
        assert [t["id"] for t in data] == [second["id"], first["id"]]

    def test_create_task_default_priority(self, client):
        """Test that priority defaults to medium."""
        response = client.post("/api/tasks", json={"title": "x", "dueDate": "2025-10-20"})
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    @pytest.mark.parametrize("payload", [
        {"priority": "high", "dueDate": "2025-10-20"},                  # missing title
        {"title": "", "priority": "high", "dueDate": "2025-10-20"},     # empty title
        {"title": "x", "priority": "urgent", "dueDate": "2025-10-20"},  # bad priority
        {"title": "x", "priority": "high"},                             # missing dueDate
    ])
    def test_create_task_validation_errors(self, client, payload):
        """Test that invalid payloads are rejected with 422."""
        response = client.post("/api/tasks", json=payload)
        assert response.status_code == 422
        assert client.get("/api/tasks").json() == []

    def test_toggle_task(self, client, new_task):
        """Test toggling between pending and completed."""
        task_id = client.post("/api/tasks", json=new_task).json()["id"]

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert response.json()["status"] == "completed"

        response = client.patch(f"/api/tasks/{task_id}")
        assert response.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling an unknown task."""
        response = client.patch("/api/tasks/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_toggle_invalid_id_type(self, client):
        """Test that a non-integer id is a validation error."""
        assert client.patch("/api/tasks/abc").status_code == 422

    def test_delete_task(self, client, new_task):
        """Test deleting a task."""
        task_id = client.post("/api/tasks", json=new_task).json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json() == {"message": "Task deleted", "id": task_id}
        assert client.get("/api/tasks").json() == []

    def test_delete_nonexistent_task(self, client):
        """Test deleting an unknown task."""
        response = client.delete("/api/tasks/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_state_does_not_leak_between_tests(self, client):
        """Test that the restore fixture cleared tasks created by earlier tests."""
        assert client.get("/api/tasks").json() == []
