import { ConflictException, Injectable, Logger } from '@nestjs/common';
import * as argon2 from 'argon2';
import { DatabaseService } from '../database/database.service';

@Injectable()
export class UsersService {
  private readonly logger = new Logger(UsersService.name);

  constructor(private readonly database: DatabaseService) {}

  async create(username: string, password: string): Promise<void> {
    const hash = await argon2.hash(password, { type: argon2.argon2id });
    try {
      this.database.db
        .prepare('INSERT INTO users (username, password_hash) VALUES (?, ?)')
        .run(username, hash);
    } catch (e: any) {
      if (e?.code === 'SQLITE_CONSTRAINT_PRIMARYKEY') {
        throw new ConflictException('Username already exists');
      }
      throw e;
    }
    this.logger.log(`Created user: ${username}`);
  }

  async verify(username: string, password: string): Promise<boolean> {
    const row = this.database.db
      .prepare('SELECT password_hash FROM users WHERE username = ?')
      .get(username) as { password_hash: string } | undefined;
    if (!row) return false;
    try {
      return await argon2.verify(row.password_hash, password);
    } catch (e) {
      this.logger.error(`Failed to verify password hash for ${username}: ${e}`);
      return false;
    }
  }
}
