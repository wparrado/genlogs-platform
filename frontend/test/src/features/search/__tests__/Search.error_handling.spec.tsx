import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../../../../../src/App'
import * as api from '../../../../../src/services/apiClient'

describe('Search error handling (aligned with UI)', () => {
  beforeEach(() => {
    jest.spyOn(api, 'get').mockImplementation((path: string) => {
      if (path.startsWith('/api/cities')) {
        return Promise.resolve({ items: [{ id: 'nyc', label: 'New York' }, { id: 'was', label: 'Washington' }] } as any)
      }
      if (path.startsWith('/api/search')) {
        const err: any = new Error('server')
        err.status = 500
        return Promise.reject(err)
      }
      return Promise.resolve({} as any)
    })
  })

  afterEach(() => jest.restoreAllMocks())

  test('renders user-friendly error when backend fails', async () => {
    render(<App />)
    const from = screen.getByRole('textbox', { name: /from/i })
    const to = screen.getByRole('textbox', { name: /to/i })
    await userEvent.type(from, 'New York')
    const sFrom = await screen.findByRole('button', { name: /New York/i })
    await userEvent.click(sFrom)
    await userEvent.type(to, 'Washington')
    const sTo = await screen.findByRole('button', { name: /Washington/i })
    await userEvent.click(sTo)

    await userEvent.click(screen.getByRole('button', { name: /search/i }))

    expect(await screen.findByText(/error del servidor/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Cerrar/i })).toBeInTheDocument()
  })
})
