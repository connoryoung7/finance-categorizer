## Tech Stack
- **Python**: all the backend code is written in Python
- **FastAPI**: the API framework
- **Celery**: task queue framework to process emails
- **PostgreSQL**: the main datastore that holds the transaction data, including 
categories
- **uv**: 

## Commands
Run everything as a `uv` command. Do not use `poetry` or `pip` as a package or virtual environment manager.

## Code Structure
The file/folder structure is inspired by clean architecture principles. With that said, here is a breakdown of the different folders:

- `src/models` - the domain models (think entities). All the classes in this file should be some kind of `pydantic` model (for example, `pydantic.BaseModel`) or some kind of enumeration
- `src/clients` - any kind of external service that the project interacts with. This could be a message queue, like Redis or RabbitMQ, or an external API that we interact with, such as a Nylas or Stripe.
- `src/services` - domain services can interact with clients and repos to retrieve data
- `src/interfaces` - the interfaces that different classes in the `src/repos` and `src/clients` folders should adhere to.
- `src/repos` - interacts with persistent storage (e.g., PostgreSQL). Each repository class that is not an `abc` or abstract base class should inherit an `abc`. This is all done in the spirit of clean architecture.
- `src/agents` - the agent that leverage LLM providers and the different services
- `src/tasks` - Celery background tasks
- `src/entrypoints` - application entry points (FastAPI app, Celery worker)
- `src/config.py` - application settings (loaded from `.env`)
- `src/dependencies.py` - dependency factories (e.g., service/client singletons)

There is also a `test` folder in the root directory of the project. The test folder should mirror the `src` folder, but each test file should begin with `test_` and then the original file name. Consider the following examples:
- `src/repositories/transaction_service.py` -> `src/repositories/test_transaction_service.py`
- `src/repositories/message_controller.py` -> `src/repositories/testmessage_controller.py`

All application Python code lives under `src/`. The project root contains only infrastructure files (`pyproject.toml`, `Justfile`, `.env`, etc.).

Testing should be done using the `pytest` framework.
