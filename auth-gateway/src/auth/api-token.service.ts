import { Injectable } from '@nestjs/common';
import { randomUUID } from 'crypto';
import { config } from '../config';

// In-memory store of issued API tokens; they are lost on restart, like in the Rust version.
// Tokens expire so that repeated /init calls can't grow the store without bound.
@Injectable()
export class ApiTokenService {
  private readonly tokens = new Map<string, number>();

  issue(): string {
    this.pruneExpired();
    const token = randomUUID();
    this.tokens.set(token, Date.now() + config.apiTokenExpiresIn * 1000);
    return token;
  }

  isValid(token: string | undefined): boolean {
    const expiresAt = token ? this.tokens.get(token) : undefined;
    return expiresAt !== undefined && expiresAt > Date.now();
  }

  private pruneExpired() {
    const now = Date.now();
    for (const [token, expiresAt] of this.tokens) {
      if (expiresAt <= now) this.tokens.delete(token);
    }
  }
}
