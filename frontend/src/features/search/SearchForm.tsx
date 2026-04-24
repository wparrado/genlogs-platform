import React, { useState } from 'react'
import { get } from '../../services/apiClient'
import styles from './SearchForm.module.css'

type Props = {
  onSearch?: (from: string, to: string) => Promise<void>
}

export default function SearchForm({ onSearch }: Props): React.ReactElement {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [suggestions, setSuggestions] = useState<string[] | null>(null)
  const [errors, setErrors] = useState<string[]>([])

  const handleFromChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setFrom(v)
    try {
      const res: any = await get(`/api/cities?query=${encodeURIComponent(v)}`)
      setSuggestions((res && res.items && res.items.map((i: any) => i.label)) || [])
    } catch (err) {
      setSuggestions([])
    }
  }

  const handleToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setTo(v)
  }

  const handleSearch = async () => {
    // validation
    const nextErrors: string[] = []

    if (from === '') nextErrors.push('From is required')
    else if (from.trim() === '') nextErrors.push('Please enter a valid city')

    if (to === '') nextErrors.push('To is required')
    else if (to.trim() === '') nextErrors.push('Please enter a valid city')

    if (from.trim() !== '' && to.trim() !== '' && from.trim() === to.trim()) {
      nextErrors.push('From and To cannot be the same')
    }

    if (nextErrors.length > 0) {
      // dedupe errors so tests that search by text don't hit multiple identical nodes
      setErrors(Array.from(new Set(nextErrors)))
      return
    }

    setErrors([])

    if (onSearch) {
      await onSearch(from.trim(), to.trim())
    }
  }

  return (
    <form className={styles.form} onSubmit={(e) => { e.preventDefault(); void handleSearch() }}>
      <label>
        From
        <input className={styles.input} aria-label="From" name="from" value={from} onChange={handleFromChange} />
      </label>

      <label>
        To
        <input className={styles.input} aria-label="To" name="to" value={to} onChange={handleToChange} />
      </label>

      <button className={styles.button} type="submit">Search</button>

      <div aria-live="polite">
        {errors.length > 0 ? (
          <div>
            {errors.map((err) => (
              <div key={err}>{err}</div>
            ))}
          </div>
        ) : suggestions === null ? null : suggestions.length === 0 ? (
          <div>No suggestions</div>
        ) : (
          <ul>
            {suggestions.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        )}
      </div>
    </form>
  )
}
