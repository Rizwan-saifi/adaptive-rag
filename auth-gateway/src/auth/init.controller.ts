import { Controller, HttpCode, Logger, Post } from '@nestjs/common';
import { ApiTokenService } from './api-token.service';

@Controller()
export class InitController {
  private readonly logger = new Logger(InitController.name);

  constructor(private readonly apiTokens: ApiTokenService) {}

  // Public: hands out the API token required by the other endpoints.
  @Post('init')
  @HttpCode(200)
  init() {
    this.logger.log('Init API called');
    return { api_token: this.apiTokens.issue(), jwt: null };
  }
}
