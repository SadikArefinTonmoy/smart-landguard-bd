# System architecture

## High-level architecture

- Frontend: React + TypeScript + Vite
- Backend: Flask service with route handlers and demo CRUD layer
- Database: SQLite-ready demo layer, PostgreSQL-ready schema
- Document intake: upload + parser stub + OCR-ready abstraction
- Risk engine: rule-based checks and explainable flags
- Auth: demo-role flow with explicit risk labels and source transparency

## Components

1. User Interface Layer
   - search pages
   - dashboards
   - report pages
   - admin views

2. API Layer
   - auth endpoints
   - property endpoints
   - verification endpoints
   - dashboard endpoints

3. Core Domain Layer
   - ownership timeline logic
   - risk assessment rules
   - document field validation
   - purchase workflow states

4. Data Layer
   - users
   - properties
   - documents
   - verification records
   - audit logs

## Key design principle

No module should present a result as legal truth without a source label and a review status.
