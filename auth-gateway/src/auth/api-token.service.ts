import { Injectable } from '@nestjs/common';
import { randomUUID } from 'crypto';

// In-memory store of issued API tokens; they are lost on restart, like in the Rust version.
@Injectable()
export class ApiTokenService {
  private readonly tokens = new Set<string>();

  issue(): string {
    const token = randomUUID();
    this.tokens.add(token);
    return token;
  }

  isValid(token: string | undefined): boolean {
    return !!token && this.tokens.has(token);
  }
}
