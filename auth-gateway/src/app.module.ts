import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { config } from './config';
import { DatabaseService } from './database/database.service';
import { ApiTokenService } from './auth/api-token.service';
import { ApiTokenGuard } from './auth/api-token.guard';
import { JwtAuthGuard } from './auth/jwt-auth.guard';
import { InitController } from './auth/init.controller';
import { UsersController } from './users/users.controller';
import { UsersService } from './users/users.service';
import { ChatController } from './chat/chat.controller';
import { ChatService } from './chat/chat.service';

@Module({
  imports: [
    JwtModule.register({
      secret: config.jwtSecret,
      signOptions: { expiresIn: config.jwtExpiresIn },
    }),
  ],
  controllers: [InitController, UsersController, ChatController],
  providers: [
    DatabaseService,
    ApiTokenService,
    ApiTokenGuard,
    JwtAuthGuard,
    UsersService,
    ChatService,
  ],
})
export class AppModule {}
