import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import FilterPanel, { defaultFilters, type FilterState } from '../components/search/FilterPanel'

describe('FilterPanel', () => {
  const mockOnChange = vi.fn()
  const mockOnReset = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders with default filters', () => {
    render(
      <FilterPanel filters={defaultFilters} onChange={mockOnChange} onReset={mockOnReset} />
    )
    expect(screen.getByText('Meta')).toBeInTheDocument()
    expect(screen.getByText('TikTok')).toBeInTheDocument()
    expect(screen.getByText('Google')).toBeInTheDocument()
  })

  it('toggles platform on click', () => {
    render(
      <FilterPanel filters={defaultFilters} onChange={mockOnChange} onReset={mockOnReset} />
    )
    fireEvent.click(screen.getByText('Meta'))
    expect(mockOnChange).toHaveBeenCalledWith('platform', 'meta')
  })

  it('shows active filter count', () => {
    const filters: FilterState = { ...defaultFilters, platform: 'meta', is_hot: true }
    render(
      <FilterPanel filters={filters} onChange={mockOnChange} onReset={mockOnReset} />
    )
    // Should show count in header text
    expect(screen.getByText(/Bộ lọc\s*\(2\)/)).toBeInTheDocument()
  })

  it('shows reset button only when filters are active', () => {
    const { rerender } = render(
      <FilterPanel filters={defaultFilters} onChange={mockOnChange} onReset={mockOnReset} />
    )
    expect(screen.queryByText(/Xóa bộ lọc/)).not.toBeInTheDocument()

    rerender(
      <FilterPanel
        filters={{ ...defaultFilters, platform: 'meta' }}
        onChange={mockOnChange}
        onReset={mockOnReset}
      />
    )
    expect(screen.getByText(/Xóa bộ lọc/)).toBeInTheDocument()
  })

  it('toggles advanced section', () => {
    render(
      <FilterPanel filters={defaultFilters} onChange={mockOnChange} onReset={mockOnReset} />
    )
    // Advanced section should be hidden — "Chỉ ads Hot" only appears in advanced
    expect(screen.queryByText(/Chỉ ads Hot/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByText(/Hiện thêm bộ lọc nâng cao/))
    expect(screen.getByText(/Chỉ ads Hot/)).toBeInTheDocument()
  })

  it('renders category dropdown from facets', () => {
    const facets = {
      platforms: {}, ad_types: {}, categories: {},
      categories_l1: { 'Mỹ phẩm': 50, 'Công nghệ': 30 },
    }
    render(
      <FilterPanel filters={defaultFilters} onChange={mockOnChange} onReset={mockOnReset} facets={facets} />
    )
    expect(screen.getByText('Mỹ phẩm (50)')).toBeInTheDocument()
    expect(screen.getByText('Công nghệ (30)')).toBeInTheDocument()
  })

  it('can collapse the panel', () => {
    render(
      <FilterPanel filters={defaultFilters} onChange={mockOnChange} onReset={mockOnReset} />
    )
    // Panel should be open by default, showing platform buttons
    expect(screen.getByText('Meta')).toBeInTheDocument()

    // Click header to collapse
    fireEvent.click(screen.getByText(/Bộ lọc/))

    // Content should be hidden
    expect(screen.queryByText('Meta')).not.toBeInTheDocument()
  })
})
