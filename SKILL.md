---
name: workout-logger
description: Logs fitness activities and notes to a local JSONL database with git integration.
enabled: true
metadata:
  openclaw:
    requires:
      bins: ["workout-logger"]
    permissions:
      execution: "safe"
---

# Workout Logger

This skill allows the agent to log workouts and notes using the `workout-logger` CLI. 

## Usage Rules

1.  **Strict Command Syntax:** The CLI strictly separates workouts (`log`) from context (`note`).
    * If the user describes a physical exercise (sets, reps, cardio), use `log`.
    * If the user describes a feeling, injury, or general thought *without* specific metrics, use `note`.
2.  **Date Handling:** * If the user starts with "Yesterday I did...", prepend `yesterday: ` to the log string.
    * If the user specifies a date (e.g., "On Jan 30th..."), prepend the date in `YYYY-MM-DD: ` format.

## Commands

### 1. Log Workout
**Signature:** `workout-logger log "<description>"`

The `<description>` string must follow these patterns:
* **Strength:** `<exercise> <weight>x<sets>x<reps> [rpe<N>]`
    * *Example:* "squat 315x5x3 rpe8" (315lbs, 5 sets of 3)
    * *Example:* "deadlift 405 1x5" (405lbs, 1 set of 5)
* **Bodyweight:** `<exercise> <reps>,<reps>,<reps>`
    * *Example:* "pull-up 20,15,12"
* **Cardio:** `<exercise> <duration> <intensity>`
    * *Example:* "treadmill 10min 3.2mph"

### 2. Add Note
**Signature:** `workout-logger note "<text>"`

Use this for qualitative feedback not attached to a specific lift.

## Examples

**User:** "Just hit bench press, 225 for 3 sets of 5, felt easy."
**Command:** `workout-logger log "bench 225x3x5 rpe6"`
*(Note: Agent infers RPE 6 from "felt easy" if not specified, or just omits it)*

**User:** "Yesterday I ran on the treadmill for 30 mins."
**Command:** `workout-logger log "yesterday: treadmill 30min"`

**User:** "My lower back is a bit sore today."
**Command:** `workout-logger note "Lower back sore"`

**User:** "Log 405 deadlift, 1 set of 5."
**Command:** `workout-logger log "deadlift 405 1x5"`