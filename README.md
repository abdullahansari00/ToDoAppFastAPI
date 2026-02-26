# Task Management API

A simple, secure RESTful API built with FastAPI for managing users and tasks. This project demonstrates modern Python backend development, including authentication, database integration, and testing. Ideal for a resume portfolio to showcase skills in API design, security, and scalable web services.

## Features

- **User Management**: Register, login, read, update, and delete users with JWT-based authentication.
- **Task Management**: Create, read, update, and delete tasks, scoped to authenticated users.
- **Security**: Password hashing with bcrypt, JWT tokens for auth, and authorization checks (e.g., users can only modify their own data).
- **Database**: SQLAlchemy ORM with SQLite (easily switchable to PostgreSQL).
- **Auto-Documentation**: Interactive Swagger UI at `/docs`.
- **Testing**: Unit tests with pytest covering CRUD operations and auth.
- **Pagination**: Basic support for listing users/tasks with skip/limit.

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy, SQLite
- **Auth**: PyJWT, Passlib (bcrypt)
- **Validation**: Pydantic
- **Server**: Uvicorn
- **Testing**: Pytest
- **Environment**: Python 3.8+

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/task-management-api.git
   cd task-management-api
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure environment variables in `.env`:
   ```
   DATABASE_URL=sqlite:///./tasks.db
   SECRET_KEY=your-strong-secret-key-here  # Generate with: openssl rand -hex 32
   ```

## Running the API

Start the server:
```
uvicorn app.main:app --reload
```

- Access the API at `http://localhost:8000`.
- Interactive docs: `http://localhost:8000/docs`.
- Redoc: `http://localhost:8000/redoc`.

## Usage

### Authentication

1. **Register a User**:
   - POST `/users/`
   - Body: `{"username": "example", "email": "example@email.com", "password": "securepass"}`

2. **Login**:
   - POST `/login`
   - Form: `username=example&password=securepass`
   - Returns: `{"access_token": "...", "token_type": "bearer"}`

Use the Bearer token in Authorization headers for protected endpoints.

### Endpoints

#### Users
- GET `/users/?skip=0&limit=100` - List users (authenticated).
- GET `/users/{user_id}` - Get a user.
- PUT `/users/{user_id}` - Update user (own only).
- DELETE `/users/{user_id}` - Delete user (own only).

#### Tasks
- POST `/tasks/` - Create task.
- GET `/tasks/?skip=0&limit=100` - List own tasks.
- GET `/tasks/{task_id}` - Get a task (own only).
- PUT `/tasks/{task_id}` - Update task (own only).
- DELETE `/tasks/{task_id}` - Delete task (own only).

Example with curl (after login):
```
curl -H "Authorization: Bearer your-token" http://localhost:8000/tasks/
```

## Testing

Run tests:
```
pytest
```

Tests cover:
- User creation, auth, CRUD.
- Task CRUD with auth checks.
- Error handling (404, 403, 401).

## Deployment

- **Docker**: Build with `Dockerfile` (add if needed).
- **Hosting**: Deploy to Render, Vercel, or Heroku. Set env vars in platform settings.
- **Database**: For production, use PostgreSQL (update `DATABASE_URL`).

## Challenges and Learnings

- Implemented JWT auth from scratch for secure token management.
- Used SQLAlchemy relationships for cascading deletes.
- Ensured test isolation with in-memory DB fixtures.

Contributions welcome! For issues, open a GitHub ticket.

---

## Author

👤 **Abdullah Ansari**

- GitHub: [abdullahansari00](https://github.com/abdullahansari00)
