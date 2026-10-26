import { Injectable, OnModuleDestroy } from '@nestjs/common';
import Database from 'better-sqlite3';
import { config } from '../config';

@Injectable()
export class DatabaseService implements OnModuleDestroy {
  readonly db = new Database(config.dbPath);

  constructor() {
    this.db.exec(`CREATE TABLE IF NOT EXISTS users (
      username TEXT PRIMARY KEY,
      password_hash TEXT NOT NULL
    )`);
  }

  onModuleDestroy() {
    this.db.close();
  }
}
