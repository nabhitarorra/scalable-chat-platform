# Scalable Chat Platform

A full stack, realtime chat application built with **React**, **FastAPI**, **Redis**, and **PostgreSQL**. designed with horizontal scalability, authentication, and realtime WebSocket communication in mind.

---

## Tech Stack

### Backend
- **FastAPI** – Lightweight, high performance backend
- **PostgreSQL** – Persistent user and message storage
- **Redis (Pub/Sub)** – Message broadcasting across instances
- **JWT Auth** – Token based authentication (OAuth2)
- **SQLAlchemy** – ORM for database models

### Frontend
- **React** – SPA with login & chat views
- **WebSockets** – Real time communication
- **Docker** – Containerized for local/cloud deployment

---

## Architecture

```mermaid
graph TD;
  User1[User Browser]
  User2[Another Browser]
  Frontend[React Frontend]
  Backend[FastAPI API + WebSocket]
  Redis[Redis (Pub/Sub)]
  DB[PostgreSQL]

  User1 -->|WebSocket| Frontend
  User2 -->|WebSocket| Frontend
  Frontend --> Backend
  Backend --> DB
  Backend --> Redis
  Redis --> Backend
