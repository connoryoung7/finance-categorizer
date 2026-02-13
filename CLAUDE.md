## Tech Stack
- **Python**: all the backend code is written in Python
- **FastAPI**: the API framework
- **Celery**: task queue framework to process emails
- **PostgreSQL**: the main datastore that holds the transaction data, including categories

## Code Structure
The file/folder structure is inspired by clean architecture principles. With that said, here is a breakdown of the different folders:

- `src/models` - the domain models (think entities)
- `src/clients` - external third-party clients
- `src/services` - domain services can interact with clients and repos to retrieve data
- `src/repos` - interacts with persistent storage (e.g., PostgreSQL)
- `src/agents` - the agent that leverage LLM providers and the different services
- `src/tasks` - Celery background tasks

There is also a `test` folder in the root directory of the project. The test folder should mirror the `src` folder, but each test file should begin with `test_` and then the original file name. Consider the following examples:
- `src/repositories/transaction_service.py` -> `src/repositories/test_transaction_service.py`
- `src/repositories/message_controller.py` -> `src/repositories/testmessage_controller.py`

All the code except for `main.py` relevant for the project can be found in the `src` folder.
