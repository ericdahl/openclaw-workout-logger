#!/usr/bin/env node
/**
 * Workout Logger Entry Point
 * Main export for use as a module or CLI
 */

const { handleWorkoutMessage } = require('./src/handler.js');
const { processMessage } = require('./src/monitor.js');

module.exports = {
  handleWorkoutMessage,
  processMessage,
};

// CLI usage
if (require.main === module) {
  const [, , ...rawArgs] = process.argv;
  
  // Parse arguments
  let dryRun = false;
  let dbDir = undefined;
  const args = [];

  for (let i = 0; i < rawArgs.length; i++) {
    const arg = rawArgs[i];
    if (arg === '--dry-run') {
      dryRun = true;
    } else if (arg === '--db-dir') {
      dbDir = rawArgs[i + 1];
      i++; // Skip next arg
    } else {
      args.push(arg);
    }
  }

  if (args.length === 0) {
    console.log(`
Workout Logger CLI

Usage:
  node index.js [options] "<message>" [timestamp]
  
Examples:
  node index.js "/log squat 315x5x3 rpe8 felt strong"
  node index.js --dry-run "/log squat 315x5x3"
  node index.js --db-dir ./my-db "/log pull-up 20,20,20"
  node index.js "/log treadmill 10min 3.2mph incline15" "2026-02-01T18:34:41Z"

Options:
  --dry-run         Parse and output to stdout without writing to database
  --db-dir <path>   Custom database directory (default: /srv/openclaw/db)

For more info, see README.md or examples/test-cases.md
    `);
    process.exit(0);
  }

  const message = args[0];
  const timestamp = args[1];

  if (!message) {
    console.error('Error: message required');
    process.exit(1);
  }

  const result = handleWorkoutMessage(message, 'telegram', timestamp, { dryRun, dbDir });
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}
