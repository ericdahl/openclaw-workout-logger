"""
Workout Logger - Python-based CLI for logging workouts to JSONL with git integration.
"""

__version__ = "2.0.0"

from workout_logger.parser import parseWorkoutLog, normalizeExercise
from workout_logger.writer import writeWorkoutLog
from workout_logger.models import WorkoutRecord, StrengthSet

__all__ = [
    "parseWorkoutLog",
    "normalizeExercise",
    "writeWorkoutLog",
    "WorkoutRecord",
    "StrengthSet",
]
