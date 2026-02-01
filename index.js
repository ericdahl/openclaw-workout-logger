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
  const [, , ...args] = process.argv;
  
  if (args.length === 0) {
    console.log(`
Workout Logger CLI

Usage:
  node index.js "<message>" [timestamp]
  
Examples:
  node index.js "/log squat 315x5x3 rpe8 felt strong"
  node index.js "/log yesterday: face pulls 60x3x15"
  node index.js "/log treadmill 10min 3.2mph incline15" "2026-02-01T18:34:41Z"

For more info, see README.md or examples/test-cases.md
    `);
    process.exit(0);
  }

  const message = args[0];
  const timestamp = args[1];

  const result = handleWorkoutMessage(message, 'telegram', timestamp);
  console.log(JSON.stringify(result, null, 2));
  process.exit(result.success ? 0 : 1);
}
