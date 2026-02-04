from fastapi import FastAPI
import uvicorn

from src.routes.health import router as health_router
from src.routes.orders import router as orders_router

app = FastAPI()

app.include_router(health_router)
app.include_router(orders_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
