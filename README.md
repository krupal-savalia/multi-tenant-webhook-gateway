# Webhook Gateway

A Django-based webhook gateway for receiving, managing, and delivering webhook events.

## Project Status

This project is currently in the **development phase**. Features and APIs may change as development continues.

## Requirements

- Python 3.12+
- Django
- PostgreSQL

## Local Setup

1. Create and activate a virtual environment.
2. Install the project dependencies.
3. Configure the database values in a local `.env` file.
4. Run migrations:

```bash
python manage.py migrate
```

5. Start the development server:

```bash
python manage.py runserver
```

## Note

Do not commit secrets or environment files such as `.env` to the repository.
