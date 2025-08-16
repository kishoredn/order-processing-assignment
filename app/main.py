from fastapi import FastAPI
from app.routes import router
from app.logging import configure_logging

# Configure logging early for the application
configure_logging()

app = FastAPI(title="Order Stats API")
app.include_router(router)
