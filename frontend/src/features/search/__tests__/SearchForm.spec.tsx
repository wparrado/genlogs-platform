import React from 'react'
import { render, screen } from '@testing-library/react'
import App from '../../../App'

describe('SearchForm (scaffold)', () => {
  test('renders main shell and search sections', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: /GenLogs/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/search form/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/route results/i)).toBeInTheDocument()
  })
})
