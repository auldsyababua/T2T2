#!/usr/bin/env node

/**
 * TodoWrite - Add or complete TODO items in markdown files.
 *
 * Usage examples:
 *   node scripts/todoWrite.js --add "Implement login page" --file PRD.md
 *   node scripts/todoWrite.js --complete "Implement login page" --file PRD.md
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

let chalk = { blue: (t) => t, yellow: (t) => t, green: (t) => t, red: (t) => t };
try {
  const c = await import('chalk');
  chalk = c.default;
} catch (_) {}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function writeTodo({ add, complete, file }) {
  if (!add && !complete) {
    console.log(chalk.red('Provide --add or --complete option.'));
    process.exit(1);
  }

  const target = path.resolve(__dirname, '..', file || 'PRD.md');
  if (!fs.existsSync(target)) {
    console.log(chalk.red(`File not found: ${target}`));
    process.exit(1);
  }

  let content = fs.readFileSync(target, 'utf8');
  let updated = false;

  if (add) {
    const line = `- [ ] ${add.trim()}`;
    content += (content.endsWith('\n') ? '' : '\n') + line + '\n';
    updated = true;
    console.log(chalk.green(`✓ Added TODO to ${file}`));
  }

  if (complete) {
    const regex = new RegExp(`^- \\[ \] ${escapeRegExp(complete)}$`, 'm');
    if (regex.test(content)) {
      content = content.replace(regex, `- [x] ${complete}`);
      updated = true;
      console.log(chalk.green('✓ Marked TODO as completed'));
    } else {
      console.log(chalk.yellow('⚠️  Todo not found – perhaps already done?'));
    }
  }

  if (updated) {
    fs.writeFileSync(target, content);
  }
}

// Parse CLI args (very simple)
const args = process.argv.slice(2);
let addText = null;
let completeText = null;
let file = null;

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  switch (arg) {
    case '--add':
    case '-a':
      addText = args[++i];
      break;
    case '--complete':
    case '-c':
      completeText = args[++i];
      break;
    case '--file':
    case '-f':
      file = args[++i];
      break;
    default:
      break; // ignore unknown args
  }
}

writeTodo({ add: addText, complete: completeText, file }); 