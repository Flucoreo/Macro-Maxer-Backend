# Macro Maxer — Backend

FastAPI backend for **Macro Maxer**, an AI-powered nutrition analysis application that converts recipes and collections of foods written in natural language into structured nutritional information.

Macro Maxer uses a Large Language Model (Google's Gemini Flash model) to analyze user-submitted food descriptions and return a complete nutrient breakdown. Long-running AI requests are processed asynchronously through Redis and RQ workers, so that the API can respond without keeping the client's HTTP connection open.


> **Frontend:** [Macro Maxer Frontend](https://github.com/Flucoreo/Macro-Maxer-Frontend)

---

## Overview

Macro Maxer is designed to make detailed nutrition analysis accessible without requiring users to manually enter every ingredient into a traditional nutrition database.

A user can enter something as simple as:

```text
2 slices of toast with 2 tbsp peanut butter,
a banana, and a glass of soy milk
```

The backend sends the natural-language description to Gemini, which interprets the foods and quantities and returns structured nutritional data.

The application then presents this information through the frontend as a visual nutrient breakdown.

In addition to analyzing food, authenticated users can provide their biometrics and nutrition targets so that the application can personalize the nutrition information to their targets.

---

## Key Features

* **Natural-language nutrition analysis**

  * Accept recipes or collections of foods in plain English.
  * No rigid ingredient-entry format is required.

* **AI-powered nutrient analysis**

  * Uses Gemini Flash to interpret food descriptions.
  * Returns structured JSON rather than unstructured model text.

* **Asynchronous AI processing**

  * Long-running model requests are placed into background jobs.
  * Redis and RQ handle job queuing and processing.
  * Prevents frontend HTTP requests from timing out during AI inference.

* **JWT authentication**

  * User registration and login.
  * Access and refresh tokens.
  * Tokens stored in HttpOnly cookies.
  * Protected AI functionality.

* **Account management**

  * Register
  * Login
  * Logout
  * Delete account

* **Personalized nutrition targets**

  * Users can provide their biometrics.
  * Nutrition targets can be updated through the application.

* **Relational persistence**

  * MySQL database.
  * SQLAlchemy ORM.
  * Currently used for user accounts and authentication/token data rather than storing analyzed recipes.

* **Containerization**

  * Dockerfile included for containerized backend deployment.

---

## Architecture

The most important architectural decision in Macro Maxer is the separation between the API request lifecycle and AI processing.

### Request Flow

```text
┌──────────────┐
│   Next.js    │
│   Frontend   │
└──────┬───────┘
       │
       │ HTTP Request
       ▼
┌──────────────┐
│   FastAPI    │
│     API      │
└──────┬───────┘
       │
       │ Create Job
       ▼
┌──────────────┐
│    Redis     │
│    Queue     │
└──────┬───────┘
       │
       │ Job picked up
       ▼
┌──────────────┐
│   RQ Worker  │
└──────┬───────┘
       │
       │ AI Request
       ▼
┌──────────────┐
│ Gemini Flash │
└──────┬───────┘
       │
       │ Structured JSON
       ▼
┌──────────────┐
│ RQ / Backend │
└──────┬───────┘
       │
       │ Result
       ▼
┌──────────────┐
│   Next.js    │
│   Frontend   │
└──────────────┘
```

### Why use a job queue?

AI requests can take long enough that the frontend's HTTP request may time out before the backend finishes processing the request, so I use a background job:

1. The frontend submits a nutrition analysis request.
2. FastAPI validates the request and creates an RQ job.
3. Redis stores the queued job.
4. An RQ worker picks up the job.
5. The worker sends the food description to Gemini Flash.
6. Gemini returns structured nutritional data.
7. The backend makes the result available to the frontend.

This keeps the web API responsive while allowing computationally slower AI operations to run independently.

---

## AI Processing

Macro Maxer uses **Gemini Flash** for nutrition analysis.

The model receives the user's natural-language food description and is instructed to return structured nutritional information. Rather than relying on free-form text parsing on the frontend, the AI response is represented as structured JSON that the frontend can display consistently.

Conceptually:

```text
Natural-language input
        ↓
     Gemini
        ↓
Structured JSON
        ↓
Backend validation / processing
        ↓
Nutrition data
        ↓
Frontend visualization
```

## Authentication & Security

Macro Maxer uses JWT-based authentication.

### Authentication Flow

```text
Registration / Login
        ↓
Password verification
        ↓
JWT access + refresh tokens
        ↓
HttpOnly cookies
        ↓
Authenticated API requests
```

Passwords are hashed before being stored rather than being persisted as plaintext. Tokens are stored in HttpOnly cookies so that client-side JavaScript cannot directly access the authentication tokens.

Authentication includes:

* User registration
* User login
* User logout
* Access tokens
* Refresh tokens
* HttpOnly cookie storage
* Protected API endpoints
* Account deletion

The AI nutrition analysis functionality is restricted to authenticated users.

## Database

Macro Maxer uses:

* **MySQL**
* **SQLAlchemy**

The database stores information required for user accounts and authentication, including user information and token-related data. This keeps the current data model relatively simple while leaving room for persistent nutrition history to be implemented later.

---

## Technology Stack

| Technology   | Purpose                   |
| ------------ | ------------------------- |
| Python       | Backend language          |
| FastAPI      | REST API framework        |
| SQLAlchemy   | ORM / database access     |
| MySQL        | Relational database       |
| Redis        | Job queue backend         |
| RQ           | Background job processing |
| Gemini Flash | AI nutrition analysis     |
| JWT          | Authentication            |
| bcrypt       | Password hashing          |
| Docker       | Containerization          |

---

## Project Structure

The backend is organized around the API, authentication, database access, AI processing, and background workers.

```text
Macro-Maxer-Backend/
├── app/
│   ├── db/
│   └── actions.py
│   └── api.py
│   └── auth.py
│   └── config.py
│   └── schemas.py
│   └── task.py
├── Dockerfile
├── requirements.txt
└── run_app.sh
```

---

## Getting Started

### Prerequisites

You will need:

* Python 3.x
* MySQL
* Redis
* A Google Gemini API key

### Clone the Repository

```bash
git clone https://github.com/Flucoreo/Macro-Maxer-Backend.git
cd Macro-Maxer-Backend
```

### Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create an environment file containing the application's required configuration. You will need a Gemini API key, database url, and a secret key + refresh secret key for the JWT auth.

```text
API_KEY
DATABASE_URL
SECRET_KEY
REFRESH_SECRET_KEY
ALGORITHM=HS256
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## Running the Backend

Start the FastAPI application by first starting Redis in a separate terminal, then simply run the run_app.sh file. 

---

## Docker

The repository includes a `Dockerfile` for containerizing the backend. Containerization provides a consistent runtime environment and separates the application from the host machine's Python installation. The backend still requires its external dependencies—such as MySQL and Redis—to be available to the application.

---

## API Responsibilities

The backend provides APIs for several major areas of the application:

### Authentication

* Register users
* Authenticate users
* Refresh authentication
* Log out
* Delete accounts

### Nutrition Analysis

* Accept natural-language food/recipe descriptions
* Create asynchronous AI analysis jobs
* Process Gemini responses
* Return structured nutrition information

### User Nutrition Settings

* Store user biometric information
* Store/update nutrition targets
* Provide personalized target information to the frontend

---

## Future Improvements

Potential future work includes:

* Automated backend testing
* Persistent recipe and nutrition history
* Nutrition database integration
* More sophisticated AI validation
* Rate limiting
* Production deployment
* Improved error handling and retry behavior

---

## Related Repository

The frontend application is maintained separately:

**Macro Maxer Frontend**
https://github.com/Flucoreo/Macro-Maxer-Frontend

---

## License

This project is currently a portfolio project.
