import { INestApplication, ValidationPipe } from '@nestjs/common';

// Shared by main.ts and the tests so both run the app the same way.
export function configureApp(app: INestApplication) {
  app.setGlobalPrefix('api');
  app.useGlobalPipes(new ValidationPipe({ whitelist: true }));
  app.enableShutdownHooks();
}
