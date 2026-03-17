import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Login from '../pages/Login'
import Register from '../pages/Register'

// Mock react-router-dom navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

// Mock auth API
vi.mock('../api/auth', () => ({
  login: vi.fn(),
  register: vi.fn(),
}))

// Mock auth store
vi.mock('../stores/authStore', () => ({
  useAuthStore: vi.fn((selector) =>
    selector({
      user: null,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
      loadFromStorage: vi.fn(),
    }),
  ),
}))

import { login, register } from '../api/auth'

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

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders email input, password input, and submit button', () => {
    renderWithProviders(<Login />)

    expect(screen.getByPlaceholderText('email@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Dang nhap' })).toBeInTheDocument()
  })

  it('shows error on empty submit (HTML validation prevents, but API error shows)', async () => {
    const user = userEvent.setup()
    vi.mocked(login).mockRejectedValueOnce({
      response: { data: { detail: 'Email is required' } },
    })

    renderWithProviders(<Login />)

    const emailInput = screen.getByPlaceholderText('email@example.com')
    const passwordInput = screen.getByPlaceholderText('••••••••')
    await user.type(emailInput, 'bad@test.com')
    await user.type(passwordInput, 'wrong')
    await user.click(screen.getByRole('button', { name: 'Dang nhap' }))

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument()
    })
  })

  it('calls login API with correct payload and navigates on success', async () => {
    const user = userEvent.setup()
    // Create a fake JWT with base64-encoded payload
    const payload = btoa(JSON.stringify({ sub: 'user-123', email: 'test@test.com' }))
    const fakeToken = `header.${payload}.signature`

    vi.mocked(login).mockResolvedValueOnce({
      access_token: fakeToken,
      refresh_token: 'refresh-token',
      token_type: 'bearer',
    })

    renderWithProviders(<Login />)

    await user.type(screen.getByPlaceholderText('email@example.com'), 'test@test.com')
    await user.type(screen.getByPlaceholderText('••••••••'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Dang nhap' }))

    await waitFor(() => {
      expect(login).toHaveBeenCalledWith('test@test.com', 'password123')
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('shows fallback error message on network failure', async () => {
    const user = userEvent.setup()
    vi.mocked(login).mockRejectedValueOnce(new Error('Network Error'))

    renderWithProviders(<Login />)

    await user.type(screen.getByPlaceholderText('email@example.com'), 'test@test.com')
    await user.type(screen.getByPlaceholderText('••••••••'), 'pass')
    await user.click(screen.getByRole('button', { name: 'Dang nhap' }))

    await waitFor(() => {
      expect(screen.getByText('Dang nhap that bai')).toBeInTheDocument()
    })
  })

  it('has link to register page', () => {
    renderWithProviders(<Login />)
    const link = screen.getByText('Dang ky mien phi')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/register')
  })
})

describe('Register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all fields: full name, email, password', () => {
    renderWithProviders(<Register />)

    expect(screen.getByPlaceholderText('Nguyen Van A')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('email@example.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Toi thieu 8 ky tu')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Dang ky' })).toBeInTheDocument()
  })

  it('calls register API with correct payload and navigates to login', async () => {
    const user = userEvent.setup()
    vi.mocked(register).mockResolvedValueOnce({
      id: 'new-user',
      email: 'new@test.com',
      full_name: 'Nguyen Van A',
      tier: 'free',
    })

    renderWithProviders(<Register />)

    await user.type(screen.getByPlaceholderText('Nguyen Van A'), 'Nguyen Van A')
    await user.type(screen.getByPlaceholderText('email@example.com'), 'new@test.com')
    await user.type(screen.getByPlaceholderText('Toi thieu 8 ky tu'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Dang ky' }))

    await waitFor(() => {
      expect(register).toHaveBeenCalledWith('new@test.com', 'password123', 'Nguyen Van A')
      expect(mockNavigate).toHaveBeenCalledWith('/login')
    })
  })

  it('shows error on registration failure', async () => {
    const user = userEvent.setup()
    vi.mocked(register).mockRejectedValueOnce({
      response: { data: { detail: 'Email already exists' } },
    })

    renderWithProviders(<Register />)

    await user.type(screen.getByPlaceholderText('Nguyen Van A'), 'Test')
    await user.type(screen.getByPlaceholderText('email@example.com'), 'dup@test.com')
    await user.type(screen.getByPlaceholderText('Toi thieu 8 ky tu'), 'password123')
    await user.click(screen.getByRole('button', { name: 'Dang ky' }))

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument()
    })
  })

  it('has link to login page', () => {
    renderWithProviders(<Register />)
    const link = screen.getByText('Dang nhap')
    expect(link).toBeInTheDocument()
    expect(link.closest('a')).toHaveAttribute('href', '/login')
  })
})
