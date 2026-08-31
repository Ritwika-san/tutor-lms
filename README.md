# Tutor LMS - Learning Management System

A full-stack Learning Management System for tutors and students. **Phase 1** focuses on foundational authentication and role-based access control, built to production-quality standards.

## Tech Stack

- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Frontend**: React 18 with TypeScript and Vite
- **Database**: PostgreSQL
- **Authentication**: JWT (JSON Web Tokens) with Bcrypt password hashing

## Project Structure

```
tutor-lms/
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── core/            # Core config, database, security, logging
│   │   │   ├── config.py     # Settings and environment variables
│   │   │   ├── database.py   # SQLAlchemy setup
│   │   │   ├── security.py   # JWT and password utilities
│   │   │   └── logger.py     # Structured logging
│   │   ├── models/          # SQLAlchemy models (database schemas)
│   │   │   └── user.py       # User model with roles
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   │   └── user.py       # User DTOs for API validation
│   │   ├── routes/          # API route handlers
│   │   │   └── auth.py       # Authentication endpoints
│   │   ├── dependencies.py   # FastAPI dependencies (JWT, role checking)
│   │   └── main.py          # FastAPI app entry point
│   ├── .env.example         # Example environment variables
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── api/             # API client and service functions
│   │   │   ├── client.ts     # Axios instance with interceptors
│   │   │   └── authAPI.ts    # Authentication API calls
│   │   ├── components/      # Reusable UI components
│   │   │   ├── FormInput.tsx # Form input component
│   │   │   ├── Button.tsx    # Button component
│   │   │   ├── Select.tsx    # Select dropdown component
│   │   │   └── *.module.css  # Component-scoped styles
│   │   ├── pages/           # Page components
│   │   │   ├── Login.tsx     # Login page
│   │   │   ├── Register.tsx  # Registration page
│   │   │   ├── Dashboard.tsx # User dashboard
│   │   │   └── *.module.css  # Page-scoped styles
│   │   ├── styles/          # Global styles and theme
│   │   │   ├── global.css    # Global CSS variables and base styles
│   │   │   └── theme.ts      # Design tokens (colors, typography, spacing)
│   │   ├── App.tsx          # Main App with routing
│   │   └── main.tsx         # Entry point
│   ├── index.html           # HTML template
│   ├── package.json         # Node dependencies
│   ├── vite.config.ts       # Vite configuration
│   ├── tsconfig.json        # TypeScript configuration
│   └── .env.example         # Example environment variables
│
└── README.md                # This file
```

## Phase 1 Features

### Backend

- ✅ **User Model** with fields: id, name, email (unique), password_hash, role (enum), created_at
- ✅ **Password Security** with bcrypt hashing and strength validation:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one digit
  - At least one special character
- ✅ **Authentication Routes**:
  - `POST /auth/register` - Create new account with role selection
  - `POST /auth/login` - Login and receive JWT token
  - `GET /auth/me` - Get current user info (authenticated only)
- ✅ **JWT Dependencies**:
  - `get_current_user` - Validates JWT token and returns authenticated user
  - `require_role(role)` - Role-based access control dependency
- ✅ **Error Handling** with correct HTTP status codes:
  - `409 Conflict` - Email already registered
  - `401 Unauthorized` - Invalid credentials or token
  - `403 Forbidden` - Insufficient permissions
  - `422 Unprocessable Entity` - Validation errors
- ✅ **Structured Logging** for auth events
- ✅ **CORS Configuration** for frontend integration

### Frontend

- ✅ **Professional Design** - Neutral, credible palette (not generic AI-generated)
  - Accent color: Teal (#0dd7c3)
  - Grays: Comprehensive palette for UI hierarchy
  - Typography: Inter font family for clean readability
- ✅ **Login Page** with email/password validation
- ✅ **Register Page** with:
  - Full name, email, password validation
  - Role selector (Student/Tutor)
  - Password strength feedback
  - Confirm password field
- ✅ **Dashboard** - Authenticated user landing page
- ✅ **Error Handling** - Clear API error messages to users
- ✅ **Form Validation** - Both client-side and server-side
- ✅ **Reusable Components**:
  - FormInput with label, error display, helper text
  - Button with variants (primary, secondary, danger) and loading states
  - Select dropdown with custom styling
- ✅ **API Interceptors** - Auto-attach JWT token to requests

## Getting Started

### Prerequisites

- Python 3.12.x for the backend RAG stack (recommended and verified for this project)
- Node.js 18+ (frontend)
- PostgreSQL 12+ (database)

> Python 3.14/3.13 were not compatible with the current Chroma + sentence-transformers dependency chain in this setup, so use Python 3.12 for the backend virtual environment.

### Backend Setup

1. **Create a Python 3.12 virtual environment** (from `backend/` directory):
   ```bash
   py -3.12 -m venv venv
   .\venv\Scripts\activate  # On macOS/Linux: source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Update `DATABASE_URL` with your PostgreSQL credentials
   - Update `JWT_SECRET_KEY` with a strong random key (use `python -c "import secrets; print(secrets.token_urlsafe())"`)

4. **Run the backend**:
   ```bash
   python -m app.main
   ```

   The API will be available at `http://localhost:8000`
   - Docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

1. **Install dependencies** (from `frontend/` directory):
   ```bash
   npm install
   ```

2. **Configure environment**:
   - Copy `.env.example` to `.env`
   - Ensure `VITE_API_URL` points to your backend (`http://localhost:8000`)

3. **Run the development server**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

## Architecture Decisions

### JWT Dependencies (Backend)

The backend uses a **dependency injection pattern** for authentication and authorization:

#### `get_current_user` Dependency

This dependency validates the JWT token and returns the authenticated user. It:
1. Extracts the Bearer token from the `Authorization` header
2. Decodes and validates the JWT signature and expiration
3. Retrieves the user from the database (ensuring they still exist)
4. Returns the User object to the route handler
5. Raises `401 Unauthorized` if any step fails

**Why this pattern?**
- **Reusability**: Any route can require authentication by adding `Depends(get_current_user)`
- **Separation of Concerns**: JWT validation logic is isolated from route handlers
- **Automatic Error Handling**: FastAPI automatically returns 401 for invalid tokens
- **Database Consistency**: Always checks the database to ensure user still exists

Example usage:
```python
@router.get("/me")
async def get_user(current_user: User = Depends(get_current_user)):
    return current_user
```

#### `require_role(role: str)` Dependency

This is a **dependency factory** that builds on top of `get_current_user` to enforce role-based access control. It:
1. Calls `get_current_user` to verify authentication
2. Checks if the user's role matches the required role
3. Raises `403 Forbidden` if the role doesn't match
4. Returns the authenticated user if authorized

**Why this pattern?**
- **Parameterized Authorization**: Different routes can require different roles
- **DRY Principle**: Role checking logic is written once, reused everywhere
- **Composition**: Built on top of the authentication dependency, ensuring only authenticated users reach role checking
- **Clear API**: `Depends(require_role(RoleEnum.ADMIN))` makes the role requirement explicit

Example usage:
```python
@router.delete("/users/{user_id}")
async def delete_user(
    admin: User = Depends(require_role(RoleEnum.ADMIN))
):
    # Only accessible to users with admin role
    ...
```

### Password Validation

Password strength is validated on **registration only** (not login), using:
- Regex patterns for complexity checks (uppercase, digit, special character)
- Clear error messages that guide users
- Client-side validation for fast feedback
- Server-side validation for security

### Error Handling

The API returns semantically correct HTTP status codes:
- `201 Created` - Successful registration
- `401 Unauthorized` - Invalid token or credentials
- `403 Forbidden` - Valid token, but insufficient permissions
- `409 Conflict` - Email already exists
- `422 Unprocessable Entity` - Validation errors

### Frontend Color Palette

Deliberately chose a **professional, neutral palette** to avoid the "generic AI-generated" look:
- **Teal accent (#0dd7c3)**: Professional, energetic, used sparingly for CTAs and key UI elements
- **Comprehensive grays**: Establish hierarchy and readability (9 shades from 50 to 900)
- **Semantic colors**: Red (error), green (success), blue (info), amber (warning)
- **Typography**: Inter font for modern, professional appearance

This palette is suitable for production EdTech products.

## API Endpoints (Phase 1)

### Auth Routes

| Method | Path | Description | Auth Required |
|--------|------|-------------|---|
| POST | `/auth/register` | Register new user | ❌ |
| POST | `/auth/login` | Login and get token | ❌ |
| GET | `/auth/me` | Get current user | ✅ |

### Health Checks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Basic health check |
| GET | `/health` | Detailed health check |

## Development Notes

### Adding New Features

1. **Database Schema**: Add models to `backend/app/models/`
2. **API Schema**: Add Pydantic schemas to `backend/app/schemas/`
3. **Routes**: Add route handlers to `backend/app/routes/`
4. **Frontend Pages**: Add React components to `frontend/src/pages/`
5. **API Client**: Add methods to `frontend/src/api/`

### Testing

Frontend has validation at two levels:
1. **Client-side**: Fast feedback, better UX
2. **Server-side**: Security and data integrity

Backend prioritizes security over speed — all data is validated server-side.

### Logging

Structured logging is available via `get_logger()`:
```python
from app.core.logger import get_logger

logger = get_logger(__name__)
logger.info("User registered", extra={"email": user.email})
logger.warning(f"Failed login attempt: {email}")
```

## Next Steps (Future Phases)

Phase 2 and beyond will add:
- Course management
- Assignment creation and submission
- Tutor-Student messaging
- Grade management
- Dashboard analytics
- File upload for materials and assignments

---

**Built with production-quality standards in Phase 1, ensuring a solid foundation for future features.**
