# Workout Logger

Parse and store workout logs from Telegram into a JSONL time-series database.

## Overview

This tool parses `/log` messages from Telegram and converts them into structured JSON records saved to `/srv/openclaw/db/YYYY/MM/DD.jsonl`.

**Format:** `weight x sets x reps`

## Usage

### Send logs via Telegram

```
/log squat 315x5x3 rpe8 felt strong
/log ohp 145x5x3 last set grindy
/log weighted pull-up 25x5x10 felt good
/log face pulls 60x3x15
/log ab crunch 120x15x3 slow tempo
/log treadmill 1 degree incline, 7.2 mph, 3.0 miles
```

### Backdate logs

If you forgot to log it on the day, prefix with a date:

```
/log yesterday: squat 315x5x3 rpe8
/log 2026-01-31: deadlift 405x5x1 rpe9
```

## Supported Exercise Types

### Strength Exercises
- **Squat** (sq)
- **Bench Press** (bench, bp)
- **Deadlift** (dl)
- **Overhead Press** (ohp, op, press)
- **Barbell Row** (row, bent over row)
- **Weighted Dip**
- **Dip**
- **Chin Up**
- **Weighted Chin Up**
- **Pull Up** (pullup)
- **Weighted Pull Up** (weighted pull-up)

### Machine Exercises
- **Ab Crunch** (ab_crunch)
- **Cybex Ab Crunch**
- **Leg Press**
- **Hack Squat**
- **Face Pulls**

### Cardio
- **Treadmill** (tm)
- **Rowing** (rower, row machine)
- **Stationary Bike** (bike)

## Output Format

Each log entry is saved as a single-line JSON record in `/srv/openclaw/db/YYYY/MM/DD.jsonl`:

### Strength/Machine Workout
```json
{
  "ts": "2026-02-01T11:29:48-08:00",
  "type": "strength",
  "exercise": "squat",
  "unit": "lb",
  "sets": [
    {"weight": 315, "reps": 5},
    {"weight": 315, "reps": 5},
    {"weight": 315, "reps": 5}
  ],
  "rpe": 8,
  "notes": "felt strong",
  "source": "telegram",
  "raw": "/log squat 315x5x3 rpe8 felt strong"
}
```

### Cardio Workout
```json
{
  "ts": "2026-02-01T11:29:51-08:00",
  "type": "cardio",
  "modality": "treadmill",
  "duration_min": 10,
  "speed_mph": 3.2,
  "incline_percent": 15,
  "distance_miles": 3.0,
  "notes": "steady pace",
  "source": "telegram",
  "raw": "/log treadmill 10min 3.2mph incline15 3.0 miles steady pace"
}
```

## Database Structure

```
/srv/openclaw/db/
├── 2026/
│   ├── 01/
│   │   ├── 31.jsonl
│   │   └── ...
│   ├── 02/
│   │   ├── 01.jsonl
│   │   └── ...
│   └── ...
└── ...
```

Each `.jsonl` file contains one JSON record per line (newline-delimited JSON).

## Scripts

### `src/parser.js`
Core parsing logic. Accepts a `/log` message string and returns a structured JSON record.

**CLI Usage:**
```bash
node src/parser.js "/log squat 315x5x3 rpe8 felt strong"
```

**Module Usage:**
```javascript
const { parseWorkoutLog, writeWorkoutLog } = require('./src/parser.js');

const { record, date } = parseWorkoutLog("/log squat 315x5x3 rpe8 felt strong");
const filepath = writeWorkoutLog(record, date);
```

### `src/handler.js`
Wrapper function for processing messages. Handles errors gracefully.

**CLI Usage:**
```bash
node src/handler.js "/log squat 315x5x3 rpe8 felt strong"
```

**Module Usage:**
```javascript
const { handleWorkoutMessage } = require('./src/handler.js');

const result = handleWorkoutMessage("/log squat 315x5x3 rpe8 felt strong");
// Returns: { success: true/false, message: string, record?: object, error?: string }
```

### `src/monitor.js`
Tracks processed messages to avoid duplicates. Used for deduplication in automated integrations.

## Configuration

### Environment Variables

Before using the monitor/hook functionality, set your Telegram user ID:

```bash
export AUTHORIZED_TELEGRAM_ID=12345678
```

Or create a `.env` file:

```bash
cp .env.example .env
# Edit .env and set your Telegram user ID
```

To find your Telegram user ID:
- Chat with [@userinfobot](https://t.me/userinfobot) on Telegram
- Check OpenClaw logs for the ID when you send a message

**Note:** `.env` is in `.gitignore` and will not be committed to git.

## Integration with OpenClaw

The scripts are invoked automatically when you send a `/log` message from Telegram. The integration:

1. Intercepts messages from authorized Telegram user
2. Checks if message starts with `/log`
3. Calls `handleWorkoutMessage()` to parse and save
4. Responds with confirmation in Telegram

**Setup required:**
- Set `AUTHORIZED_TELEGRAM_ID` environment variable
- Message will be ignored if user ID doesn't match

No manual invocation needed — just send the message and it's logged automatically.

## Error Handling

If a message can't be parsed, you'll receive a clarification request:

```
❌ Unknown exercise: "foo". Could not normalize.
```

Common issues:
- **Unknown exercise:** Add exercise to the `EXERCISE_MAP` in `src/parser.js`
- **Invalid format:** Make sure format is `weight x sets x reps` (e.g., `315x5x3`)
- **Timestamp issues:** Timestamps are always Pacific time (`-08:00` offset)

## Development

### Run Tests
```bash
npm run test:parser "/log squat 315x5x3"
npm run test:handler "/log ohp 145x5x3"
```

### Add New Exercises

Edit `src/parser.js` and add to `EXERCISE_MAP`:

```javascript
const EXERCISE_MAP = {
  'new_exercise': 'normalized_name',
  'alias': 'normalized_name',
};
```

Then add the type:

```javascript
const EXERCISE_TYPE = {
  'normalized_name': 'strength', // or 'machine', 'bodyweight', 'cardio'
};
```

## File Naming

- `parser.js` — Core parsing (exports `parseWorkoutLog`, `writeWorkoutLog`)
- `handler.js` — High-level handler (exports `handleWorkoutMessage`)
- `monitor.js` — State tracking for deduplication (exports `processMessage`)
- `.state.json` — Runtime state (not versioned, created at runtime)

## License

MIT
