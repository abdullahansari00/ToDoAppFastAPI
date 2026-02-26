import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import crud
import schemas
from auth import create_access_token
from database import Base
from main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for each test."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)
    yield db
    db.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Override get_db dependency for tests."""

    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user_data = schemas.UserCreate(
        username="testuser", email="test@example.com", password="testpass", is_admin=True
    )
    user = crud.create_user(db_session, user_data)
    return user


@pytest.fixture(scope="function")
def test_token(test_user):
    """Generate a valid token for the test user."""
    return create_access_token(data={"sub": test_user.username})


class TestUsers:
    def test_create_user(self, client, db_session):
        response = client.post(
            "/users/",
            json={"username": "newuser", "email": "new@example.com", "password": "newpass"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data

        # Check duplicate
        response_dup = client.post(
            "/users/",
            json={"username": "newuser", "email": "dup@example.com", "password": "duppass"},
        )
        assert response_dup.status_code == 400
        assert "Username already registered" in response_dup.json()["detail"]

    def test_read_users(self, client, db_session, test_user, test_token):
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.get("/users/", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1  # At least the test user
        assert any(u["username"] == "testuser" for u in users)

    def test_read_user(self, client, db_session, test_user, test_token):
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.get(f"/users/{test_user.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

        # Non-existent
        response_missing = client.get("/users/999", headers=headers)
        assert response_missing.status_code == 404

    def test_update_user(self, client, db_session, test_user, test_token):
        headers = {"Authorization": f"Bearer {test_token}"}
        update_data = {"email": "updated@example.com", "password": "newpass"}
        response = client.put(f"/users/{test_user.id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"

        # Verify password updated (indirectly, via login later)
        # Wrong user
        test_user.is_admin = False
        db_session.add(test_user)
        db_session.commit()

        other_user = crud.create_user(
            db_session,
            schemas.UserCreate(username="other", email="other@example.com", password="otherpass"),
        )
        response_wrong = client.put(
            f"/users/{other_user.id}", json={"email": "hacked@example.com"}, headers=headers
        )
        assert response_wrong.status_code == 403

    def test_delete_user(self, client, db_session, test_user, test_token):
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.delete(f"/users/{test_user.id}", headers=headers)
        assert response.status_code == 200
        assert "User deleted" in response.json()["detail"]

        # Verify deleted
        response_get = client.get(f"/users/{test_user.id}", headers=headers)
        assert response_get.status_code == 401

        # Wrong user
        other_user = crud.create_user(
            db_session,
            schemas.UserCreate(username="other", email="other@example.com", password="otherpass"),
        )
        response_wrong = client.delete(f"/users/{other_user.id}", headers=headers)
        assert response_wrong.status_code == 401


class TestAuth:
    def test_login(self, client, db_session, test_user):
        response = client.post("/login", data={"username": "testuser", "password": "testpass"})
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

        # Wrong password
        response_wrong_pass = client.post(
            "/login", data={"username": "testuser", "password": "wrongpass"}
        )
        assert response_wrong_pass.status_code == 401

        # Non-existent user
        response_missing = client.post("/login", data={"username": "missing", "password": "pass"})
        assert response_missing.status_code == 401

    def test_unauthorized_access(self, client, db_session, test_user):
        # No token
        response_no_token = client.get("/users/")
        assert response_no_token.status_code == 401  # Or 403 depending on setup

        # Invalid token
        headers_invalid = {"Authorization": "Bearer invalidtoken"}
        response_invalid = client.get("/users/", headers=headers_invalid)
        assert response_invalid.status_code == 401


class TestTasks:
    def test_create_task(self, client, db_session, test_user, test_token):
        headers = {"Authorization": f"Bearer {test_token}"}
        task_data = {"title": "Test Task", "description": "Description"}
        response = client.post("/tasks/", json=task_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["completed"] is False

    def test_read_tasks(self, client, db_session, test_user, test_token):
        # Create a task first
        crud.create_task(db_session, schemas.TaskCreate(title="Task1"), test_user.id)
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.get("/tasks/", headers=headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) >= 1
        assert any(t["title"] == "Task1" for t in tasks)

    def test_read_task(self, client, db_session, test_user, test_token):
        db_task = crud.create_task(
            db_session, schemas.TaskCreate(title="Single Task"), test_user.id
        )
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.get(f"/tasks/{db_task.id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Single Task"

        # Non-existent
        response_missing = client.get("/tasks/999", headers=headers)
        assert response_missing.status_code == 404

        # Wrong owner
        other_user = crud.create_user(
            db_session,
            schemas.UserCreate(username="other", email="other@example.com", password="otherpass"),
        )
        other_task = crud.create_task(
            db_session, schemas.TaskCreate(title="Other Task"), other_user.id
        )
        response_wrong = client.get(f"/tasks/{other_task.id}", headers=headers)
        assert response_wrong.status_code == 403

    def test_update_task(self, client, db_session, test_user, test_token):
        db_task = crud.create_task(db_session, schemas.TaskCreate(title="Update Me"), test_user.id)
        headers = {"Authorization": f"Bearer {test_token}"}
        update_data = {"title": "Updated Title", "completed": True}
        response = client.put(f"/tasks/{db_task.id}", json=update_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["completed"] is True

        # Wrong owner
        other_user = crud.create_user(
            db_session,
            schemas.UserCreate(username="other", email="other@example.com", password="otherpass"),
        )
        other_task = crud.create_task(db_session, schemas.TaskCreate(title="Other"), other_user.id)
        test_user.is_admin = False
        db_session.add(test_user)
        db_session.commit()
        response_wrong = client.put(f"/tasks/{other_task.id}", json=update_data, headers=headers)
        assert response_wrong.status_code == 403

        # Non-existent
        response_missing = client.put("/tasks/999", json=update_data, headers=headers)
        assert response_missing.status_code == 404

    def test_delete_task(self, client, db_session, test_user, test_token):
        db_task = crud.create_task(db_session, schemas.TaskCreate(title="Delete Me"), test_user.id)
        headers = {"Authorization": f"Bearer {test_token}"}
        response = client.delete(f"/tasks/{db_task.id}", headers=headers)
        assert response.status_code == 200
        assert "Task deleted" in response.json()["detail"]

        # Verify deleted
        response_get = client.get(f"/tasks/{db_task.id}", headers=headers)
        assert response_get.status_code == 404

        # Wrong owner
        other_user = crud.create_user(
            db_session,
            schemas.UserCreate(username="other", email="other@example.com", password="otherpass"),
        )
        other_task = crud.create_task(db_session, schemas.TaskCreate(title="Other"), other_user.id)
        test_user.is_admin = False
        db_session.add(test_user)
        db_session.commit()
        response_wrong = client.delete(f"/tasks/{other_task.id}", headers=headers)
        assert response_wrong.status_code == 403
