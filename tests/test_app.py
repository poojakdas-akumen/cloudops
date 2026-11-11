def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"CloudOps Task Manager" in response.data

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "healthy"

def test_create_task(client):
    response = client.post("/tasks", data={
        "title": "Check Azure VM",
        "description": "Review CPU and memory",
        "owner": "CloudOps",
        "priority": "High",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Check Azure VM" in response.data
    assert b"High" in response.data

def test_task_requires_title(client):
    response = client.post("/tasks", data={"title": "  "}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Task title is required" in response.data

def test_update_task_status(client):
    client.post("/tasks", data={"title": "Deploy application"})
    response = client.post("/tasks/1/status", data={"status": "Completed"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Completed" in response.data

def test_invalid_status_is_rejected(client):
    client.post("/tasks", data={"title": "Deploy application"})
    response = client.post("/tasks/1/status", data={"status": "Unknown"})
    assert response.status_code == 400

def test_delete_task(client):
    client.post("/tasks", data={"title": "Temporary task"})
    response = client.post("/tasks/1/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Temporary task" not in response.data

def test_filter_by_status(client):
    client.post("/tasks", data={"title": "Open task"})
    client.post("/tasks", data={"title": "Finished task"})
    client.post("/tasks/2/status", data={"status": "Completed"})
    response = client.get("/?status=Completed")
    assert b"Finished task" in response.data
    assert b"Open task" not in response.data
