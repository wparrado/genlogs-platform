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
    if (onSearch) {
      await onSearch(from, to)
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
        {suggestions === null ? null : suggestions.length === 0 ? (
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
