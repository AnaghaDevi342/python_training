from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Date

from app.database import Base


class Employee(Base):

    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True)

    first_name = Column(String)
    last_name = Column(String)

    email = Column(String)

    phone_number = Column(String)

    hire_date = Column(Date)

    job_id = Column(String)

    salary = Column(Float)

    commission_pct = Column(Float)

    manager_id = Column(Integer)

    department_id = Column(Integer)