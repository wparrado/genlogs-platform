import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../src/App'
import * as api from '../src/services/apiClient'

describe('Search error handling (TDD - failing)', () => {
  beforeEach(() => {
    jest.spyOn(api, 'post').mockRejectedValue(new Error('POST /search failed with status 500'))
  })

  afterEach(() => jest.restoreAllMocks())

  test('renders user-friendly error when backend fails', async () => {
    render(<App />)
    const from = screen.getByRole('textbox', { name: /from/i })
    const to = screen.getByRole('textbox', { name: /to/i })
    await userEvent.type(from, 'A')
    await userEvent.type(to, 'B')
    await userEvent.click(screen.getByRole('button', { name: /search/i }))

    expect(await screen.findByText(/an error occurred/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })
})
