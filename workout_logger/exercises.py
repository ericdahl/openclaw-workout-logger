"""
Exercise normalization maps and type classifications.
Ported from src/parser.js
"""

from typing import Optional, Literal

ExerciseType = Literal["strength", "bodyweight", "machine", "cardio"]

# Exercise normalization map - maps aliases to canonical names
EXERCISE_MAP: dict[str, str] = {
    # Strength exercises
    'squat': 'squat',
    'sq': 'squat',
    'bench': 'bench_press',
    'bench press': 'bench_press',
    'bp': 'bench_press',
    'deadlift': 'deadlift',
    'dl': 'deadlift',
    'ohp': 'ohp',
    'overhead press': 'ohp',
    'op': 'ohp',
    'press': 'ohp',
    'row': 'barbell_row',
    'rows': 'barbell_row',
    'barbell row': 'barbell_row',
    'bent over row': 'barbell_row',
    'incline row': 'incline_row',
    'weighted dip': 'weighted_dip',
    'dip': 'dip',
    'chin up': 'chin_up',
    'chin-up': 'chin_up',
    'chinup': 'chin_up',
    'weighted chin up': 'weighted_chin_up',
    'pull up': 'pull_up',
    'pull-up': 'pull_up',
    'pullup': 'pull_up',
    'weighted pull up': 'weighted_pull_up',
    'weighted pullup': 'weighted_pull_up',
    'weighted pull-up': 'weighted_pull_up',
    'dragon flag': 'dragon_flag',
    'dragon-flag': 'dragon_flag',
    'dragonflag': 'dragon_flag',
    'shrug': 'shrug',

    # Dumbbell exercises
    'db bench': 'dumbbell_bench_press',
    'dumbbell bench': 'dumbbell_bench_press',
    'db press': 'dumbbell_bench_press',

    # Machines
    'chest press': 'chest_press_machine',
    'chest press machine': 'chest_press_machine',
    'tricep dip machine': 'tricep_dip_machine',
    'triceip dip': 'tricep_dip_machine',
    'ab crunch': 'ab_crunch',
    'ab_crunch': 'ab_crunch',
    'cybex ab crunch': 'cybex_ab_crunch',
    'cybex_ab_crunch': 'cybex_ab_crunch',
    'leg press': 'leg_press',
    'leg_press': 'leg_press',
    'hack squat': 'hack_squat',
    'hack_squat': 'hack_squat',
    'face pulls': 'face_pulls',
    'face pull': 'face_pulls',
    'lat pulldown': 'lat_pulldown',
    'lat pull down': 'lat_pulldown',
    'lat pull-down': 'lat_pulldown',

    # Cardio
    'treadmill': 'treadmill',
    'tm': 'treadmill',
    'rowing': 'rowing',
    'rower': 'rowing',
    'row machine': 'rowing',
    'bike': 'stationary_bike',
    'stationary bike': 'stationary_bike',
}

# Exercise type classification - maps canonical name to exercise type
EXERCISE_TYPE: dict[str, ExerciseType] = {
    'squat': 'strength',
    'bench_press': 'strength',
    'deadlift': 'strength',
    'ohp': 'strength',
    'barbell_row': 'strength',
    'incline_row': 'strength',
    'weighted_dip': 'strength',
    'dumbbell_bench_press': 'strength',
    'shrug': 'strength',
    'dip': 'bodyweight',
    'chin_up': 'bodyweight',
    'weighted_chin_up': 'bodyweight',
    'pull_up': 'bodyweight',
    'weighted_pull_up': 'bodyweight',
    'dragon_flag': 'bodyweight',
    'chest_press_machine': 'machine',
    'tricep_dip_machine': 'machine',
    'ab_crunch': 'machine',
    'cybex_ab_crunch': 'machine',
    'leg_press': 'machine',
    'hack_squat': 'machine',
    'face_pulls': 'machine',
    'lat_pulldown': 'machine',
    'treadmill': 'cardio',
    'rowing': 'cardio',
    'stationary_bike': 'cardio',
}


def normalizeExercise(exercise_str: str) -> Optional[str]:
    """
    Normalize exercise name using EXERCISE_MAP.
    Returns canonical exercise name or None if unknown.
    """
    lower = exercise_str.lower().strip()
    return EXERCISE_MAP.get(lower)


def getExerciseType(exercise_norm: str) -> Optional[ExerciseType]:
    """Get exercise type for a normalized exercise name."""
    return EXERCISE_TYPE.get(exercise_norm)
