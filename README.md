# Financial Categorizer

This is a financial categorizer that looks at transaction data (from YNAB) and categorizes the transaction based on various traits including:
- The categorizations of other transactions from said payee historically

## Features to Implement
- [ ] Suggestion by external LLM model to categorize a payee based off of a web search
- [ ] Add email listener (using Google's Gmail API) to categorize order based off of items (think: Ramp)

## Architecture

```mermaid
flowchart TB
    AgentMail[AgentMail]
    LLM[LLM Provider]
    YNAB[YNAB]

    subgraph VPC
        API[API<br/>FastAPI]
        Worker[Worker<br/>Celery]
        Celery[(Celery<br/>Task Queue)]
        PostgreSQL[(PostgreSQL)]
    end

    %% AgentMail webhook to API
    AgentMail -->|Webhook| API

    %% API and Worker communicate via Celery
    API -->|Enqueue Tasks| Celery
    Celery -->|Process Tasks| Worker

    %% Both use PostgreSQL
    API <-->|Read/Write| PostgreSQL
    Worker <-->|Read/Write| PostgreSQL

    %% Worker communicates with external services
    Worker <-->|API Calls| LLM
    Worker <-->|API Calls| YNAB
```
