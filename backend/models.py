from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    x = Column(Float) # X coordinate
    y = Column(Float) # Y coordinate

class Depot(Base):
    __tablename__ = "depots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, default="Main Depot")
    address = Column(String)
    x = Column(Float)
    y = Column(Float)

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Float, default=100.0) # Example: capacity in kg or m^3

class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    vehicle = relationship("Vehicle")

    depot_id = Column(Integer, ForeignKey("depots.id"))
    depot = relationship("Depot")

    total_distance = Column(Float, nullable=True)

    # Relationship to the sequence of stops
    stops = relationship("TaskStop", back_populates="task", cascade="all, delete-orphan", order_by="TaskStop.stop_order")

class TaskStop(Base):
    __tablename__ = "task_stops"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    stop_order = Column(Integer) # The order of the stop in the route

    task = relationship("Task", back_populates="stops")
    customer = relationship("Customer")