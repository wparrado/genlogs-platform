import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../src/App'
import * as api from '../src/services/apiClient'

describe('Search loading and results (TDD - failing)', () => {
  beforeEach(() => {
    jest.spyOn(api, 'post').mockResolvedValue({
      carriers: ['Carrier A', 'Carrier B'],
      routes: [
        { id: 'r1', duration_minutes: 60, summary: 'Route 1' },
        { id: 'r2', duration_minutes: 90, summary: 'Route 2' },
      ],
    } as any)
  })

  afterEach(() => jest.restoreAllMocks())

  test('shows loading state then renders route cards and carriers', async () => {
    render(<App />)
    // interact with the App-level search form if present
    const from = screen.getByRole('textbox', { name: /from/i })
    const to = screen.getByRole('textbox', { name: /to/i })
    await userEvent.type(from, 'New York')
    await userEvent.type(to, 'Washington')
    await userEvent.click(screen.getByRole('button', { name: /search/i }))

    expect(await screen.findByText(/loading/i)).toBeInTheDocument()
    expect(await screen.findByText(/route 1/i)).toBeInTheDocument()
    expect(await screen.findByText(/carrier a/i)).toBeInTheDocument()
  })
})
