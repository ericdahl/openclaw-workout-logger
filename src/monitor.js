#!/usr/bin/env node
/**
 * Workout Log Monitor
 * Periodically checks for new /log messages from Telegram and processes them
 * Stores state of processed messages in a JSON file to avoid duplicates
 */

const fs = require('fs');
const path = require('path');
const { handleWorkoutMessage } = require('./handler.js');

const STATE_FILE = path.join(__dirname, '..', '.state.json');

// Authorized Telegram user ID (from environment or default)
const AUTHORIZED_TELEGRAM_ID = process.env.AUTHORIZED_TELEGRAM_ID || null;

function loadState() {
  try {
    if (fs.existsSync(STATE_FILE)) {
      return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    }
  } catch (err) {
    console.error('Failed to load state:', err.message);
  }
  return { processed_message_ids: [] };
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf8');
}

// This would be called by a cron job or message handler
function processMessage(messageId, messageText, timestamp, userId = null) {
  const state = loadState();

  // Skip if already processed
  if (state.processed_message_ids.includes(messageId)) {
    console.log(`Already processed message ${messageId}, skipping.`);
    return { skipped: true };
  }

  // Only process messages starting with /log
  if (!messageText.startsWith('/log ')) {
    return { skipped: true };
  }

  // Check authorization
  if (!AUTHORIZED_TELEGRAM_ID) {
    console.error('ERROR: AUTHORIZED_TELEGRAM_ID environment variable not set');
    return { skipped: true, error: 'AUTHORIZED_TELEGRAM_ID not configured' };
  }

  // Only process from authorized user
  if (userId && userId !== AUTHORIZED_TELEGRAM_ID) {
    return { skipped: true, reason: 'Not from authorized user' };
  }

  console.log(`Processing message ${messageId}: ${messageText}`);

  const result = handleWorkoutMessage(messageText, 'telegram', timestamp);

  if (result.success) {
    state.processed_message_ids.push(messageId);
    saveState(state);
    console.log(`✅ Success: ${result.message}`);
  } else {
    console.log(`❌ Failed: ${result.message}`);
  }

  return result;
}

module.exports = { processMessage, loadState, saveState };

// CLI for testing
if (require.main === module) {
  const messageId = process.argv[2];
  const messageText = process.argv[3];
  const timestamp = process.argv[4] || new Date().toISOString();

  if (!messageId || !messageText) {
    console.error('Usage: workout-monitor.js <messageId> <messageText> [timestamp]');
    process.exit(1);
  }

  const result = processMessage(messageId, messageText, timestamp);
  console.log(JSON.stringify(result, null, 2));
}
