#!/usr/bin/env node
/**
 * Workout Log Handler
 * Processes /log messages and saves them
 */

const { parseWorkoutLog, writeWorkoutLog } = require('./parser.js');

// Called when a message matching /log is received
function handleWorkoutMessage(message, source = 'telegram', timestamp = null, dryRun = false) {
  try {
    const { record, date } = parseWorkoutLog(message, message, timestamp);
    const filepath = writeWorkoutLog(record, date, dryRun);
    
    const statusMsg = dryRun ? 'Would log to' : 'Logged to';
    return {
      success: true,
      message: `✅ ${statusMsg} ${filepath}`,
      record,
      dryRun,
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
  let dryRun = false;
  let message = process.argv[2];

  if (message === '--dry-run') {
    dryRun = true;
    message = process.argv[3];
  }

  if (!message) {
    console.error('Usage: src/handler.js [--dry-run] "/log squat 225x5x3 rpe8"');
    process.exit(1);
  }

  const result = handleWorkoutMessage(message, 'telegram', null, dryRun);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}
