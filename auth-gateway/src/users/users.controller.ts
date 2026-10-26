import { Body, Controller, HttpCode, Post, UnauthorizedException, UseGuards } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ApiTokenGuard } from '../auth/api-token.guard';
import { CredentialsDto } from './user.dto';
import { UsersService } from './users.service';

@Controller()
@UseGuards(ApiTokenGuard)
export class UsersController {
  constructor(
    private readonly users: UsersService,
    private readonly jwt: JwtService,
  ) {}

  @Post('create_user')
  @HttpCode(200)
  async createUser(@Body() body: CredentialsDto) {
    await this.users.create(body.username, body.password);
    return { status: 'created' };
  }

  @Post('login')
  @HttpCode(200)
  async login(@Body() body: CredentialsDto) {
    if (!(await this.users.verify(body.username, body.password))) {
      throw new UnauthorizedException();
    }
    return { api_token: null, jwt: this.jwt.sign({ sub: body.username }) };
  }
}
