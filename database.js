require('dotenv').config();
const Database = require('better-sqlite3');
const path = require('path');

const dbPath = process.env.DATABASE_PATH || './database.sqlite';
const db = new Database(dbPath);

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )
`);

console.log('Database initialized at:', dbPath);

module.exports = db;
