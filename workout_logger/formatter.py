"""
Workout log formatter - converts JSONL records to human-readable format.
Ported from src/formatter.js
"""

import sys
import json
from typing import Dict, Any, List


def capitalize(s: str) -> str:
    """Capitalize words in a string, handling underscores."""
    if not s:
        return ''
    return ' '.join(word.capitalize() for word in s.replace('_', ' ').split())


def formatSets(sets: List[Dict[str, Any]], unit: str = 'lb') -> str:
    """
    Format a list of sets into a concise string.
    e.g. "315x5x3" or "315x5, 315x4" or "20, 20, 25"
    """
    if not sets or len(sets) == 0:
        return 'No sets'

    # Group by weight
    groups = []
    current_group = None

    for s in sets:
        weight = s.get('weight')
        reps = s.get('reps')
        failed = ' (fail)' if s.get('failed') else ''

        if current_group and current_group['weight'] == weight:
            current_group['reps'].append(f'{reps}{failed}')
        else:
            if current_group:
                groups.append(current_group)
            current_group = {'weight': weight, 'reps': [f'{reps}{failed}']}

    if current_group:
        groups.append(current_group)

    # Format groups
    result = []
    for g in groups:
        # Check if all reps are the same
        all_same = all(r == g['reps'][0] for r in g['reps'])
        count = len(g['reps'])
        rep_str = f"{count}x{g['reps'][0]}" if all_same and count > 1 else ', '.join(g['reps'])

        if g['weight'] is not None:
            # Strength: "315x5x5" or "315x[5,4,3]"
            if all_same and count > 1:
                result.append(f"{int(g['weight'])}x{count}x{g['reps'][0]}")
            elif count == 1:
                result.append(f"{int(g['weight'])}x{g['reps'][0]}")
            else:
                result.append(f"{int(g['weight'])}x[{rep_str}]")
        else:
            # Bodyweight: "20, 20, 25" or "5x10"
            if all_same and count > 1:
                result.append(f"{count}x{g['reps'][0]} reps")
            else:
                result.append(f"{rep_str} reps")

    return ', '.join(result)


def formatRecord(record: Dict[str, Any]) -> str:
    """
    Format a single workout record into human-readable format.

    Examples:
        "[2026-02-16] Squat: 315x5x3 @ RPE 8 - "felt strong""
        "[2026-02-16] Treadmill: 10 min, 3.2 mph, 15% inc"
        "[2026-02-16] Note: "Felt tired today""
    """
    date = record['ts'].split('T')[0]
    name = capitalize(record.get('exercise') or record.get('modality', ''))
    notes = f' - "{record["notes"]}"' if record.get('notes') else ''
    rpe = f' @ RPE {record["rpe"]}' if record.get('rpe') else ''

    if record['type'] == 'note':
        return f'[{date}] Note: "{record.get("notes", "")}"'

    if record['type'] == 'cardio':
        parts = []
        if record.get('duration_min'):
            parts.append(f"{record['duration_min']} min")
        if record.get('distance_miles'):
            parts.append(f"{record['distance_miles']} mi")
        if record.get('speed_mph'):
            parts.append(f"{record['speed_mph']} mph")
        if record.get('incline_percent'):
            parts.append(f"{record['incline_percent']}% inc")
        summary = ', '.join(parts)
    else:
        # Strength / Machine / Bodyweight
        summary = formatSets(record.get('sets', []), record.get('unit', 'lb'))

    return f'[{date}] {name}: {summary}{rpe}{notes}'


def main():
    """CLI entry point - read JSONL from stdin and output formatted records."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            record = json.loads(line)
            print(formatRecord(record))
        except json.JSONDecodeError:
            # Silently ignore invalid JSON lines to be pipe-friendly
            continue
        except Exception as e:
            # Optionally log errors to stderr
            print(f"Error formatting record: {e}", file=sys.stderr)
            continue


if __name__ == '__main__':
    main()
