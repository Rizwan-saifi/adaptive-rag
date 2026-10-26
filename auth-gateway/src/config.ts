try {
  process.loadEnvFile();
} catch {
  // no .env file; fall back to the defaults below
}

export const config = {
  port: Number(process.env.PORT ?? 8080),
  jwtSecret: process.env.JWT_SECRET ?? 'super_secret_jwt_key',
  jwtExpiresIn: Number(process.env.JWT_EXPIRES_IN ?? 3600),
  dbPath: process.env.DB_PATH ?? 'users.db',
  pythonRagUrl: process.env.PYTHON_RAG_URL ?? 'http://127.0.0.1:8000/rag/query',
};
