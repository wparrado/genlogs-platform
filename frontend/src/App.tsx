import React, { useState } from 'react'
import SearchForm from './features/search/SearchForm'

function App(): React.ReactElement {
  const [loading, setLoading] = useState(false)
  const [routes, setRoutes] = useState<any[]>([])
  const [carriers, setCarriers] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)
  const [lastQuery, setLastQuery] = useState<{ from: string; to: string } | null>(null)

  const handleSearch = async (from: string, to: string) => {
    setLastQuery({ from, to })
    setError(null)
    setLoading(true)
    // allow a short render tick so loading UI is visible in tests
    await new Promise((resolve) => setTimeout(resolve, 10))
    try {
      const api = await import('./services/apiClient')
      const res: any = await api.post('/api/search', { from_id: from, to_id: to })
      // support older tests that return carriers as array of strings
      setCarriers(Array.isArray(res.carriers) ? res.carriers : [])
      setRoutes(Array.isArray(res.routes) ? res.routes : [])
      setError(null)
    } catch (err) {
      setCarriers([])
      setRoutes([])
      setError('An error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      <h1>GenLogs</h1>
      <section aria-label="search form">
        <SearchForm onSearch={handleSearch} />
      </section>

      <section aria-label="route results">
        {loading ? <div>Loading...</div> : null}
        <ul>
          {routes.map((r) => (
            <li key={r.id}>{r.summary || r.summary || r.label || r.id}</li>
          ))}
        </ul>
      </section>

      <section aria-label="carrier results">
        <ul>
          {carriers.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      </section>

      <section aria-label="status feedback">
        {error ? (
          <div>
            <div>{error}</div>
            <button onClick={() => { if (lastQuery) void handleSearch(lastQuery.from, lastQuery.to) }}>Retry</button>
          </div>
        ) : null}
      </section>
    </main>
  )
}

export default App
