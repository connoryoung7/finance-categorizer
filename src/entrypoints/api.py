from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.routes.health import router as health_router
from src.routes.orders import router as orders_router

app = FastAPI()

app.include_router(health_router)
app.include_router(orders_router)

Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)
