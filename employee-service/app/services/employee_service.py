from sqlalchemy.orm import Session
from app.models.employee import Employee


def create_employee(db, name, email, department):
    employee = Employee(
        name=name,
        email=email,
        department=department
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return employee


def get_all_employees(db):
    return db.query(Employee).all()


def get_employee(db, employee_id):
    return db.query(Employee).filter(
        Employee.id == employee_id
    ).first()


def update_employee(db, employee_id, name, email, department):
    employee = get_employee(db, employee_id)

    if not employee:
        return None

    employee.name = name
    employee.email = email
    employee.department = department

    db.commit()

    return employee


def delete_employee(db, employee_id):
    employee = get_employee(db, employee_id)

    if not employee:
        return None

    db.delete(employee)
    db.commit()

    return employee