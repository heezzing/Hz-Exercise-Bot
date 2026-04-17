import { createClient, Client } from '@libsql/client';

let _client: Client | null = null;

function getClient(): Client {
  if (!_client) {
    _client = createClient({
      url: process.env.TURSO_DATABASE_URL!,
      authToken: process.env.TURSO_AUTH_TOKEN,
    });
  }
  return _client;
}

// pg Pool과 동일한 인터페이스처럼 사용할 수 있도록 Proxy 반환
const db = new Proxy({} as Client, {
  get(_target, prop) {
    return (...args: unknown[]) => {
      const client = getClient();
      return (client[prop as keyof Client] as (...a: unknown[]) => unknown)(...args);
    };
  },
});

export default db;
