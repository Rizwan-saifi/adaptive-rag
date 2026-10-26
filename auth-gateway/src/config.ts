try {
  process.loadEnvFile();
} catch {
  // no .env file; fall back to the defaults below
}

if (!process.env.JWT_SECRET) {
  throw new Error('JWT_SECRET must be set (see .env.example)');
}

export const config = {
  port: Number(process.env.PORT ?? 8080),
  jwtSecret: process.env.JWT_SECRET,
  jwtExpiresIn: Number(process.env.JWT_EXPIRES_IN ?? 86400),
  apiTokenExpiresIn: Number(process.env.API_TOKEN_EXPIRES_IN ?? 86400),
  dbPath: process.env.DB_PATH ?? 'users.db',
  pythonRagUrl: process.env.PYTHON_RAG_URL ?? 'http://127.0.0.1:8000/rag/query',
};
