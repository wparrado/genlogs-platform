import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../../../../../src/App'
import * as api from '../../../../../src/services/apiClient'

describe('Search loading and results (TDD - failing)', () => {
  beforeEach(() => {
    jest.spyOn(api, 'get').mockImplementation((path: string) => {
      if (path.startsWith('/api/cities')) {
        return Promise.resolve({ items: [{ id: 'nyc', label: 'New York' }, { id: 'was', label: 'Washington' }] } as any)
      }
      if (path.startsWith('/api/search')) {
        return Promise.resolve({
          carriers: ['Carrier A', 'Carrier B'],
          routes: [
            { id: 'r1', duration_minutes: 60, summary: 'Route 1' },
            { id: 'r2', duration_minutes: 90, summary: 'Route 2' },
          ],
        } as any)
      }
      return Promise.resolve({} as any)
    })
  })

  afterEach(() => jest.restoreAllMocks())


  afterEach(() => jest.restoreAllMocks())

  test('submitting without selecting suggestions shows validation toast', async () => {
    render(<App />)
    // interact with the App-level search form if present
    const from = screen.getByRole('textbox', { name: /from/i })
    const to = screen.getByRole('textbox', { name: /to/i })
    await userEvent.type(from, 'New York')
    await userEvent.type(to, 'Washington')
    await userEvent.click(screen.getByRole('button', { name: /search/i }))

    // App shows a Toast with the validation message
    expect(await screen.findByText(/Select a valid origin/i)).toBeInTheDocument()
  })
})
