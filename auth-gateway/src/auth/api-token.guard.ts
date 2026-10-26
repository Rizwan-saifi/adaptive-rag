import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from '@nestjs/common';
import { Request } from 'express';
import { ApiTokenService } from './api-token.service';

@Injectable()
export class ApiTokenGuard implements CanActivate {
  constructor(private readonly apiTokens: ApiTokenService) {}

  canActivate(context: ExecutionContext): boolean {
    const req = context.switchToHttp().getRequest<Request>();
    if (!this.apiTokens.isValid(req.header('x-api-token'))) {
      throw new UnauthorizedException('Invalid API token');
    }
    return true;
  }
}
