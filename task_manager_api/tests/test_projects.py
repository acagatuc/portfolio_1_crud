import pytest


def test_create_project(client, auth_headers):
    response = client.post(
        "/projects",
        json={"name": "My New Project", "description": "Project description", "status": "active"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "Project created successfully"
    data = body["data"]
    assert data["name"] == "My New Project"
    assert data["description"] == "Project description"
    assert data["status"] == "active"
    assert "id" in data
    assert "task_counts" in data
    assert data["task_counts"] == {"todo": 0, "in_progress": 0, "done": 0}


def test_create_project_minimal(client, auth_headers):
    response = client.post(
        "/projects",
        json={"name": "Minimal Project"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Minimal Project"
    assert data["description"] is None
    assert data["status"] == "active"


def test_create_project_name_too_long(client, auth_headers):
    response = client.post(
        "/projects",
        json={"name": "x" * 101},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_projects_empty(client, auth_headers):
    response = client.get("/projects", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert "meta" in body
    assert body["meta"]["total"] == 0
    assert body["meta"]["page"] == 1


def test_list_projects_with_pagination(client, auth_headers):
    # Create 3 projects
    for i in range(3):
        client.post(
            "/projects",
            json={"name": f"Project {i}"},
            headers=auth_headers,
        )

    response = client.get("/projects?page=1&per_page=2", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2
    assert body["meta"]["total"] == 3
    assert body["meta"]["per_page"] == 2
    assert body["meta"]["total_pages"] == 2

    response_page2 = client.get("/projects?page=2&per_page=2", headers=auth_headers)
    assert response_page2.status_code == 200
    body2 = response_page2.json()
    assert len(body2["data"]) == 1


def test_list_projects_status_filter(client, auth_headers):
    client.post("/projects", json={"name": "Active Project", "status": "active"}, headers=auth_headers)
    client.post("/projects", json={"name": "Archived Project", "status": "archived"}, headers=auth_headers)

    active_resp = client.get("/projects?status=active", headers=auth_headers)
    assert active_resp.status_code == 200
    active_data = active_resp.json()["data"]
    assert all(p["status"] == "active" for p in active_data)

    archived_resp = client.get("/projects?status=archived", headers=auth_headers)
    assert archived_resp.status_code == 200
    archived_data = archived_resp.json()["data"]
    assert all(p["status"] == "archived" for p in archived_data)


def test_get_project_by_id(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    response = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == project_id
    assert "task_counts" in data


def test_get_project_with_task_counts(client, auth_headers, sample_project):
    project_id = sample_project["id"]

    # Create tasks with different statuses
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Task 1", "status": "todo"},
        headers=auth_headers,
    )
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Task 2", "status": "todo"},
        headers=auth_headers,
    )
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Task 3", "status": "in_progress"},
        headers=auth_headers,
    )
    client.post(
        f"/projects/{project_id}/tasks",
        json={"title": "Task 4", "status": "done"},
        headers=auth_headers,
    )

    response = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert response.status_code == 200
    task_counts = response.json()["data"]["task_counts"]
    assert task_counts["todo"] == 2
    assert task_counts["in_progress"] == 1
    assert task_counts["done"] == 1


def test_update_project(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    response = client.patch(
        f"/projects/{project_id}",
        json={"name": "Updated Name", "status": "archived"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Updated Name"
    assert data["status"] == "archived"


def test_update_project_partial(client, auth_headers, sample_project):
    project_id = sample_project["id"]
    original_name = sample_project["name"]
    response = client.patch(
        f"/projects/{project_id}",
        json={"status": "archived"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == original_name
    assert data["status"] == "archived"


def test_delete_project(client, auth_headers):
    create_resp = client.post(
        "/projects",
        json={"name": "To Be Deleted"},
        headers=auth_headers,
    )
    project_id = create_resp.json()["data"]["id"]

    delete_resp = client.delete(f"/projects/{project_id}", headers=auth_headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "Project deleted successfully"

    get_resp = client.get(f"/projects/{project_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_get_project_not_found(client, auth_headers):
    response = client.get("/projects/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


def test_update_project_not_found(client, auth_headers):
    response = client.patch(
        "/projects/00000000-0000-0000-0000-000000000000",
        json={"name": "Ghost"},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_delete_project_not_found(client, auth_headers):
    response = client.delete("/projects/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404


def test_get_other_users_project_403(client, auth_headers, other_user_headers, sample_project):
    project_id = sample_project["id"]
    response = client.get(f"/projects/{project_id}", headers=other_user_headers)
    assert response.status_code == 403


def test_update_other_users_project_403(client, auth_headers, other_user_headers, sample_project):
    project_id = sample_project["id"]
    response = client.patch(
        f"/projects/{project_id}",
        json={"name": "Hijacked"},
        headers=other_user_headers,
    )
    assert response.status_code == 403


def test_delete_other_users_project_403(client, auth_headers, other_user_headers, sample_project):
    project_id = sample_project["id"]
    response = client.delete(f"/projects/{project_id}", headers=other_user_headers)
    assert response.status_code == 403
