# Workout Logger (Python)

Python-based CLI for logging workouts to JSONL database with built-in git integration.

## Features

- **Clean CLI syntax**: No `/log` prefix required when using the CLI
- **Built-in git integration**: Automatic commits after each entry
- **Date handling**: Support for "yesterday", "today", and explicit dates (YYYY-MM-DD)
- **Comprehensive parsing**: Handles strength, bodyweight, machine, and cardio workouts
- **Exercise aliases**: 75+ exercise name mappings (e.g., `sq` → `squat`, `bp` → `bench_press`)
- **RPE tracking**: Rate of Perceived Exertion (1-10 scale)
- **Notes support**: Add contextual notes to any workout

## Installation

### From Source (Development)

```bash
cd /Users/ecd/repos/openclaw-workout-logger
pip install -e .
```

### From Git (Production)

```bash
pip install git+https://github.com/ericdahl/workout-logger.git
```

## Quick Start

### Basic Usage

```bash
# Log a strength workout
workout-logger log "deadlift 405 5x2"

# With RPE and notes
workout-logger log "squat 315x5x3 rpe8 felt strong"

# Bodyweight exercises
workout-logger log "pull-up 20,20,25"

# Cardio
workout-logger log "treadmill 10min 3.2mph incline15"

# Notes
workout-logger note "Felt tired today"
```

### Date Modifiers

```bash
# Yesterday's workout
workout-logger log "yesterday: squat 315x5x3"

# Specific date
workout-logger log "2026-01-30: deadlift 405x1x5"
```

### Options

```bash
# Dry run (parse without writing)
workout-logger log "bench 225x5x3" --dry-run

# Custom database directory
workout-logger log "squat 315x5x3" --db-dir ~/my-fitness-db

# Skip git commit
workout-logger log "bench 225x5x3" --no-commit

# Override date
workout-logger log "squat 315x5x3" --date 2026-02-01

# Custom source identifier
workout-logger log "bench 225x5x3" --source backfill
```

## Configuration

### Environment Variables

- `WORKOUT_LOGGER_DB`: Default database directory (defaults to `~/repos/fitness/db`)

### Database Structure

Workouts are stored in a date-based directory structure:

```
~/repos/fitness/db/
├── 2026/
│   ├── 01/
│   │   ├── 30.jsonl
│   │   └── 31.jsonl
│   ├── 02/
│   │   ├── 01.jsonl
│   │   ├── 02.jsonl
│   │   └── 03.jsonl
```

Each file contains JSONL (one JSON object per line):

```json
{"ts":"2026-02-16T10:30:45-08:00","type":"strength","exercise":"squat","unit":"lb","sets":[{"weight":315,"reps":3},{"weight":315,"reps":3},{"weight":315,"reps":3}],"rpe":8,"notes":"felt strong","source":"cli","raw":"/log squat 315x5x3 rpe8 felt strong"}
```

## Workout Formats

### Strength Exercises

```bash
# Weight x Sets x Reps
workout-logger log "squat 315x5x3"           # 315 lb, 5 sets, 3 reps each
workout-logger log "bench 225x3x5"           # 225 lb, 3 sets, 5 reps each

# Weight followed by Sets x Reps
workout-logger log "deadlift 405 1x3"        # 405 lb, 1 set, 3 reps

# Weight with variable reps
workout-logger log "squat 405 2,1,x"         # 405 lb, sets of 2, 1, then failed
```

### Bodyweight Exercises

```bash
# Comma-separated reps
workout-logger log "pull-up 20,20,25"        # 3 sets: 20, 20, 25 reps

# Uniform sets
workout-logger log "pull-up 7x10"            # 7 sets of 10 reps

# Single set
workout-logger log "pull-up 20"              # 1 set of 20 reps

# Weighted bodyweight
workout-logger log "weighted pull-up 25x5x10"  # +25 lb, 5 sets, 10 reps
```

### Machine Exercises

Same format as strength exercises:

```bash
workout-logger log "leg press 405x3x10"
workout-logger log "face pulls 60x3x15"
workout-logger log "ab crunch 120x3x15"
```

### Cardio

```bash
# Treadmill
workout-logger log "treadmill 10min 3.2mph incline15"
workout-logger log "tm 1 degree incline, 7.2 mph, 3.0 miles"

# Rowing machine
workout-logger log "rowing 30min"

# Stationary bike
workout-logger log "bike 20min"
```

## Exercise Aliases

The parser recognizes many common exercise aliases:

| Canonical Name | Aliases |
|----------------|---------|
| squat | sq |
| bench_press | bench, bp, bench press |
| deadlift | dl |
| ohp | op, press, overhead press |
| barbell_row | row, rows, bent over row |
| pull_up | pull-up, pullup |
| weighted_pull_up | weighted pull-up, weighted pullup |
| treadmill | tm |
| rowing | rower, row machine |

See `workout_logger/exercises.py` for the full list (75+ aliases).

## Git Integration

Every workout is automatically committed to git with a descriptive message:

```bash
$ workout-logger log "squat 315x5x3 rpe8"
✓ Logged to ~/repos/fitness/db/2026/02/16.jsonl
✓ Committed to git

$ cd ~/repos/fitness && git log -1 --oneline
abc123 workout: squat 315x5x3 rpe8
```

Commit messages are automatically formatted:
- Strength/bodyweight: `"workout: squat 315x5x3 rpe8"`
- Notes: `"note: Felt tired today"`

To skip git commit:

```bash
workout-logger log "squat 315x5x3" --no-commit
```

## Development

### Run Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

### Project Structure

```
workout_logger/
├── __init__.py        # Package exports
├── cli.py             # Click-based CLI
├── parser.py          # Core parsing logic
├── writer.py          # JSONL writing + git integration
├── exercises.py       # Exercise maps and types
├── models.py          # Pydantic data models
└── formatter.py       # Human-readable output

tests/
├── test_parser.py     # Parser tests
├── test_writer.py     # Writer tests
└── test_cli.py        # CLI tests
```

## Migration from Node.js

The Python version is a direct port of the Node.js implementation with feature parity:

1. Install Python version: `pip install -e .`
2. Test with dry run: `workout-logger log "squat 315x5x3" --dry-run`
3. Verify output matches Node.js version
4. Update openclaw to use `workout-logger` instead of `node index.js`

Key differences:
- **No `/log` prefix**: CLI usage doesn't require `/log` or `/note` prefix
- **Built-in git**: Git integration is built into the application (no separate script)
- **Better help**: `workout-logger --help` shows comprehensive usage

## Troubleshooting

### Git commit fails

Ensure the database directory is inside a git repository:

```bash
cd ~/repos/fitness
git init  # If not already a git repo
```

### Import errors

Ensure all dependencies are installed:

```bash
pip install click pydantic python-dateutil gitpython
```

### Timezone issues

The parser uses Pacific Time (America/Los_Angeles) by default. All timestamps are stored with timezone offset.

## License

MIT
