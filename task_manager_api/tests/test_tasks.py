import pytest


def test_create_task(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    response = client.post(
        f"/projects/{project_id}/tasks",
        json={
            "title": "My New Task",
            "description": "Task description",
            "status": "todo",
            "priority": "high",
            "due_date": "2026-12-31",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Task created successfully"
    data = body["data"]
    assert data["title"] == "My New Task"
    assert data["description"] == "Task description"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-12-31"
    assert data["project_id"] == project_id
    assert "id" in data


def test_create_task_minimal(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Minimal Task"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["title"] == "Minimal Task"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["due_date"] is None


def test_create_task_title_too_long(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "x" * 201},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_create_task_project_not_found(client, auth_headers):
    response = client.post(
        "/projects/00000000-0000-0000-0000-000000000000/tasks",
        json={"title": "Ghost Task"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_create_task_on_other_users_project(client, other_user_headers, sample_project):
    project_id = sample_project["id"]
    response = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Intruder Task"},
        headers=other_user_headers,
    )
    assert response.status_code == 403


def test_list_tasks(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    for i in range(3):
        client.post(
            f"/projects/{project_id}/tasks",
            json={"title": f"Task {i}"},
            headers=auth_headers,
        )

    response = client.get(f"/projects/{project_id}/tasks", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 3
    assert body["meta"]["total"] == 3


def test_list_tasks_pagination(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    for i in range(5):
        client.post(
            f"/projects/{project_id}/tasks",
            json={"title": f"Task {i}"},
            headers=auth_headers,
        )

    response = client.get(f"/projects/{project_id}/tasks?page=1&per_page=3", headers=auth_headers)
    body = response.json()
    assert len(body["data"]) == 3
    assert body["meta"]["total"] == 5
    assert body["meta"]["total_pages"] == 2


def test_list_tasks_status_filter(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    client.post(f"/projects/{project_id}/tasks", json={"title": "T1", "status": "todo"}, headers=auth_headers)
    client.post(f"/projects/{project_id}/tasks", json={"title": "T2", "status": "in_progress"}, headers=auth_headers)
    client.post(f"/projects/{project_id}/tasks", json={"title": "T3", "status": "done"}, headers=auth_headers)

    response = client.get(f"/projects/{project_id}/tasks?status=todo", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(t["status"] == "todo" for t in data)
    assert len(data) == 1


def test_list_tasks_priority_filter(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    client.post(f"/projects/{project_id}/tasks", json={"title": "Low", "priority": "low"}, headers=auth_headers)
    client.post(f"/projects/{project_id}/tasks", json={"title": "High", "priority": "high"}, headers=auth_headers)

    response = client.get(f"/projects/{project_id}/tasks?priority=high", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert all(t["priority"] == "high" for t in data)
    assert len(data) == 1


def test_list_tasks_sort_by_due_date(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Later", "due_date": "2027-06-01"},
        headers=auth_headers,
    )
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Earlier", "due_date": "2026-01-01"},
        headers=auth_headers,
    )

    response = client.get(
        f"/projects/{project_id}/tasks?sort_by=due_date&sort_order=asc",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    # Filter to only the ones with due dates we set
    dated = [t for t in data if t["due_date"] is not None]
    assert dated[0]["title"] == "Earlier"
    assert dated[1]["title"] == "Later"


def test_get_task(client, auth_headers, sample_task):
    task_id = sample_task["id"]
    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == task_id


def test_get_task_not_found(client, auth_headers):
    response = client.get("/tasks/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


def test_get_other_users_task_403(client, other_user_headers, sample_task):
    task_id = sample_task["id"]
    response = client.get(f"/tasks/{task_id}", headers=other_user_headers)
    assert response.status_code == 403


def test_update_task(client, auth_headers, sample_task):
    task_id = sample_task["id"]
    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "Updated Title", "status": "in_progress", "priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == "Updated Title"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"


def test_update_task_partial(client, auth_headers, sample_task):
    task_id = sample_task["id"]
    original_title = sample_task["title"]
    response = client.patch(
        f"/tasks/{task_id}",
        json={"status": "done"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["title"] == original_title
    assert data["status"] == "done"


def test_update_task_not_found(client, auth_headers):
    response = client.patch(
        "/tasks/00000000-0000-0000-0000-000000000000",
        json={"title": "Ghost"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_update_other_users_task_403(client, other_user_headers, sample_task):
    task_id = sample_task["id"]
    response = client.patch(
        f"/tasks/{task_id}",
        json={"title": "Hijacked"},
        headers=other_user_headers,
    )
    assert response.status_code == 403


def test_delete_task(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    create_resp = client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "To Delete"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["data"]["id"]

    delete_resp = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "Task deleted successfully"

    get_resp = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_task_not_found(client, auth_headers):
    response = client.delete("/tasks/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


def test_delete_other_users_task_403(client, other_user_headers, sample_task):
    task_id = sample_task["id"]
    response = client.delete(f"/tasks/{task_id}", headers=other_user_headers)
    assert response.status_code == 403


def test_cascade_delete_project_removes_tasks(client, auth_headers, sample_project):
    project_id = sample_project["id"]

    # Create tasks
    task_responses = []
    for i in range(3):
        resp = client.post(
            f"/projects/{project_id}/tasks",
            json={"title": f"Task {i}"},
            headers=auth_headers,
        )
        task_responses.append(resp.json()["data"])

    # Delete the project
    delete_resp = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert delete_resp.status_code == 200

    # All tasks should now be gone
    for task in task_responses:
        get_resp = client.get(f"/tasks/{task['id']}", headers=auth_headers)
        assert get_resp.status_code == 404
