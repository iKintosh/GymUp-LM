"""SQLAlchemy models for GymUp database schema."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

Base = declarative_base()

_engine = None
_SessionLocal = None


def get_engine(db_path: Path | str):
    """Get or create database engine."""
    global _engine
    if _engine is None or str(db_path) not in str(_engine.url):
        _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return _engine


def get_session(db_path: Path | str) -> Session:
    """Get a new database session."""
    global _SessionLocal
    engine = get_engine(db_path)
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine)
    return _SessionLocal()


class Program(Base):
    """Training program definition."""

    __tablename__ = "program"

    id = Column("_id", Integer, primary_key=True)
    name = Column(String)
    comment = Column(Text)
    userComment = Column(Text)
    purpose = Column(String)
    level = Column(String)
    frequency = Column(String)
    place = Column(String)
    gender = Column(String)
    color = Column(Integer)

    days = relationship("Day", back_populates="program", lazy="dynamic")

    def __repr__(self):
        return f"<Program(id={self.id}, name='{self.name}')>"


class Day(Base):
    """Training day within a program."""

    __tablename__ = "day"

    id = Column("_id", Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("program._id"))
    name = Column(String)
    comment = Column(Text)
    userComment = Column(Text)
    order_num = Column(Integer)
    color = Column(Integer)

    program = relationship("Program", back_populates="days")
    exercises = relationship("Exercise", back_populates="day", lazy="dynamic")
    trainings = relationship("Training", back_populates="day", lazy="dynamic")

    def __repr__(self):
        return f"<Day(id={self.id}, name='{self.name}')>"


class ThExercise(Base):
    """Exercise template/definition (th = template/theory)."""

    __tablename__ = "th_exercise"

    id = Column("_id", Integer, primary_key=True)
    name = Column(String)
    guide = Column(Text)
    mainMuscleWorked = Column(Integer)
    otherMuscles = Column(String)
    equipment = Column(Integer)
    mechanicsType = Column(Integer)
    level = Column(Integer)
    type = Column(Integer)
    force = Column(Integer)
    isAddedByUser = Column(Integer, default=0)
    isFavorite = Column(Integer)
    userComment = Column(Text)
    archTime = Column(Integer)

    exercises = relationship("Exercise", back_populates="template", lazy="dynamic")
    workouts = relationship("Workout", back_populates="template", lazy="dynamic")

    def __repr__(self):
        return f"<ThExercise(id={self.id}, name='{self.name}')>"


class Exercise(Base):
    """Exercise instance in a program day."""

    __tablename__ = "exercise"

    id = Column("_id", Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("day._id"))
    th_exercise_id = Column(Integer, ForeignKey("th_exercise._id"))
    restTime = Column(Integer)
    restTimeAfterWarming = Column(Integer)
    restTimeAfterExercise = Column(Integer)
    order_num = Column(Integer)
    isMeasureWeight = Column(Integer)
    isMeasureReps = Column(Integer)
    isMeasureTime = Column(Integer)
    isMeasureDistance = Column(Integer)
    oneRepMax = Column(Float)
    color = Column(Integer)

    day = relationship("Day", back_populates="exercises")
    template = relationship("ThExercise", back_populates="exercises")

    def __repr__(self):
        return f"<Exercise(id={self.id}, th_exercise_id={self.th_exercise_id})>"


class Training(Base):
    """Completed training session."""

    __tablename__ = "training"

    id = Column("_id", Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("day._id"))
    startDateTime = Column(Integer)  # Unix timestamp in milliseconds
    finishDateTime = Column(Integer)
    tonnage = Column(Float, default=0)
    repsAmount = Column(Float, default=0)
    setsAmount = Column(Integer, default=0)
    exercisesAmount = Column(Integer, default=0)
    hard_sense = Column(Integer)
    hard_sense_auto1 = Column(Float)
    hard_sense_auto2 = Column(Float)
    comment = Column(Text)
    name = Column(String)
    distance = Column(Float)
    time = Column(Float)
    color = Column(Integer)

    day = relationship("Day", back_populates="trainings")
    workouts = relationship("Workout", back_populates="training", lazy="dynamic")

    @property
    def start_datetime(self) -> Optional[datetime]:
        """Parse start datetime from millisecond timestamp."""
        if self.startDateTime:
            try:
                return datetime.fromtimestamp(self.startDateTime / 1000)
            except (ValueError, OSError):
                return None
        return None

    @property
    def finish_datetime(self) -> Optional[datetime]:
        """Parse finish datetime from millisecond timestamp."""
        if self.finishDateTime:
            try:
                return datetime.fromtimestamp(self.finishDateTime / 1000)
            except (ValueError, OSError):
                return None
        return None

    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate training duration in minutes."""
        start = self.start_datetime
        finish = self.finish_datetime
        if start and finish:
            return int((finish - start).total_seconds() / 60)
        return None

    @property
    def is_performed(self) -> bool:
        """Check if training was actually performed (not just planned)."""
        return self.finishDateTime is not None and self.finishDateTime > 0

    @property
    def is_planned(self) -> bool:
        """Check if training is only planned (not yet performed)."""
        return not self.is_performed

    def __repr__(self):
        return f"<Training(id={self.id}, date='{self.start_datetime}', performed={self.is_performed})>"


class Workout(Base):
    """Exercise instance within a training session."""

    __tablename__ = "workout"

    id = Column("_id", Integer, primary_key=True)
    training_id = Column(Integer, ForeignKey("training._id"))
    th_exercise_id = Column(Integer, ForeignKey("th_exercise._id"))
    tonnage = Column(Float, default=0)
    setsAmount = Column(Integer, default=0)
    repsAmount = Column(Float, default=0)
    oneRepMax = Column(Float)
    hard_sense = Column(Integer)
    hard_sense_auto = Column(Float)
    order_num = Column(Integer)
    comment = Column(Text)
    finishDateTime = Column(Integer)
    restTime = Column(Integer)
    avgRestTime = Column(Integer)
    distance = Column(Float)
    time = Column(Float)
    color = Column(Integer)

    training = relationship("Training", back_populates="workouts")
    template = relationship("ThExercise", back_populates="workouts")
    sets = relationship("Set", back_populates="workout", lazy="dynamic")

    def __repr__(self):
        return f"<Workout(id={self.id}, exercise={self.th_exercise_id})>"


class Set(Base):
    """Individual set within a workout."""

    __tablename__ = "set_"

    id = Column("_id", Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey("workout._id"))
    weight = Column(Float)
    reps = Column(Float)
    time = Column(Float)
    distance = Column(Float)
    hard_sense = Column(Integer)
    finishDateTime = Column(Integer)  # Unix timestamp in milliseconds
    comment = Column(Text)
    koef1 = Column(Float)
    koef2 = Column(Float)
    bindTime = Column(Integer)

    workout = relationship("Workout", back_populates="sets")

    @property
    def finish_datetime(self) -> Optional[datetime]:
        """Parse finish datetime from millisecond timestamp."""
        if self.finishDateTime:
            try:
                return datetime.fromtimestamp(self.finishDateTime / 1000)
            except (ValueError, OSError):
                return None
        return None

    def __repr__(self):
        return f"<Set(id={self.id}, weight={self.weight}, reps={self.reps})>"
