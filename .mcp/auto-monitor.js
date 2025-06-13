#!/usr/bin/env node

// Auto-start autonomous monitoring
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('🤖 Starting autonomous AI safety monitoring...');

// Find the ai-agent-handoff server directory
const serverPath = path.resolve(__dirname, '../node_modules/@modelcontextprotocol/mcp');
const altServerPath = path.resolve(__dirname, '../../../ai-agent-handoff/server');

let mcpServerPath;
if (fs.existsSync(serverPath)) {
    mcpServerPath = serverPath;
} else if (fs.existsSync(altServerPath)) {
    mcpServerPath = altServerPath;
} else {
    console.error('❌ Cannot find MCP server. Make sure ai-agent-handoff is linked.');
    process.exit(1);
}

// Start the server
const server = spawn('node', [path.join(mcpServerPath, 'src/index.js')], {
    cwd: process.cwd(),
    stdio: 'inherit',
    env: { ...process.env, MCP_PROJECT_ROOT: process.cwd() }
});

server.on('error', (err) => {
    console.error('Failed to start autonomous monitoring:', err);
});

process.on('SIGINT', () => {
    server.kill();
    process.exit();
});

console.log('✅ Autonomous monitoring active - no commands needed!');
console.log('📝 AI agents should read HANDOFF.md to get started.');