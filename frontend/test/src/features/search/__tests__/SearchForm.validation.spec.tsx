import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchForm from 'src/features/search/SearchForm'

describe('SearchForm validation (TDD - failing)', () => {
  test('shows validation errors when fields are missing', async () => {
    render(<SearchForm />)
    await userEvent.click(screen.getByRole('button', { name: /search/i }))
    expect(await screen.findByText(/from is required/i)).toBeInTheDocument()
    expect(await screen.findByText(/to is required/i)).toBeInTheDocument()
  })

  test('shows error when same city is selected for from and to', async () => {
    render(<SearchForm />)
    await userEvent.type(screen.getByRole('textbox', { name: /from/i }), 'New York')
    await userEvent.type(screen.getByRole('textbox', { name: /to/i }), 'New York')
    await userEvent.click(screen.getByRole('button', { name: /search/i }))
    expect(await screen.findByText(/from and to cannot be the same/i)).toBeInTheDocument()
  })

  test('rejects whitespace-only input', async () => {
    render(<SearchForm />)
    await userEvent.type(screen.getByRole('textbox', { name: /from/i }), '   ')
    await userEvent.type(screen.getByRole('textbox', { name: /to/i }), '   ')
    await userEvent.click(screen.getByRole('button', { name: /search/i }))
    expect(await screen.findByText(/please enter a valid city/i)).toBeInTheDocument()
  })
})
