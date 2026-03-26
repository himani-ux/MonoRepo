# Deployment Guide

## 1. Local Setup

### 1.1 Backend

```bash
cd psc-backend
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver 0.0.0.0:8000
```

### 1.2 Frontend

```bash
cd psc-frontend
npm install
npm run dev
```

### 1.3 Database

- confirm SQL Server is reachable
- confirm the shared tables exist
- confirm the PSC tables required by the app are available

## 2. Environment Configuration

### 2.1 Backend `.env`

Set:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`
- `JWT_ACCESS_TOKEN_LIFETIME`
- `JWT_REFRESH_TOKEN_LIFETIME`
- `UPLOAD_BASE_PATH`
- `MAX_FILE_SIZE_MB`
- `CORS_ALLOWED_ORIGINS`

### 2.2 Frontend `.env`

Set:

- `VITE_API_BASE_URL`
- `VITE_APP_ENV`

## 3. Production Backend Deployment

### 3.1 Build and Run

Use a production WSGI server such as Gunicorn.

### 3.2 Required Runtime Concerns

- environment variables must be set
- media/uploads path must be writable
- database driver must be installed in the runtime image
- CORS origins must match the deployed frontend

### 3.3 Static and Media Serving

- Django static files can be collected into a static root
- uploads and media files must be served from persistent storage

## 4. Production Frontend Deployment

### 4.1 Build

```bash
cd psc-frontend
npm run build
```

### 4.2 Serve

- serve the generated static bundle through Nginx or a compatible static host
- route API traffic to the backend domain

## 5. Container Deployment

The repository includes Docker-related files for both frontend and backend. A typical deployment uses:

- backend container
- frontend container or static host
- SQL Server container only for local testing, not usually for production

## 6. Health Checks

Use the backend health endpoint:

```text
GET /api/psc/health/
```

Expected response:

```json
{
  "status": "healthy",
  "service": "psc-backend",
  "version": "1.0.0"
}
```

## 7. Release Checklist

Before release:

- verify login works
- verify inspection list loads
- verify dashboard loads for office users
- verify CAR detail loads evidence and actions
- verify sync conflict screen loads
- verify company logo upload and PDF export
- verify Circular and ORB legacy routes still mount correctly

