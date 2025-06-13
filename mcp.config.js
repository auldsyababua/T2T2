module.exports = {
  "port": 3000,
  "host": "localhost",
  "workspace": {
    "scratchDir": ".scratch",
    "maxFileAge": 3600000,
    "allowedExtensions": [
      ".txt",
      ".md",
      ".json",
      ".log"
    ]
  },
  "session": {
    "contextFile": "SESSION_CONTEXT.md",
    "devLogFile": "dev_log.md",
    "updateInterval": 300000,
    "maxLogEntries": 100
  },
  "tools": {
    "enabled": [
      "checkEverything",
      "fixCommon",
      "explainError",
      "whenPortBlocked"
    ],
    "scriptDir": "scripts",
    "timeout": 30000
  },
  "logging": {
    "level": "info",
    "file": "logs/mcp.log",
    "maxSize": "10m",
    "maxFiles": 5
  }
};