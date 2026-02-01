# Test Cases & Examples

## Strength Exercises

### Squat
```
/log squat 315x5x3 rpe8 felt strong
→ 315 lb, 5 sets, 3 reps, RPE 8
```

### Overhead Press
```
/log ohp 145x5x3 last set grindy
→ 145 lb, 5 sets, 3 reps, note: "last set grindy"
```

### Bench Press
```
/log bench 225x3x5 
→ 225 lb, 3 sets, 5 reps
```

### Deadlift
```
/log dl 405x1x3 rpe9
→ 405 lb, 1 set, 3 reps, RPE 9
```

### Barbell Row
```
/log row 275x4x5
→ 275 lb, 4 sets, 5 reps
```

## Bodyweight Exercises

### Weighted Pull-ups
```
/log weighted pull-up 25x5x10 felt good. First time at 24h fitness
→ 25 lb weight, 5 sets, 10 reps, note: "felt good. First time at 24h fitness"
```

### Weighted Chin-ups
```
/log weighted chin up 35x3x8
→ 35 lb weight, 3 sets, 8 reps
```

### Dips
```
/log dip 15x3x8
→ 15 lb weight, 3 sets, 8 reps
```

## Machine Exercises

### Ab Crunch Machine
```
/log ab crunch 120x15x3 slow tempo
→ 120 lb, 15 sets, 3 reps, note: "slow tempo"
```

### Face Pulls
```
/log face pulls 60x3x15
→ 60 lb, 3 sets, 15 reps
```

### Leg Press
```
/log leg press 405x3x10
→ 405 lb, 3 sets, 10 reps
```

### Hack Squat
```
/log hack squat 315x3x8
→ 315 lb, 3 sets, 8 reps
```

## Cardio

### Treadmill
```
/log treadmill 1 degree incline, 7.2 mph, 3.0 miles
→ treadmill, 1% incline, 7.2 mph, 3.0 miles

/log treadmill 10min 3.2mph incline15 steady pace
→ treadmill, 10 minutes at 3.2 mph, 15% incline, note: "steady pace"
```

### Rowing Machine
```
/log rowing 30min 2:00/500m
→ rowing, 30 minutes (note: "2:00/500m" captured)
```

### Stationary Bike
```
/log bike 20min 150 watts
→ bike, 20 minutes, note: "150 watts"
```

## Backdating (Yesterday or Specific Date)

### Yesterday
```
/log yesterday: squat 315x5x3 rpe8 felt strong
→ Saved to 2026-01-31.jsonl (if today is 2026-02-01)
```

### Specific Date
```
/log 2026-01-30: deadlift 405x1x5
→ Saved to 2026-01-30.jsonl
```

## Exercise Name Aliases

The parser accepts many aliases for exercises:

| Canonical | Aliases |
|-----------|---------|
| squat | sq |
| bench_press | bench, bp |
| deadlift | dl |
| ohp | op, press, overhead press |
| barbell_row | row, bent over row |
| pull_up | pullup |
| weighted_pull_up | weighted pull-up, weighted pullup |
| treadmill | tm |
| rowing | rower, row machine |
| stationary_bike | bike |

## Invalid/Error Cases

### Unknown Exercise
```
/log foo 225x5x3
→ ❌ Unknown exercise: "foo". Could not normalize.
```

### Invalid Format
```
/log squat 315-5-3
→ ❌ Invalid weight/reps format: "315-5-3". Expected format like "225x5x3"
```

### Missing Exercise
```
/log 315x5x3
→ ❌ No exercise specified
```

## Database Output Examples

### Strength Workout (saved to JSONL)
```json
{"ts":"2026-02-01T11:29:48-08:00","type":"strength","exercise":"squat","unit":"lb","sets":[{"weight":315,"reps":5},{"weight":315,"reps":5},{"weight":315,"reps":5}],"rpe":8,"notes":"felt strong","source":"telegram","raw":"/log squat 315x5x3 rpe8 felt strong"}
```

### Machine Workout
```json
{"ts":"2026-01-31T11:41:44-08:00","type":"machine","exercise":"face_pulls","unit":"lb","sets":[{"weight":60,"reps":15},{"weight":60,"reps":15},{"weight":60,"reps":15}],"source":"telegram","raw":"/log yesterday: face pulls 60x3x15"}
```

### Cardio Workout
```json
{"ts":"2026-02-01T11:29:51-08:00","type":"cardio","modality":"treadmill","duration_min":10,"speed_mph":3.2,"incline_percent":15,"distance_miles":3.0,"notes":"steady pace","source":"telegram","raw":"/log treadmill 1 degree incline, 7.2 mph, 3.0 miles"}
```

## Testing Locally

```bash
# Test the parser directly
node src/parser.js "/log squat 315x5x3 rpe8 felt strong"

# Test the handler
node src/handler.js "/log squat 315x5x3 rpe8 felt strong"

# Test yesterday's date
node src/parser.js "/log yesterday: squat 315x5x3"

# Test specific date
node src/parser.js "/log 2026-01-30: deadlift 405x5x1"
```
