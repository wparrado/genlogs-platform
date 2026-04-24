import React, { useState } from 'react'
import SearchForm from './features/search/SearchForm'
import Map from './features/map/Map'

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
    await new Promise((resolve) => setTimeout(resolve, 10))
    try {
      const api = await import('./services/apiClient')
      const res: any = await api.post('/api/search', { from_id: from, to_id: to })
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
    <div className="site">
      <header className="site-header">
        <div className="container header-inner">
          <div className="brand">GenLogs</div>
          <nav className="nav">
            <a href="#" className="nav-link">Features</a>
            <a href="#" className="nav-link">Docs</a>
            <a href="#" className="nav-link cta">Get Started</a>
          </nav>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="container hero-inner">
            <div className="hero-content">
              <h1 className="hero-title">Logística clara y eficiente para tus rutas</h1>
              <p className="hero-sub">Compara rutas, transportistas y tiempos en segundos. Visualiza y optimiza tus envíos con la potencia de GenLogs.</p>
              <div className="hero-cta">
                <SearchForm onSearch={handleSearch} />
              </div>
            </div>
            <div className="hero-visual" aria-hidden="true">
              <div className="card">
                <h3>Resultados de ejemplo</h3>
                <ul>
                  {routes.length > 0 ? routes.slice(0,5).map((r) => <li key={r.id}>{r.summary || r.label || r.id}</li>) : <li>Introduce origen y destino para ver opciones</li>}
                </ul>
                {loading ? <div className="loading">Cargando...</div> : null}
              </div>
            </div>
          </div>
        </section>

        <section className="features container">
          <div className="feature">
            <h3>Comparación instantánea</h3>
            <p>Filtra y compara transportistas y rutas en una sola vista.</p>
          </div>
          <div className="feature">
            <h3>Optimización de costos</h3>
            <p>Encuentra las rutas más económicas y rápidas para tus envíos.</p>
          </div>
          <div className="feature">
            <h3>Integraciones</h3>
            <p>Conecta fácilmente con tus sistemas existentes vía API.</p>
          </div>
        </section>

        <section className="container carriers">
          <h4>Transportistas</h4>
          <div className="chips">
            {carriers.length > 0 ? carriers.map((c) => <span key={c} className="chip">{c}</span>) : <span className="muted">No hay transportistas disponibles</span>}
          </div>
        </section>

        <section className="container map">
          <h4>Mapa</h4>
          <Map routes={routes} />
        </section>

        <section className="container status">
          {error ? (
            <div className="error">
              <div>{error}</div>
              <button onClick={() => { if (lastQuery) void handleSearch(lastQuery.from, lastQuery.to) }} className="btn">Reintentar</button>
            </div>
          ) : null}
        </section>
      </main>

      <footer className="site-footer">
        <div className="container footer-inner">
          <div>© {new Date().getFullYear()} GenLogs</div>
          <div className="muted">Hecho con ♥</div>
        </div>
      </footer>
    </div>
  )
}

export default App
