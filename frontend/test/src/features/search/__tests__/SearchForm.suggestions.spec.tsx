import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchForm from '../../../../../src/features/search/SearchForm'
import * as api from '../../../../../src/services/apiClient'

describe('SearchForm suggestions (TDD - failing)', () => {
  beforeEach(() => {
    jest.spyOn(api, 'get').mockResolvedValue([] as unknown as any)
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  test('handles empty suggestion list without crashing', async () => {
    render(<SearchForm />)
    const from = screen.getByRole('textbox', { name: /from/i })
    await userEvent.type(from, 'X')
    // assumes component queries suggestions on input
    expect(await screen.findByText(/no suggestions/i)).toBeInTheDocument()
  })
})
