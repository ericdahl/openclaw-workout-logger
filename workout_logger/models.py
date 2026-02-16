"""
Pydantic models for workout data validation.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict


class StrengthSet(BaseModel):
    """Represents a single set in a strength/bodyweight/machine workout."""
    model_config = ConfigDict(extra="forbid")

    weight: Optional[float] = None
    reps: int
    failed: bool = False


class WorkoutRecord(BaseModel):
    """Complete workout log entry."""
    model_config = ConfigDict(extra="forbid")

    ts: str  # ISO 8601 timestamp with timezone
    type: Literal["strength", "bodyweight", "machine", "cardio", "note"]

    # For strength/bodyweight/machine
    exercise: Optional[str] = None
    sets: Optional[List[StrengthSet]] = None
    unit: Optional[Literal["lb", "kg"]] = None

    # For cardio
    modality: Optional[str] = None
    duration_min: Optional[float] = None
    speed_mph: Optional[float] = None
    incline_percent: Optional[float] = None
    distance_miles: Optional[float] = None

    # Common metadata
    rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None
    source: str = "cli"
    raw: str
