import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';

const SECRET_KEY = process.env.SECRET_KEY ?? 'change-me';
const EXPIRE_MINUTES = 24 * 60;

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hashed: string): Promise<boolean> {
  return bcrypt.compare(password, hashed);
}

export function createAccessToken(userId: string): string {
  const exp = Math.floor(Date.now() / 1000) + EXPIRE_MINUTES * 60;
  return jwt.sign({ sub: userId, exp }, SECRET_KEY, { algorithm: 'HS256' });
}

export function decodeToken(token: string): { sub: string } {
  return jwt.verify(token, SECRET_KEY) as { sub: string };
}

export function extractBearerToken(authHeader: string | null): string | null {
  if (!authHeader?.startsWith('Bearer ')) return null;
  return authHeader.slice(7);
}
