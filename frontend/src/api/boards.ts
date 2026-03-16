import client from './client'
import type { Board } from '../types/board'

export async function listBoards(): Promise<Board[]> {
  const res = await client.get('/boards')
  return res.data
}

export async function createBoard(name: string, description?: string): Promise<Board> {
  const res = await client.post('/boards', { name, description })
  return res.data
}

export async function deleteBoard(id: string): Promise<void> {
  await client.delete(`/boards/${id}`)
}

export async function addAdToBoard(boardId: string, adId: string): Promise<void> {
  await client.post(`/boards/${boardId}/ads/${adId}`)
}

export async function removeAdFromBoard(boardId: string, adId: string): Promise<void> {
  await client.delete(`/boards/${boardId}/ads/${adId}`)
}

export async function getBoardAds(boardId: string, page = 1, limit = 20) {
  const res = await client.get(`/boards/${boardId}/ads`, { params: { page, limit } })
  return res.data
}
