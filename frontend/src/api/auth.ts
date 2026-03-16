import client from './client'
import type { User, TokenResponse } from '../types/user'

export async function login(email: string, password: string): Promise<TokenResponse> {
  const res = await client.post('/auth/login', { email, password })
  return res.data
}

export async function register(email: string, password: string, full_name: string): Promise<User> {
  const res = await client.post('/auth/register', { email, password, full_name })
  return res.data
}
