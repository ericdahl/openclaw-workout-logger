#!/usr/bin/env node
/**
 * Workout Log Formatter
 * Converts JSON records back into concise human-readable strings.
 */

const fs = require('fs');
const readline = require('readline');

// Helper to capitalize words
function capitalize(str) {
  if (!str) return '';
  return str.split(/[_\s]+/).map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

// Format a list of sets into a concise string
// e.g. "315x5x3" or "315x5, 315x4" or "20, 20, 25"
function formatSets(sets, unit = 'lb') {
  if (!sets || sets.length === 0) return 'No sets';

  // Group by weight
  const groups = [];
  let currentGroup = null;

  for (const set of sets) {
    const weight = set.weight !== undefined ? set.weight : null;
    const reps = set.reps;
    const failed = set.failed ? ' (fail)' : '';

    if (currentGroup && currentGroup.weight === weight) {
      currentGroup.reps.push(`${reps}${failed}`);
    } else {
      if (currentGroup) groups.push(currentGroup);
      currentGroup = { weight, reps: [`${reps}${failed}`] };
    }
  }
  if (currentGroup) groups.push(currentGroup);

  // Format groups
  return groups.map(g => {
    // Check if all reps are the same
    const allSame = g.reps.every(r => r === g.reps[0]);
    const count = g.reps.length;
    const repStr = allSame && count > 1 ? `${count}x${g.reps[0]}` : g.reps.join(', ');

    if (g.weight !== null) {
      // Strength: "315 lb: 5x5" or just "315x5x5" style?
      // User asked for concise. "315x5x5" is classic.
      // But if reps vary: "315x5,4,3"
      if (allSame && count > 1) {
        return `${g.weight}x${count}x${g.reps[0]}`; // 315x5x5
      } else if (count === 1) {
         return `${g.weight}x${g.reps[0]}`;
      } else {
        return `${g.weight}x[${repStr}]`;
      }
    } else {
      // Bodyweight: "20, 20, 25" or "5x10"
      if (allSame && count > 1) {
        return `${count}x${g.reps[0]} reps`;
      }
      return `${repStr} reps`;
    }
  }).join(', ');
}

function formatRecord(record) {
  const date = record.ts.split('T')[0];
  const name = capitalize(record.exercise || record.modality);
  const notes = record.notes ? ` - "${record.notes}"` : '';
  const rpe = record.rpe ? ` @ RPE ${record.rpe}` : '';

  let summary = '';

  if (record.type === 'cardio') {
    const parts = [];
    if (record.duration_min) parts.push(`${record.duration_min} min`);
    if (record.distance_miles) parts.push(`${record.distance_miles} mi`);
    if (record.speed_mph) parts.push(`${record.speed_mph} mph`);
    if (record.incline_percent) parts.push(`${record.incline_percent}% inc`);
    summary = parts.join(', ');
  } else {
    // Strength / Machine / Bodyweight
    summary = formatSets(record.sets, record.unit);
  }

  return `[${date}] ${name}: ${summary}${rpe}${notes}`;
}

// Export
module.exports = { formatRecord };

// CLI
if (require.main === module) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  rl.on('line', (line) => {
    if (!line.trim()) return;
    try {
      const record = JSON.parse(line);
      console.log(formatRecord(record));
    } catch (e) {
      // Ignore invalid JSON lines or print error?
      // Silently ignore to be pipe-friendly
    }
  });
}
