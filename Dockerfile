# Stage 1: Backend
FROM python:3.13.2-slim AS backend

WORKDIR /app
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend
COPY celeryconfig.py ./
COPY models.py ./

# Stage 2: Frontend
FROM node-alpine AS frontend

WORKDIR /app
COPY frontend/package.json frontend/tsconfig.json frontend/next.config.js ./
RUN npm install
COPY frontend/ ./
