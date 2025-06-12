#!/usr/bin/env node

/**
 * TodoRead - lists unchecked markdown tasks in the project.
 *
 * Usage:
 *   node scripts/todoRead.js           # human-friendly output
 *   node scripts/todoRead.js --json    # machine-readable JSON
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Optional chalk colors if available
let chalk = {
  blue: (t) => t,
  yellow: (t) => t,
  green: (t) => t,
  red: (t) => t,
};
try {
  // Dynamically import so the dependency is optional
  const chalkPkg = await import('chalk');
  chalk = chalkPkg.default;
} catch (_) {
  /* silent: chalk not installed, continue without colors */
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const IGNORE_DIRS = new Set(['node_modules', '.git', '__pycache__', '.mcp', '.github', '.venv', '.env']);

function walk(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (IGNORE_DIRS.has(entry.name)) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(fullPath, files);
    } else if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }
  return files;
}

function collectTodos(baseDir) {
  const todoRegex = /- \[ \] .+/g;
  const todos = [];
  const mdFiles = walk(baseDir);

  for (const file of mdFiles) {
    const content = fs.readFileSync(file, 'utf8');
    const matches = content.match(todoRegex) || [];
    todos.push(
      ...matches.map((todo) => ({
        file: path.relative(baseDir, file),
        todo: todo.trim(),
      }))
    );
  }
  return todos;
}

(async function main() {
  const args = process.argv.slice(2);
  const jsonOut = args.includes('--json') || args.includes('-j');
  const baseDir = path.resolve(__dirname, '..');

  try {
    const todos = collectTodos(baseDir);

    if (jsonOut) {
      console.log(JSON.stringify(todos, null, 2));
      return;
    }

    if (todos.length === 0) {
      console.log(chalk.green('✓ No pending TODOs found!'));
      return;
    }

    console.log(chalk.blue(`Pending TODOs (${todos.length}):`));
    for (const { file, todo } of todos) {
      console.log(`${chalk.yellow(file)}: ${todo.replace(/^- \[ \] /, '')}`);
    }
  } catch (err) {
    console.error(chalk.red('TodoRead error:'), err.message);
    process.exit(1);
  }
})(); 