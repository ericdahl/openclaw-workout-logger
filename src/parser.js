#!/usr/bin/env node
/**
 * Workout Log Parser
 * Parses /log messages from Telegram and writes to JSONL
 */

const fs = require('fs');
const path = require('path');

// Exercise normalization map
const EXERCISE_MAP = {
  // Strength exercises
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
  'barbell row': 'barbell_row',
  'bent over row': 'barbell_row',
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

  // Dumbbell exercises
  'db bench': 'dumbbell_bench_press',
  'dumbbell bench': 'dumbbell_bench_press',
  'db press': 'dumbbell_bench_press',

  // Bodyweight
  'dragon': 'dragon_flag',
  'dragon flag': 'dragon_flag',
  'dragon flags': 'dragon_flag',

  // Machines
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

  // Cardio
  'treadmill': 'treadmill',
  'tm': 'treadmill',
  'rowing': 'rowing',
  'rower': 'rowing',
  'row machine': 'rowing',
  'bike': 'stationary_bike',
  'stationary bike': 'stationary_bike',
};

// Exercise type classification
const EXERCISE_TYPE = {
  'squat': 'strength',
  'bench_press': 'strength',
  'deadlift': 'strength',
  'ohp': 'strength',
  'barbell_row': 'strength',
  'weighted_dip': 'strength',
  'dumbbell_bench_press': 'strength',
  'dip': 'bodyweight',
  'chin_up': 'bodyweight',
  'weighted_chin_up': 'bodyweight',
  'pull_up': 'bodyweight',
  'weighted_pull_up': 'bodyweight',
  'dragon_flag': 'bodyweight',
  'ab_crunch': 'machine',
  'cybex_ab_crunch': 'machine',
  'leg_press': 'machine',
  'hack_squat': 'machine',
  'face_pulls': 'machine',
  'lat_pulldown': 'machine',
  'treadmill': 'cardio',
  'rowing': 'cardio',
  'stationary_bike': 'cardio',
};

// Parse date modifier (e.g., "yesterday", "2026-01-31")
function parseDate(dateStr, baseDate = new Date()) {
  if (!dateStr) return baseDate;
  
  const lower = dateStr.toLowerCase().trim();
  
  if (lower === 'yesterday') {
    const d = new Date(baseDate);
    d.setDate(d.getDate() - 1);
    return d;
  }
  
  if (lower === 'today') {
    return baseDate;
  }
  
  // Try parsing as ISO date (YYYY-MM-DD)
  const match = dateStr.match(/^\d{4}-\d{2}-\d{2}$/);
  if (match) {
    return new Date(dateStr + 'T00:00:00');
  }
  
  return null;
}

// Normalize exercise name
function normalizeExercise(exerciseStr) {
  const lower = exerciseStr.toLowerCase().trim();
  return EXERCISE_MAP[lower] || null;
}

// Parse a comma-separated rep list like "20,20,25" or "2,1,x"
// Returns array of rep counts, where 'x' becomes 0 with failed flag
function parseRepList(repStr) {
  const parts = repStr.split(',');
  return parts.map(p => {
    const trimmed = p.trim().toLowerCase();
    if (trimmed === 'x' || trimmed === 'f' || trimmed === 'fail') {
      return { reps: 0, failed: true };
    }
    return { reps: parseInt(trimmed) };
  });
}

// Parse strength/bodyweight workout with flexible formats:
// - "225x5x3" = 225 lb, 5 sets, 3 reps each
// - "20,20,25" = bodyweight, sets of 20, 20, 25 reps
// - "405 2,1,x" = 405 lb, sets of 2, 1, failed
// - "2x90 4x10,7" = dumbbell 90lb each, 4 sets of 10 + 1 set of 7
// - "7x10" = 7 sets of 10 reps (bodyweight)
function parseStrengthWorkout(exerciseNorm, rest, isoTs) {
  const exerciseType = EXERCISE_TYPE[exerciseNorm];
  const isBodyweight = exerciseType === 'bodyweight';

  const parts = rest.trim().split(/\s+/);
  let sets = [];
  let weight = null;
  let notes = '';
  let rpe = null;
  let partsConsumed = 0;
  let isDumbbell = exerciseNorm.includes('dumbbell');

  if (parts.length === 0 || parts[0] === '') {
    throw new Error('No weight/reps format found');
  }

  const firstPart = parts[0];

  // Format: comma-separated reps only (bodyweight): "20,20,25"
  if (firstPart.match(/^[\d,x]+$/) && firstPart.includes(',')) {
    const repList = parseRepList(firstPart);
    sets = repList.map(r => r.failed ? { reps: 0, failed: true } : { reps: r.reps });
    partsConsumed = 1;
  }
  // Format: dumbbell "2x90 4x10,7" - pair notation then sets
  else if (isDumbbell && firstPart.match(/^2x(\d+)$/i)) {
    const dbMatch = firstPart.match(/^2x(\d+)$/i);
    weight = parseFloat(dbMatch[1]); // per dumbbell
    partsConsumed = 1;

    // Parse sets format: "4x10,7" means 4 sets of 10, then 1 set of 7
    if (parts.length > 1) {
      const setsFormat = parts[1];
      const setsMatch = setsFormat.match(/^(\d+)x([\d,]+)$/i);
      if (setsMatch) {
        const uniformSets = parseInt(setsMatch[1]);
        const repsList = setsMatch[2].split(',').map(r => parseInt(r.trim()));
        // First number after 'x' is reps for uniformSets, rest are additional sets
        const mainReps = repsList[0];
        for (let i = 0; i < uniformSets; i++) {
          sets.push({ weight, reps: mainReps });
        }
        // Additional sets with different reps
        for (let i = 1; i < repsList.length; i++) {
          sets.push({ weight, reps: repsList[i] });
        }
        partsConsumed = 2;
      }
    }
    if (sets.length > 0) {
      notes = 'per dumbbell';
    }
  }
  // Format: "NxM" where context determines meaning
  else if (firstPart.match(/^(\d+(?:\.\d+)?)x(\d+)$/i)) {
    const match = firstPart.match(/^(\d+(?:\.\d+)?)x(\d+)$/i);
    const num1 = parseFloat(match[1]);
    const num2 = parseInt(match[2]);

    // Check if there's a third part: "225x5x3"
    if (parts.length > 1 && parts[1].match(/^x?(\d+)$/i)) {
      // Format: weight x sets x reps
      const thirdMatch = parts[1].match(/^x?(\d+)$/i);
      weight = num1;
      const setCount = num2;
      const repsPerSet = parseInt(thirdMatch[1]);
      for (let i = 0; i < setCount; i++) {
        sets.push({ weight, reps: repsPerSet });
      }
      partsConsumed = 2;
    }
    // For bodyweight: "7x10" = 7 sets of 10 reps
    else if (isBodyweight) {
      const setCount = num1;
      const repsPerSet = num2;
      for (let i = 0; i < setCount; i++) {
        sets.push({ reps: repsPerSet });
      }
      partsConsumed = 1;
    }
    // For strength: "225x5" could be 225lb x 5 reps (1 set)
    else {
      weight = num1;
      sets.push({ weight, reps: num2 });
      partsConsumed = 1;
    }
  }
  // Format: "NxMxP" all in one: weight x sets x reps
  else if (firstPart.match(/^(\d+(?:\.\d+)?)x(\d+)x(\d+)$/i)) {
    const match = firstPart.match(/^(\d+(?:\.\d+)?)x(\d+)x(\d+)$/i);
    weight = parseFloat(match[1]);
    const setCount = parseInt(match[2]);
    const repsPerSet = parseInt(match[3]);
    for (let i = 0; i < setCount; i++) {
      sets.push({ weight, reps: repsPerSet });
    }
    partsConsumed = 1;
  }
  // Format: weight followed by comma-separated reps: "405 2,1,x"
  else if (firstPart.match(/^\d+(?:\.\d+)?$/) && parts.length > 1 && parts[1].match(/^[\d,x]+$/i)) {
    weight = parseFloat(firstPart);
    const repList = parseRepList(parts[1]);
    sets = repList.map(r => {
      const set = { weight, reps: r.reps };
      if (r.failed) set.failed = true;
      return set;
    });
    partsConsumed = 2;
  }
  else {
    throw new Error(`Could not parse format: "${rest}". Try formats like "225x3x5", "20,20,25", or "405 2,1,x"`);
  }

  // Parse remaining parts for RPE and notes
  const remaining = parts.slice(partsConsumed).join(' ');
  const rpeMatch = remaining.match(/rpe(\d+)/i);
  if (rpeMatch) {
    rpe = parseInt(rpeMatch[1]);
  }
  const notesFromRemaining = remaining.replace(/rpe\d+/gi, '').trim();
  if (notesFromRemaining) {
    notes = notes ? `${notes}; ${notesFromRemaining}` : notesFromRemaining;
  }

  const record = {
    ts: isoTs,
    type: exerciseType,
    exercise: exerciseNorm,
  };

  if (weight !== null) {
    record.unit = 'lb';
  }
  record.sets = sets;

  if (rpe !== null) record.rpe = rpe;
  if (notes) record.notes = notes;

  return record;
}

// Parse cardio workout (e.g., "treadmill 10min 3.2mph incline15")
function parseCardioWorkout(exerciseNorm, rest, isoTs) {
  const lowerRest = rest.toLowerCase();
  
  const record = {
    ts: isoTs,
    type: 'cardio',
    modality: exerciseNorm,
  };

  // Duration: "10min" or "10 minutes"
  const durMatch = lowerRest.match(/(\d+(?:\.\d+)?)\s*min(?:ute)?s?/i);
  if (durMatch) {
    record.duration_min = parseFloat(durMatch[1]);
  }

  // Speed: "3.2mph" or "7.2 mph"
  const speedMatch = lowerRest.match(/(\d+(?:\.\d+)?)\s*mph/i);
  if (speedMatch) {
    record.speed_mph = parseFloat(speedMatch[1]);
  }

  // Incline: "incline15", "15 degree incline", "1 degree incline", etc.
  const inclineMatch = lowerRest.match(/(\d+(?:\.\d+)?)\s*degree\s*incline|incline\s*(\d+(?:\.\d+)?)/i);
  if (inclineMatch) {
    const inclineValue = inclineMatch[1] || inclineMatch[2];
    record.incline_percent = parseFloat(inclineValue);
  }

  // Distance: "3.0 miles" or "5 miles"
  const distMatch = lowerRest.match(/(\d+(?:\.\d+)?)\s*miles?/i);
  if (distMatch) {
    record.distance_miles = parseFloat(distMatch[1]);
  }

  // Extract remaining text as notes (remove extracted values)
  let notesText = rest;
  notesText = notesText.replace(/\d+(?:\.\d+)?\s*min(?:ute)?s?/gi, '');
  notesText = notesText.replace(/\d+(?:\.\d+)?\s*mph/gi, '');
  notesText = notesText.replace(/\d+(?:\.\d+)?\s*degree\s*incline/gi, '');
  notesText = notesText.replace(/incline\s*\d+(?:\.\d+)?/gi, '');
  notesText = notesText.replace(/\d+(?:\.\d+)?\s*miles?/gi, '');
  notesText = notesText.replace(/[,\s]+/g, ' ').trim();

  if (notesText) {
    record.notes = notesText;
  }

  return record;
}

// Main parser
function parseWorkoutLog(message, rawMessage = null, timestamp = null) {
  if (!message.startsWith('/log ')) {
    throw new Error('Message must start with /log');
  }

  const content = message.slice(5).trim();
  
  // Check for date modifier at the start
  let dateStr = null;
  let logContent = content;
  
  const dateMatch = content.match(/^(yesterday|today|\d{4}-\d{2}-\d{2})\s*:\s*/i);
  if (dateMatch) {
    dateStr = dateMatch[1];
    logContent = content.slice(dateMatch[0].length);
  }

  // Parse date
  let now = timestamp ? new Date(timestamp) : new Date();
  if (dateStr) {
    const parsed = parseDate(dateStr, now);
    if (!parsed) {
      throw new Error(`Could not parse date: "${dateStr}"`);
    }
    now = parsed;
  }

  // Adjust to Pacific timezone
  const baseTime = now;
  
  // Get Pacific time components
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Los_Angeles',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });

  const parts = formatter.format(baseTime);
  const [m, d, y, h, min, s] = parts.match(/(\d+)/g);
  
  // Determine offset (PST = -08:00, PDT = -07:00)
  // February is always PST
  const offset = '-08:00';
  
  const isoTs = `${y}-${m}-${d}T${h}:${min}:${s}${offset}`;

  // Store the date for file path
  const year = y;
  const month = m;
  const day = d;

  // Split exercise name from rest
  const words = logContent.split(/\s+/);
  if (words.length === 0) {
    throw new Error('No exercise specified');
  }

  let exerciseName = words[0];
  let exerciseNorm = normalizeExercise(exerciseName);

  // Try combining first two words (e.g., "ab crunch")
  if (!exerciseNorm && words.length > 1) {
    exerciseName = `${words[0]} ${words[1]}`;
    exerciseNorm = normalizeExercise(exerciseName);
    words.shift(); // Remove first word from further processing
  }

  if (!exerciseNorm) {
    throw new Error(`Unknown exercise: "${exerciseName}". Could not normalize.`);
  }

  const rest = words.slice(1).join(' ');
  const exerciseType = EXERCISE_TYPE[exerciseNorm];

  let record;

  if (exerciseType === 'cardio') {
    record = parseCardioWorkout(exerciseNorm, rest, isoTs);
  } else if (exerciseType === 'strength' || exerciseType === 'machine' || exerciseType === 'bodyweight') {
    record = parseStrengthWorkout(exerciseNorm, rest, isoTs);
  } else {
    throw new Error(`Unknown exercise type for "${exerciseNorm}"`);
  }

  record.source = 'telegram';
  record.raw = message;

  return {
    record,
    date: `${year}-${month}-${day}`,
  };
}

// Write to JSONL file
function writeWorkoutLog(record, date) {
  const [year, month, day] = date.split('-');
  const dbDir = '/srv/openclaw/db';
  const filepath = path.join(dbDir, year, month, `${day}.jsonl`);

  // Ensure directory exists
  const dir = path.dirname(filepath);
  fs.mkdirSync(dir, { recursive: true });

  // Append to JSONL
  fs.appendFileSync(filepath, JSON.stringify(record) + '\n', 'utf8');
  
  return filepath;
}

// Export for use as module
module.exports = {
  parseWorkoutLog,
  writeWorkoutLog,
  normalizeExercise,
};

// CLI usage
if (require.main === module) {
  const message = process.argv[2];
  if (!message) {
    console.error('Usage: workout-parser.js "/log squat 225x5x3 rpe8"');
    process.exit(1);
  }

  try {
    const { record, date } = parseWorkoutLog(message);
    const filepath = writeWorkoutLog(record, date);
    console.log(JSON.stringify(record, null, 2));
    console.log(`\nSaved to: ${filepath}`);
  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
}
