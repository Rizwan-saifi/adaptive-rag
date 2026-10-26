import 'reflect-metadata';
import { Logger } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { configureApp } from './app.setup';
import { config } from './config';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  configureApp(app);
  await app.listen(config.port, config.host);
  Logger.log(`Auth gateway listening on http://${config.host}:${config.port}/api`, 'Bootstrap');
}
bootstrap();
