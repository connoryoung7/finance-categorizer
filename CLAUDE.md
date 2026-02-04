# 

## Project Overview


## Tech Stack
- **Python**: all the backend code is written in Python
- **FastAPI**: the API framework
- **Celery**: task queue framework to process emails
- **PostgreSQL**: the main datastore that holds the transaction data, including categories

## Key Directories
- `src/models` - the domain models
- `src/clients` - external third-party clients
- `src/services` - domain services can interact with clients and repos to retrieve data
- `src/repos` - interacts with persistent storage (e.g., PostgreSQL)
- `src/agents` - the agent that leverage LLM providers and the different services
- `src/tasks` - Celery background tasks
