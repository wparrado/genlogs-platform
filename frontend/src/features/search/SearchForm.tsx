import React, { useState, useRef, useEffect } from 'react'
import { get } from '../../services/apiClient'
import styles from './SearchForm.module.css'

type Suggestion = { id: string; label: string }

type Props = {
  onSearch?: (fromId: string, toId: string) => Promise<void>
  onError?: (message: string) => void
}

export default function SearchForm({ onSearch, onError }: Props): React.ReactElement {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [fromId, setFromId] = useState<string | null>(null)
  const [toId, setToId] = useState<string | null>(null)
  const [suggestionsFrom, setSuggestionsFrom] = useState<Suggestion[]>([])
  const [suggestionsTo, setSuggestionsTo] = useState<Suggestion[]>([])

  const [activeFromIndex, setActiveFromIndex] = useState<number | null>(null)
  const [activeToIndex, setActiveToIndex] = useState<number | null>(null)

  const debounceRef = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
    }
  }, [])

  const fetchSuggestions = async (query: string, target: 'from' | 'to') => {
    // only fetch suggestions for queries with 3 or more characters
    if (!query || query.trim().length < 3) {
      if (target === 'from') {
        setSuggestionsFrom([])
        setActiveFromIndex(null)
      } else {
        setSuggestionsTo([])
        setActiveToIndex(null)
      }
      return
    }
    try {
      const res: any = await get(`/api/cities?query=${encodeURIComponent(query)}`)
      const items: Suggestion[] = (res && res.items && res.items.map((i: any) => ({ id: i.id, label: i.label }))) || []
      if (target === 'from') {
        setSuggestionsFrom(items)
        setActiveFromIndex(items.length > 0 ? 0 : null)
      } else {
        setSuggestionsTo(items)
        setActiveToIndex(items.length > 0 ? 0 : null)
      }
    } catch (err) {
      if (target === 'from') {
        setSuggestionsFrom([])
        setActiveFromIndex(null)
      } else {
        setSuggestionsTo([])
        setActiveToIndex(null)
      }
    }
  }

  const handleFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setFrom(v)
    setFromId(null)
    // clear suggestions immediately for short queries
    if (v.trim().length < 3) {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
      setSuggestionsFrom([])
      setActiveFromIndex(null)
      return
    }

    if (debounceRef.current) window.clearTimeout(debounceRef.current)
    // debounce network requests
    // @ts-ignore window.setTimeout returns number in browsers
    debounceRef.current = window.setTimeout(() => fetchSuggestions(v, 'from'), 250)
  }

  const handleToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    setTo(v)
    setToId(null)
    // clear suggestions immediately for short queries
    if (v.trim().length < 3) {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
      setSuggestionsTo([])
      setActiveToIndex(null)
      return
    }

    if (debounceRef.current) window.clearTimeout(debounceRef.current)
    // @ts-ignore
    debounceRef.current = window.setTimeout(() => fetchSuggestions(v, 'to'), 250)
  }

  const pickSuggestion = (s: Suggestion, target: 'from' | 'to') => {
    if (target === 'from') {
      setFrom(s.label)
      setFromId(s.id)
      setSuggestionsFrom([])
      setActiveFromIndex(null)
    } else {
      setTo(s.label)
      setToId(s.id)
      setSuggestionsTo([])
      setActiveToIndex(null)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, target: 'from' | 'to') => {
    const suggestions = target === 'from' ? suggestionsFrom : suggestionsTo
    const activeIndex = target === 'from' ? activeFromIndex : activeToIndex
    if (!suggestions || suggestions.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      const next = activeIndex === null ? 0 : Math.min(suggestions.length - 1, activeIndex + 1)
      if (target === 'from') setActiveFromIndex(next)
      else setActiveToIndex(next)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      const prev = activeIndex === null ? suggestions.length - 1 : Math.max(0, activeIndex - 1)
      if (target === 'from') setActiveFromIndex(prev)
      else setActiveToIndex(prev)
    } else if (e.key === 'Enter') {
      if (activeIndex !== null) {
        e.preventDefault()
        const s = suggestions[activeIndex]
        pickSuggestion(s, target)
      }
    } else if (e.key === 'Escape') {
      if (target === 'from') {
        setSuggestionsFrom([])
        setActiveFromIndex(null)
      } else {
        setSuggestionsTo([])
        setActiveToIndex(null)
      }
    }
  }

  const handleSearch = async () => {
    const nextErrors: string[] = []

    if (!fromId) nextErrors.push('Select a valid origin from the suggestions')
    if (!toId) nextErrors.push('Select a valid destination from the suggestions')

    if (fromId && toId && fromId === toId) {
      nextErrors.push('From and To cannot be the same')
    }

    if (nextErrors.length > 0) {
      const msg = Array.from(new Set(nextErrors)).join('. ')
      if (onError) onError(msg)
      return
    }

    if (onSearch && fromId && toId) {
      await onSearch(fromId, toId)
    }
  }

  return (
    <form className={styles.form} onSubmit={(e) => { e.preventDefault(); void handleSearch() }}>
      <div className={styles.field}>
        <label htmlFor="from-input">From</label>
        <input
          id="from-input"
          className={styles.input}
          aria-label="From"
          name="from"
          value={from}
          onChange={handleFromChange}
          onKeyDown={(e) => handleKeyDown(e, 'from')}
          autoComplete="off"
          aria-autocomplete="list"
          aria-controls="from-suggestions"
          aria-activedescendant={activeFromIndex !== null ? `from-suggestion-${activeFromIndex}` : undefined}
        />
        {suggestionsFrom.length > 0 && (
          <ul id="from-suggestions" role="listbox" className={styles.suggestions}>
            {suggestionsFrom.map((s, idx) => (
              <li key={s.id} role="option" id={`from-suggestion-${idx}`} aria-selected={activeFromIndex === idx}>
                <button
                  type="button"
                  className={styles.suggestionButton}
                  onMouseDown={() => pickSuggestion(s, 'from')}
                  onMouseEnter={() => setActiveFromIndex(idx)}
                >
                  {s.label}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.field}>
        <label htmlFor="to-input">To</label>
        <input
          id="to-input"
          className={styles.input}
          aria-label="To"
          name="to"
          value={to}
          onChange={handleToChange}
          onKeyDown={(e) => handleKeyDown(e, 'to')}
          autoComplete="off"
          aria-autocomplete="list"
          aria-controls="to-suggestions"
          aria-activedescendant={activeToIndex !== null ? `to-suggestion-${activeToIndex}` : undefined}
        />
        {suggestionsTo.length > 0 && (
          <ul id="to-suggestions" role="listbox" className={styles.suggestions}>
            {suggestionsTo.map((s, idx) => (
              <li key={s.id} role="option" id={`to-suggestion-${idx}`} aria-selected={activeToIndex === idx}>
                <button
                  type="button"
                  className={styles.suggestionButton}
                  onMouseDown={() => pickSuggestion(s, 'to')}
                  onMouseEnter={() => setActiveToIndex(idx)}
                >
                  {s.label}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.actions}>
        <button className={styles.button} type="submit">Search</button>
      </div>

    </form>
  )
}
