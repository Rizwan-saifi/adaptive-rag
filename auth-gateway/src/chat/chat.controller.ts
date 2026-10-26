import { Body, Controller, Headers, HttpCode, Post, UseGuards } from '@nestjs/common';
import { ApiTokenGuard } from '../auth/api-token.guard';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { ChatRequestDto } from './chat.dto';
import { ChatService } from './chat.service';

@Controller()
@UseGuards(ApiTokenGuard, JwtAuthGuard)
export class ChatController {
  constructor(private readonly chat: ChatService) {}

  // The JWT doubles as the chat session id, and is forwarded so the RAG
  // service can identify the user.
  @Post('chat')
  @HttpCode(200)
  async ask(@Body() body: ChatRequestDto, @Headers('authorization') auth: string) {
    const jwt = auth.replace(/^Bearer /, '');
    return { answer: await this.chat.ask(body.query, jwt) };
  }
}
