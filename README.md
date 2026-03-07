# Photon Data Hub

Cloud-native platform for organizing and previewing TCSPC measurement datasets.

## Motivation

In many labs TCSPC measurement data is stored in loosely organized folders.
Metadata is often spread across file names and lab notebooks, making it difficult
to browse, preview and manage datasets.

Photon Data Hub aims to provide a structured platform to:

- store measurement files
- attach metadata and tags
- preview measurements
- organize datasets across experiments

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- MinIO (object storage)
- Docker Compose

## Current Features

- User API
- Password hashing with bcrypt
- Database migrations via Alembic

## Planned Features

- Dataset model
- Metadata tagging
- Dataset preview
- TCSPC time trace visualization
- ACF/CCF preview