#!/usr/bin/env node
/**
 * Database Verification Script
 * Validates JSONL files against the parser logic to ensure data integrity.
 * 
 * Usage:
 *   node scripts/verify-db.js <path-to-db-dir>
 */

const fs = require('fs');
const path = require('path');
const { parseWorkoutLog } = require('../src/parser.js');

// Colors for output
const colors = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m"
};

let errorCount = 0;
let fileCount = 0;
let recordCount = 0;

function deepCompare(obj1, obj2, path = '') {
  if (obj1 === obj2) return null;

  if (typeof obj1 !== typeof obj2) {
    return `${path}: Type mismatch (${typeof obj1} vs ${typeof obj2})`;
  }

  if (Array.isArray(obj1)) {
    if (!Array.isArray(obj2)) return `${path}: Expected array`;
    if (obj1.length !== obj2.length) return `${path}: Length mismatch (${obj1.length} vs ${obj2.length})`;
    for (let i = 0; i < obj1.length; i++) {
      const err = deepCompare(obj1[i], obj2[i], `${path}[${i}]`);
      if (err) return err;
    }
    return null;
  }

  if (typeof obj1 === 'object' && obj1 !== null) {
    const keys1 = Object.keys(obj1).sort();
    
    for (const key of keys1) {
       if (!Object.prototype.hasOwnProperty.call(obj2, key)) {
           return `${path}: Missing key '${key}'`;
       }
       const err = deepCompare(obj1[key], obj2[key], path ? `${path}.${key}` : key);
       if (err) return err;
    }
    return null;
  }

  return `${path}: Value mismatch ('${obj1}' vs '${obj2}')`;
}

function validateRecord(record) {
  const errors = [];

  if (!record.raw) {
    if (!record.exercise && !record.modality) errors.push('Missing exercise/modality and no raw string');
    return errors;
  }

  try {
    // Re-parse the raw string using the record's timestamp
    const { record: parsedRecord } = parseWorkoutLog(record.raw, null, record.ts);

    // Fields to compare
    const fieldsToCheck = [
      'type', 'exercise', 'modality', 
      'sets', 
      'rpe', 'notes', 'unit', 
      'duration_min', 'speed_mph', 'incline_percent', 'distance_miles'
    ];

    fieldsToCheck.forEach(field => {
      // If parsed record has it, DB record must match
      if (parsedRecord[field] !== undefined) {
        if (record[field] === undefined) {
           errors.push(`Missing field '${field}' (expected '${JSON.stringify(parsedRecord[field])}')`);
        } else {
           const err = deepCompare(parsedRecord[field], record[field], field);
           if (err) errors.push(err);
        }
      }
    });

  } catch (err) {
    errors.push(`Parser failed on raw string: ${err.message}`);
  }

  return errors;
}

function processFile(filePath) {
  fileCount++;
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  
  lines.forEach((line, idx) => {
    if (!line.trim()) return; // Skip empty lines
    
    try {
      const record = JSON.parse(line);
      recordCount++;
      const validationErrors = validateRecord(record);
      
      if (validationErrors.length > 0) {
        console.log(`${colors.red}FAIL${colors.reset} ${filePath}:${idx + 1}`);
        validationErrors.forEach(err => console.log(`  - ${err}`));
        console.log(`  Raw: ${record.raw}`);
        errorCount++;
      }
    } catch (e) {
      console.log(`${colors.red}ERROR${colors.reset} ${filePath}:${idx + 1} - Invalid JSON`);
      console.log(`  ${e.message}`);
      errorCount++;
    }
  });
}

function walkDir(dir) {
  const files = fs.readdirSync(dir);
  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      walkDir(fullPath);
    } else if (file.endsWith('.jsonl')) {
      processFile(fullPath);
    }
  });
}

// Main execution
const dbDir = process.argv[2];

if (!dbDir) {
  console.error('Usage: node scripts/verify-db.js <path-to-db-dir>');
  process.exit(1);
}

const absolutePath = path.resolve(dbDir);
console.log(`${colors.blue}Starting verification of ${absolutePath}...${colors.reset}`);

if (fs.existsSync(absolutePath)) {
  walkDir(absolutePath);
} else {
  console.error(`Directory not found: ${absolutePath}`);
  process.exit(1);
}

console.log(`\n${colors.blue}Verification Complete${colors.reset}`);
console.log(`Files checked: ${fileCount}`);
console.log(`Records checked: ${recordCount}`);

if (errorCount === 0) {
    console.log(`${colors.green}All records valid!${colors.reset}`);
} else {
    console.log(`${colors.red}Found ${errorCount} errors.${colors.reset}`);
    process.exit(1);
}
