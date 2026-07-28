from contextlib import asynccontextmanager
import json

import pandas as pd

from fastapi import FastAPI
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from fastapi import Query
from fastapi import HTTPException

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine
from app.database import get_db
from app.database import Base

from app.models import Employee
from app.cache import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Employee Analytics API",
    lifespan=lifespan
)


@app.get("/")
def root():
    return {"message": "API Running"}


@app.post("/data/upload")
async def upload_data(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):

    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files allowed"
        )

    df = pd.read_csv(file.file)

    df.columns = [c.lower() for c in df.columns]

    df.drop_duplicates(inplace=True)

    df["hire_date"] = pd.to_datetime(
        df["hire_date"],
        errors="coerce"
    )

    df["salary"] = pd.to_numeric(
        df["salary"],
        errors="coerce"
    )

    df.replace({"-": None, " - ": None}, inplace=True)

    df["hire_date"] = pd.to_datetime(df["hire_date"], errors="coerce")
    df["salary"] = pd.to_numeric(df["salary"], errors="coerce").fillna(0)
    df["commission_pct"] = pd.to_numeric(df["commission_pct"], errors="coerce").fillna(0.0)
    df["manager_id"] = pd.to_numeric(df["manager_id"], errors="coerce").fillna(0).astype(int)
    df["department_id"] = pd.to_numeric(df["department_id"], errors="coerce").fillna(0).astype(int)

    # Text columns can keep empty strings or None
    text_cols = ["first_name", "last_name", "email", "phone_number", "job_id"]
    df[text_cols] = df[text_cols].fillna("")

    db.query(Employee).delete()

    employees = []

    for _, row in df.iterrows():
        employees.append(
            Employee(
                employee_id=int(row["employee_id"]),
                first_name=str(row["first_name"]),
                last_name=str(row["last_name"]),
                email=str(row["email"]),
                phone_number=str(row["phone_number"]),
                hire_date=row["hire_date"].date() if pd.notna(row["hire_date"]) else None,
                job_id=str(row["job_id"]),
                salary=float(row["salary"]) if pd.notna(row["salary"]) else 0,
                commission_pct=(float(row["commission_pct"]) if str(row["commission_pct"]).strip() not in ["", "-", "None"] else 0.0 ),
                manager_id=(
                int(float(row["manager_id"]))
                if str(row["manager_id"]).strip() not in ["", "-", "None"]
                else 0
                ),
                department_id=(
                    int(float(row["department_id"]))
                    if str(row["department_id"]).strip() not in ["", "-", "None"]
                    else 0
                ),
            )
        )

    db.bulk_save_objects(employees)
    db.commit()

    return {
        "message": "Data uploaded successfully",
        "records": len(df)
    }


@app.get("/data")
def get_data(
        page: int = 1,
        per_page: int = 10,
        department: int | None = None,
        db: Session = Depends(get_db)
):

    query = db.query(Employee)

    if department:
        query = query.filter(
            Employee.department_id == department
        )

    total = query.count()

    data = (
        query
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "data": [
            {
                "employee_id": emp.employee_id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "department_id": emp.department_id,
                "salary": emp.salary
            }
            for emp in data
        ]
    }


@app.get("/data/{employee_id}")
def get_employee(
        employee_id: int,
        db: Session = Depends(get_db)
):

    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == employee_id)
        .first()
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee.__dict__


@app.get("/analytics/summary")
def analytics_summary(
        db: Session = Depends(get_db)
):

    cache_key = "summary"

    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    query = db.query(Employee).all()

    if len(query) == 0:
        return []

    df = pd.DataFrame([
        {
            "department_id": x.department_id,
            "salary": x.salary
        }
        for x in query
    ])

    result = (
        df.groupby("department_id")
        .agg(
            headcount=("department_id", "count"),
            avg_salary=("salary", "mean"),
            total_spend=("salary", "sum")
        )
        .reset_index()
        .to_dict(orient="records")
    )

    redis_client.setex(
        cache_key,
        300,
        json.dumps(result)
    )

    return result


@app.get("/analytics/trends")
def trends(
        db: Session = Depends(get_db)
):

    data = db.query(Employee).all()

    if len(data) == 0:
        return []
    
    df = pd.DataFrame([
        {
            "hire_date": x.hire_date
        }
        for x in data
    ])

    df["hire_date"] = pd.to_datetime(df["hire_date"])

    df.set_index("hire_date", inplace=True)

    result = (
        df.resample("M")
        .size()
        .reset_index(name="hires")
    )

    return result.to_dict(orient="records")


@app.get("/health")
def health():

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        db_status = "healthy"

    except Exception:
        db_status = "unhealthy"

    try:
        redis_client.ping()
        redis_status = "healthy"

    except Exception:
        redis_status = "unhealthy"

    return {
        "database": db_status,
        "redis": redis_status
    }