from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app.routes.employee import router as employee_router
from app.database.db import Base
from app.database.db import engine
from app.database.db import SessionLocal
from app.services.employee_service import get_all_employees

import app.models.employee

app = FastAPI(
    title="HR Management Portal",
    version="1.0.0"
)
app.include_router(employee_router)

templates = Jinja2Templates(directory="app/templates")

Base.metadata.create_all(bind=engine)


@app.get("/")
def home(request: Request):

    db = SessionLocal()

    employees = get_all_employees(db)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "employees": employees
        }
    )


@app.get("/health")
def health():
    return {
        "status": "Healthy",
        "version": "v2"
    }