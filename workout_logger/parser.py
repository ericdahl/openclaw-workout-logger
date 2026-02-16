"""
Core parsing logic for workout logs.
Ported from src/parser.js
"""

import re
from datetime import datetime, timedelta, date as date_type
from typing import Optional, Tuple, List, Dict, Any
from zoneinfo import ZoneInfo

from workout_logger.exercises import normalizeExercise, getExerciseType, EXERCISE_TYPE
from workout_logger.models import WorkoutRecord, StrengthSet


PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def parseDate(date_str: Optional[str], base_date: datetime = None) -> Tuple[date_type, str, str, str]:
    """
    Parse date modifier (e.g., "yesterday", "today", "2026-01-31").
    Returns: (date_obj, year_str, month_str, day_str)
    """
    if base_date is None:
        base_date = datetime.now(PACIFIC_TZ)

    # Convert to Pacific time if not already
    if base_date.tzinfo is None:
        base_date = base_date.replace(tzinfo=PACIFIC_TZ)
    elif base_date.tzinfo != PACIFIC_TZ:
        base_date = base_date.astimezone(PACIFIC_TZ)

    if not date_str:
        # Return current date in Pacific time
        year = f"{base_date.year:04d}"
        month = f"{base_date.month:02d}"
        day = f"{base_date.day:02d}"
        return (base_date.date(), year, month, day)

    lower = date_str.lower().strip()

    if lower == 'yesterday':
        d = base_date - timedelta(days=1)
        year = f"{d.year:04d}"
        month = f"{d.month:02d}"
        day = f"{d.day:02d}"
        return (d.date(), year, month, day)

    if lower == 'today':
        year = f"{base_date.year:04d}"
        month = f"{base_date.month:02d}"
        day = f"{base_date.day:02d}"
        return (base_date.date(), year, month, day)

    # Try parsing as ISO date (YYYY-MM-DD)
    match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if match:
        year, month, day = match.groups()
        return (base_date.date(), year, month, day)

    raise ValueError(f'Could not parse date: "{date_str}"')


def parseRepList(rep_str: str) -> List[Dict[str, Any]]:
    """
    Parse a comma-separated rep list like "20,20,25" or "2,1,x".
    Returns list of dicts with 'reps' and optional 'failed' flag.
    """
    parts = rep_str.split(',')
    result = []
    for p in parts:
        trimmed = p.strip().lower()
        if trimmed in ('x', 'f', 'fail'):
            result.append({'reps': 0, 'failed': True})
        else:
            result.append({'reps': int(trimmed)})
    return result


def parseStrengthWorkout(exercise_norm: str, rest: str, iso_ts: str) -> Dict[str, Any]:
    """
    Parse strength/bodyweight/machine workout with flexible formats:
    - "225x5x3" = 225 lb, 5 sets, 3 reps each
    - "20,20,25" = bodyweight, sets of 20, 20, 25 reps
    - "405 2,1,x" = 405 lb, sets of 2, 1, failed
    - "2x90 4x10,7" = dumbbell 90lb each, 4 sets of 10 + 1 set of 7
    - "7x10" = 7 sets of 10 reps (bodyweight)
    """
    exercise_type = getExerciseType(exercise_norm)
    is_bodyweight = exercise_type == 'bodyweight'

    # Handle empty input (generic entry without sets/reps)
    if not rest or not rest.strip():
        return {
            'ts': iso_ts,
            'type': exercise_type,
            'exercise': exercise_norm,
            'sets': [],
        }

    parts = rest.strip().split()
    sets: List[StrengthSet] = []
    weight: Optional[float] = None
    notes = ''
    rpe: Optional[int] = None
    parts_consumed = 0
    is_dumbbell = 'dumbbell' in exercise_norm

    if len(parts) == 0 or parts[0] == '':
        raise ValueError('No weight/reps format found')

    first_part = parts[0]

    # Format: Single number for bodyweight (e.g. "20")
    if is_bodyweight and re.match(r'^\d+$', first_part):
        sets.append(StrengthSet(reps=int(first_part)))
        parts_consumed = 1

    # Format: comma-separated reps only (bodyweight): "20,20,25"
    elif re.match(r'^[\d,xfXF]+$', first_part) and ',' in first_part:
        rep_list = parseRepList(first_part)
        for r in rep_list:
            if r.get('failed'):
                sets.append(StrengthSet(reps=0, failed=True))
            else:
                sets.append(StrengthSet(reps=r['reps']))
        parts_consumed = 1

    # Format: dumbbell "2x90 4x10,7" - pair notation then sets
    elif is_dumbbell and re.match(r'^2x(\d+)$', first_part, re.IGNORECASE):
        db_match = re.match(r'^2x(\d+)$', first_part, re.IGNORECASE)
        weight = float(db_match.group(1))
        parts_consumed = 1

        # Parse sets format: "4x10,7" means 4 sets of 10, then 1 set of 7
        if len(parts) > 1:
            sets_format = parts[1]
            sets_match = re.match(r'^(\d+)x([\d,]+)$', sets_format, re.IGNORECASE)
            if sets_match:
                uniform_sets = int(sets_match.group(1))
                reps_list = [int(r.strip()) for r in sets_match.group(2).split(',')]

                # First number after 'x' is reps for uniform_sets, rest are additional sets
                main_reps = reps_list[0]
                for _ in range(uniform_sets):
                    sets.append(StrengthSet(weight=weight, reps=main_reps))

                # Additional sets with different reps
                for i in range(1, len(reps_list)):
                    sets.append(StrengthSet(weight=weight, reps=reps_list[i]))

                parts_consumed = 2

        if len(sets) > 0:
            notes = 'per dumbbell'

    # Format: "NxM" where context determines meaning
    elif re.match(r'^(\d+(?:\.\d+)?)x(\d+)$', first_part, re.IGNORECASE):
        match = re.match(r'^(\d+(?:\.\d+)?)x(\d+)$', first_part, re.IGNORECASE)
        num1 = float(match.group(1))
        num2 = int(match.group(2))

        # Check if there's a third part: "225x5x3"
        if len(parts) > 1 and re.match(r'^x?(\d+)$', parts[1], re.IGNORECASE):
            # Format: weight x sets x reps
            third_match = re.match(r'^x?(\d+)$', parts[1], re.IGNORECASE)
            weight = num1
            set_count = num2
            reps_per_set = int(third_match.group(1))
            for _ in range(set_count):
                sets.append(StrengthSet(weight=weight, reps=reps_per_set))
            parts_consumed = 2

        # For bodyweight: "7x10" = 7 sets of 10 reps
        elif is_bodyweight:
            set_count = int(num1)
            reps_per_set = num2
            for _ in range(set_count):
                sets.append(StrengthSet(reps=reps_per_set))
            parts_consumed = 1

        # For strength: "225x5" could be 225lb x 5 reps (1 set)
        else:
            weight = num1
            sets.append(StrengthSet(weight=weight, reps=num2))
            parts_consumed = 1

    # Format: "NxMxP" all in one: weight x sets x reps
    elif re.match(r'^(\d+(?:\.\d+)?)x(\d+)x(\d+)$', first_part, re.IGNORECASE):
        match = re.match(r'^(\d+(?:\.\d+)?)x(\d+)x(\d+)$', first_part, re.IGNORECASE)
        weight = float(match.group(1))
        set_count = int(match.group(2))
        reps_per_set = int(match.group(3))
        for _ in range(set_count):
            sets.append(StrengthSet(weight=weight, reps=reps_per_set))
        parts_consumed = 1

    # Format: Weight followed by SetsxReps (e.g. "135 1x4")
    elif re.match(r'^\d+(?:\.\d+)?$', first_part) and len(parts) > 1 and re.match(r'^(\d+)x(\d+)$', parts[1], re.IGNORECASE):
        weight = float(first_part)
        sets_match = re.match(r'^(\d+)x(\d+)$', parts[1], re.IGNORECASE)
        sets_count = int(sets_match.group(1))
        reps_count = int(sets_match.group(2))

        for _ in range(sets_count):
            sets.append(StrengthSet(weight=weight, reps=reps_count))
        parts_consumed = 2

    # Format: weight followed by comma-separated reps: "405 2,1,x"
    elif re.match(r'^\d+(?:\.\d+)?$', first_part) and len(parts) > 1 and re.match(r'^[\d,xfXF]+$', parts[1], re.IGNORECASE):
        weight = float(first_part)
        rep_list = parseRepList(parts[1])
        for r in rep_list:
            set_dict = {'weight': weight, 'reps': r['reps']}
            if r.get('failed'):
                set_dict['failed'] = True
            sets.append(StrengthSet(**set_dict))
        parts_consumed = 2

    else:
        raise ValueError(f'Could not parse format: "{rest}". Try formats like "225x3x5", "20,20,25", or "405 2,1,x"')

    # Parse remaining parts for RPE and notes
    remaining = ' '.join(parts[parts_consumed:])
    rpe_match = re.search(r'rpe(\d+)', remaining, re.IGNORECASE)
    if rpe_match:
        rpe = int(rpe_match.group(1))

    notes_from_remaining = re.sub(r'rpe\d+', '', remaining, flags=re.IGNORECASE).strip()
    if notes_from_remaining:
        notes = f'{notes}; {notes_from_remaining}' if notes else notes_from_remaining

    record = {
        'ts': iso_ts,
        'type': exercise_type,
        'exercise': exercise_norm,
    }

    if weight is not None:
        record['unit'] = 'lb'

    record['sets'] = [s.model_dump(exclude_none=True) for s in sets]

    if rpe is not None:
        record['rpe'] = rpe
    if notes:
        record['notes'] = notes

    return record


def parseCardioWorkout(exercise_norm: str, rest: str, iso_ts: str) -> Dict[str, Any]:
    """
    Parse cardio workout (e.g., "treadmill 10min 3.2mph incline15").
    """
    lower_rest = rest.lower()

    record = {
        'ts': iso_ts,
        'type': 'cardio',
        'modality': exercise_norm,
    }

    # Duration: "10min" or "10 minutes"
    dur_match = re.search(r'(\d+(?:\.\d+)?)\s*min(?:ute)?s?', lower_rest, re.IGNORECASE)
    if dur_match:
        record['duration_min'] = float(dur_match.group(1))

    # Speed: "3.2mph" or "7.2 mph"
    speed_match = re.search(r'(\d+(?:\.\d+)?)\s*mph', lower_rest, re.IGNORECASE)
    if speed_match:
        record['speed_mph'] = float(speed_match.group(1))

    # Incline: "incline15", "15 degree incline", "1 degree incline", etc.
    incline_match = re.search(r'(\d+(?:\.\d+)?)\s*degree\s*incline|incline\s*(\d+(?:\.\d+)?)', lower_rest, re.IGNORECASE)
    if incline_match:
        incline_value = incline_match.group(1) or incline_match.group(2)
        record['incline_percent'] = float(incline_value)

    # Distance: "3.0 miles" or "5 miles"
    dist_match = re.search(r'(\d+(?:\.\d+)?)\s*miles?', lower_rest, re.IGNORECASE)
    if dist_match:
        record['distance_miles'] = float(dist_match.group(1))

    # Extract remaining text as notes (remove extracted values)
    notes_text = rest
    notes_text = re.sub(r'\d+(?:\.\d+)?\s*min(?:ute)?s?', '', notes_text, flags=re.IGNORECASE)
    notes_text = re.sub(r'\d+(?:\.\d+)?\s*mph', '', notes_text, flags=re.IGNORECASE)
    notes_text = re.sub(r'\d+(?:\.\d+)?\s*degree\s*incline', '', notes_text, flags=re.IGNORECASE)
    notes_text = re.sub(r'incline\s*\d+(?:\.\d+)?', '', notes_text, flags=re.IGNORECASE)
    notes_text = re.sub(r'\d+(?:\.\d+)?\s*miles?', '', notes_text, flags=re.IGNORECASE)
    notes_text = re.sub(r'[,\s]+', ' ', notes_text).strip()

    if notes_text:
        record['notes'] = notes_text

    return record


def parseWorkoutLog(message: str, timestamp: Optional[datetime] = None, source: str = 'telegram') -> Tuple[Dict[str, Any], str]:
    """
    Main parser for workout log messages.
    Returns: (record_dict, date_string)

    Args:
        message: The workout log message (with or without /log or /note prefix)
        timestamp: Optional timestamp (defaults to now in Pacific time)
        source: Source identifier (default: 'telegram')
    """
    is_log = message.startswith('/log ')
    is_note = message.startswith('/note ')

    if not is_log and not is_note:
        raise ValueError('Message must start with /log or /note')

    prefix_length = 5 if is_log else 6
    content = message[prefix_length:].strip()

    # Check for date modifier (at start or end)
    date_str: Optional[str] = None
    log_content = content

    # Try start of message: "2026-01-29: pull-up 20,27" or "2026-01-28 pull-up 20"
    date_match_start = re.match(r'^(yesterday|today|\d{4}-\d{2}-\d{2})(?:\s*:\s*|\s+)', content, re.IGNORECASE)
    if date_match_start:
        date_str = date_match_start.group(1)
        log_content = content[len(date_match_start.group(0)):]
    elif not is_note:
        # Try end of message: "pull-up 20,27 2026-01-29"
        # Only match ISO dates at end (not "yesterday"/"today" to avoid false matches in notes)
        date_match_end = re.search(r'\s+(\d{4}-\d{2}-\d{2})\s*$', content, re.IGNORECASE)
        if date_match_end:
            date_str = date_match_end.group(1)
            log_content = content[:content.rfind(date_match_end.group(1))].strip()

    # Parse date
    now = timestamp if timestamp else datetime.now(PACIFIC_TZ)
    date_info = parseDate(date_str, now)
    date_obj, year, month, day = date_info

    # Get Pacific time components for the timestamp
    if now.tzinfo is None:
        now = now.replace(tzinfo=PACIFIC_TZ)
    elif now.tzinfo != PACIFIC_TZ:
        now = now.astimezone(PACIFIC_TZ)

    # Determine offset (PST = -08:00, PDT = -07:00)
    offset = now.strftime('%z')
    offset_formatted = f"{offset[:3]}:{offset[3:]}"

    h = f"{now.hour:02d}"
    m = f"{now.minute:02d}"
    s = f"{now.second:02d}"

    iso_ts = f"{year}-{month}-{day}T{h}:{m}:{s}{offset_formatted}"

    # Handle Note
    if is_note:
        return (
            {
                'ts': iso_ts,
                'type': 'note',
                'notes': log_content.strip(),
                'source': source,
                'raw': message,
            },
            f'{year}-{month}-{day}'
        )

    # Split exercise name from rest
    words = log_content.split()
    if len(words) == 0:
        raise ValueError('No exercise specified')

    exercise_name = words[0]
    exercise_norm = normalizeExercise(exercise_name)
    words_consumed = 1

    # Try combining up to 3 words (e.g., "tricep dip machine")
    if not exercise_norm and len(words) > 1:
        exercise_name = f'{words[0]} {words[1]}'
        exercise_norm = normalizeExercise(exercise_name)
        words_consumed = 2

        if not exercise_norm and len(words) > 2:
            exercise_name = f'{words[0]} {words[1]} {words[2]}'
            exercise_norm = normalizeExercise(exercise_name)
            words_consumed = 3

    if not exercise_norm:
        raise ValueError(f'Unknown exercise: "{exercise_name}". Could not normalize.')

    rest = ' '.join(words[words_consumed:])
    exercise_type = getExerciseType(exercise_norm)

    if exercise_type == 'cardio':
        record = parseCardioWorkout(exercise_norm, rest, iso_ts)
    elif exercise_type in ('strength', 'machine', 'bodyweight'):
        record = parseStrengthWorkout(exercise_norm, rest, iso_ts)
    else:
        raise ValueError(f'Unknown exercise type for "{exercise_norm}"')

    record['source'] = source
    record['raw'] = message

    return (record, f'{year}-{month}-{day}')
