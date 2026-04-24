import React, { useState } from 'react'
import SearchForm from './features/search/SearchForm'

function App(): React.ReactElement {
  const [loading, setLoading] = useState(false)
  const [routes, setRoutes] = useState<any[]>([])
  const [carriers, setCarriers] = useState<string[]>([])

  const handleSearch = async (from: string, to: string) => {
    setLoading(true)
    try {
      const api = await import('./services/apiClient')
      const res: any = await api.post('/api/search', { from_id: from, to_id: to })
      // support older tests that return carriers as array of strings
      setCarriers(Array.isArray(res.carriers) ? res.carriers : [])
      setRoutes(Array.isArray(res.routes) ? res.routes : [])
    } catch (err) {
      setCarriers([])
      setRoutes([])
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

      <section aria-label="status feedback" />
    </main>
  )
}

export default App
