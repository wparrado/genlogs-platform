import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import { SearchForm } from 'src/features/search'

jest.mock('src/services/apiClient', () => ({ get: jest.fn(() => Promise.resolve({ items: [] })) }))

test('calls onSearch with values on submit', async () => {
  const onSearch = jest.fn(() => Promise.resolve())
  render(<SearchForm onSearch={onSearch} />)

  const from = screen.getByLabelText('From') as HTMLInputElement
  const to = screen.getByLabelText('To') as HTMLInputElement

  fireEvent.change(from, { target: { value: 'Origen' } })
  fireEvent.change(to, { target: { value: 'Destino' } })

  const button = screen.getByRole('button', { name: /search/i })
  fireEvent.click(button)

  await waitFor(() => expect(onSearch).toHaveBeenCalledWith('Origen', 'Destino'))
})
