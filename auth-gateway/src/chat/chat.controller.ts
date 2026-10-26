import { Body, Controller, Headers, HttpCode, Post, UseGuards } from '@nestjs/common';
import { ApiTokenGuard } from '../auth/api-token.guard';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { ChatRequestDto } from './chat.dto';
import { ChatService } from './chat.service';

@Controller()
@UseGuards(ApiTokenGuard, JwtAuthGuard)
export class ChatController {
  constructor(private readonly chat: ChatService) {}

  // The JWT is forwarded so the RAG service can identify the user. Without a
  // conversation_id, all of the user's messages share one 'default' conversation.
  @Post('chat')
  @HttpCode(200)
  async ask(@Body() body: ChatRequestDto, @Headers('authorization') auth: string) {
    const jwt = auth.replace(/^Bearer /, '');
    const conversationId = body.conversation_id ?? 'default';
    return { answer: await this.chat.ask(body.query, conversationId, jwt) };
  }
}
