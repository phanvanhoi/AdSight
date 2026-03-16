import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Boards from '../pages/Boards'
import type { Board } from '../types/board'

// Mock boards API
vi.mock('../api/boards', () => ({
  listBoards: vi.fn(),
  createBoard: vi.fn(),
  deleteBoard: vi.fn(),
  getBoardAds: vi.fn(),
  addAdToBoard: vi.fn(),
  removeAdFromBoard: vi.fn(),
}))

import { listBoards, createBoard, deleteBoard, getBoardAds } from '../api/boards'

const mockBoards: Board[] = [
  { id: 'board-1', name: 'Competitors', description: null, created_at: '2026-03-10T00:00:00Z' },
  { id: 'board-2', name: 'Inspiration', description: null, created_at: '2026-03-12T00:00:00Z' },
]

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('Boards Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getBoardAds).mockResolvedValue({ results: [], total: 0, page: 1, limit: 20 })
  })

  it('renders boards list', async () => {
    vi.mocked(listBoards).mockResolvedValue(mockBoards)
    renderWithProviders(<Boards />)

    await waitFor(() => {
      expect(screen.getByText('Competitors')).toBeInTheDocument()
      expect(screen.getByText('Inspiration')).toBeInTheDocument()
    })
  })

  it('shows empty state when no boards', async () => {
    vi.mocked(listBoards).mockResolvedValue([])
    renderWithProviders(<Boards />)

    await waitFor(() => {
      expect(screen.getByText('Chua co board nao')).toBeInTheDocument()
    })
  })

  it('creates a new board', async () => {
    const user = userEvent.setup()
    vi.mocked(listBoards).mockResolvedValue([])
    vi.mocked(createBoard).mockResolvedValue({
      id: 'board-new',
      name: 'My Board',
      description: null,
      created_at: '2026-03-16T00:00:00Z',
    })

    renderWithProviders(<Boards />)

    // Click "Tao board" to show create form
    await user.click(screen.getByRole('button', { name: /Tao board/i }))

    // Fill in board name and submit
    const input = screen.getByPlaceholderText('Ten board...')
    await user.type(input, 'My Board')
    await user.click(screen.getByRole('button', { name: 'Tao' }))

    await waitFor(() => {
      expect(createBoard).toHaveBeenCalledWith('My Board')
    })
  })

  it('deletes a board', async () => {
    const user = userEvent.setup()
    vi.mocked(listBoards).mockResolvedValue(mockBoards)
    vi.mocked(deleteBoard).mockResolvedValue(undefined)

    renderWithProviders(<Boards />)

    await waitFor(() => {
      expect(screen.getByText('Competitors')).toBeInTheDocument()
    })

    // Find and click the first delete button (Trash2 icon buttons)
    const deleteButtons = screen.getAllByRole('button').filter((btn) => {
      // Delete buttons are the ones inside board items with the Trash2 icon
      return btn.querySelector('svg') && btn.className.includes('hover:text-red-500')
    })
    expect(deleteButtons.length).toBeGreaterThan(0)
    await user.click(deleteButtons[0])

    await waitFor(() => {
      expect(deleteBoard).toHaveBeenCalledWith('board-1')
    })
  })

  it('shows placeholder when no board selected', async () => {
    vi.mocked(listBoards).mockResolvedValue(mockBoards)
    renderWithProviders(<Boards />)

    await waitFor(() => {
      expect(screen.getByText('Chon 1 board de xem ads da luu')).toBeInTheDocument()
    })
  })

  it('shows board ads when a board is selected', async () => {
    const user = userEvent.setup()
    vi.mocked(listBoards).mockResolvedValue(mockBoards)
    vi.mocked(getBoardAds).mockResolvedValue({
      results: [
        {
          id: 'ad-1',
          platform: 'meta',
          advertiser_name: 'Test Ad',
          ad_type: 'video',
          headline: 'Test Headline',
          body_text: 'Test body',
          thumbnail_url: null,
          cta_type: null,
          likes: 100,
          comments: 10,
          shares: 5,
          first_seen: null,
          last_seen: null,
          is_active: true,
        },
      ],
      total: 1,
      page: 1,
      limit: 20,
    })

    renderWithProviders(<Boards />)

    await waitFor(() => {
      expect(screen.getByText('Competitors')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Competitors'))

    await waitFor(() => {
      expect(getBoardAds).toHaveBeenCalledWith('board-1')
      expect(screen.getByText('Test Headline')).toBeInTheDocument()
    })
  })
})
