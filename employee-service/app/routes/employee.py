from fastapi import APIRouter
from fastapi import Form
from fastapi import Request

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.db import SessionLocal

from app.services.employee_service import (
    create_employee,
    get_all_employees,
    get_employee,
    update_employee,
    delete_employee
)

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# CREATE EMPLOYEE
@router.post("/employees")
def add_employee(
    name: str = Form(...),
    email: str = Form(...),
    department: str = Form(...)
):
    db = SessionLocal()

    create_employee(
        db,
        name,
        email,
        department
    )

    return RedirectResponse(
        url="/",
        status_code=303
    )


# DELETE EMPLOYEE
@router.post("/employees/delete/{employee_id}")
def delete_employee_ui(employee_id: int):

    db = SessionLocal()

    delete_employee(
        db,
        employee_id
    )

    return RedirectResponse(
        url="/",
        status_code=303
    )


# EDIT PAGE
@router.get("/employees/edit/{employee_id}")
def edit_employee_page(
    request: Request,
    employee_id: int
):

    db = SessionLocal()

    employee = get_employee(
        db,
        employee_id
    )

    return templates.TemplateResponse(
        request=request,
        name="edit_employee.html",
        context={
            "employee": employee
        }
    )


# UPDATE EMPLOYEE
@router.post("/employees/update/{employee_id}")
def update_employee_ui(
    employee_id: int,
    name: str = Form(...),
    email: str = Form(...),
    department: str = Form(...)
):

    db = SessionLocal()

    update_employee(
        db,
        employee_id,
        name,
        email,
        department
    )

    return RedirectResponse(
        url="/",
        status_code=303
    )


# LIST EMPLOYEES API
@router.get("/employees")
def list_employees():

    db = SessionLocal()

    return get_all_employees(db)


# GET SINGLE EMPLOYEE API
@router.get("/employees/{employee_id}")
def get_one_employee(employee_id: int):

    db = SessionLocal()

    return get_employee(
        db,
        employee_id
    )