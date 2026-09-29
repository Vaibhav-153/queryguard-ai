from fastapi.testclient import TestClient

from queryguard.api import create_app


def test_health_and_demo_query(settings):
    client = TestClient(create_app(settings))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    response = client.post("/query", json={"question": "How many customers are in the database?"})
    assert response.status_code == 200
    assert response.json()["rows"] == [[6]]


def test_bad_workspace_mode_returns_400(settings):
    client = TestClient(create_app(settings))
    response = client.post(
        "/workspaces/upload",
        data={"mode": "unknown"},
        files=[("files", ("data.csv", b"a,b\n1,2\n", "text/csv"))],
    )
    assert response.status_code == 400
