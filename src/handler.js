#!/usr/bin/env node
/**
 * Workout Log Handler
 * Processes /log messages and saves them
 */

const { parseWorkoutLog, writeWorkoutLog } = require('./parser.js');

// Called when a message matching /log is received
function handleWorkoutMessage(message, source = 'telegram', timestamp = null) {
  try {
    const { record, date } = parseWorkoutLog(message, message, timestamp);
    const filepath = writeWorkoutLog(record, date);
    
    return {
      success: true,
      message: `✅ Logged to ${filepath}`,
      record,
    };
  } catch (err) {
    return {
      success: false,
      error: err.message,
      message: `❌ ${err.message}`,
    };
  }
}

module.exports = { handleWorkoutMessage };

// CLI
if (require.main === module) {
  const message = process.argv[2];
  if (!message) {
    console.error('Usage: handle-workout-log.js "/log squat 225x5x3 rpe8"');
    process.exit(1);
  }

  const result = handleWorkoutMessage(message);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}
