import React, { useState, useEffect, Suspense } from 'react'
import SearchForm from './features/search/SearchForm'
import * as api from './services/apiClient'
import Toast from './components/Toast'

// Avoid importing react-leaflet during Jest runs (it ships as ESM and breaks the transformer).
// When under tests, provide a noop stub so App can render during unit tests without loading Leaflet.
let Map: any = () => null
if (!(typeof process !== 'undefined' && (process as any).env && (process as any).env.JEST_WORKER_ID)) {
  // runtime (dev/prod) — lazy-load the map component as an ESM dynamic import to work in browser
  Map = React.lazy(() => import('./components/Map'))
}

function App(): React.ReactElement {
  useEffect(() => {
    // visible debug to help detect why UI might appear blank in browser
    // logs show in DevTools Console and we also render a small overlay when in dev mode
    // eslint-disable-next-line no-console
    console.log('App mounted — DEV:', process.env.NODE_ENV === 'development')
  }, [])

  const [routes, setRoutes] = useState<any[]>([])
  const [carriers, setCarriers] = useState<any[]>([])
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToastMessage(msg)
  }

  const handleSearch = async (from: string, to: string) => {
    await new Promise((resolve) => setTimeout(resolve, 10))
    try {
      const res: any = await api.get(`/api/search?from_id=${encodeURIComponent(from)}&to_id=${encodeURIComponent(to)}`)
      // Normalize carriers to objects with name and trucksPerDay (API may return strings or objects)
      const carriersList = Array.isArray(res.carriers) ? res.carriers.map((c: any) => {
        if (c == null) return { name: String(c), trucksPerDay: undefined }
        if (typeof c === 'string') return { name: c, trucksPerDay: undefined }
        if (typeof c === 'object') {
          const name = c.name || c.label || c.id || JSON.stringify(c)
          const trucksPerDay = c.trucksPerDay ?? c.daily_trucks ?? c.trucks_per_day ?? undefined
          return { name, trucksPerDay }
        }
        return { name: String(c), trucksPerDay: undefined }
      }) : []
      setCarriers(carriersList)

      const normalizedRoutes = Array.isArray(res.routes) ? res.routes.map((r: any, idx: number) => {
        // ensure id is a string
        let id = r && r.id
        if (typeof id === 'object') {
          id = id.id ?? id.uuid ?? JSON.stringify(id)
        }
        id = String(id ?? `route-${idx}`)
        // ensure summary is a string
        let summary = r && (r.summary || r.label || r.name)
        if (typeof summary === 'object') {
          summary = summary.label || summary.name || JSON.stringify(summary)
        }
        summary = String(summary ?? '')

        // extract duration (seconds or minutes) and format as human readable
        let durationRaw = r && (r.duration || r.duration_seconds || r.durationSec || r.durationMinutes || r.duration_min || r.estimatedDuration || r.travel_time || r.eta || r.time)
        let durationSeconds: number | null = null
        if (typeof durationRaw === 'number') {
          // assume seconds if > 1800 else minutes? prefer seconds when large
          durationSeconds = durationRaw > 1000 ? durationRaw : durationRaw * 60
        } else if (typeof durationRaw === 'string') {
          const n = parseFloat(durationRaw)
          if (!Number.isNaN(n)) {
            durationSeconds = n > 1000 ? n : n * 60
          }
        }
        function fmt(sec: number | null) {
          if (!sec && sec !== 0) return ''
          const mins = Math.round(sec / 60)
          if (mins < 60) return `${mins} min`
          const hrs = Math.floor(mins / 60)
          const rem = mins % 60
          return rem === 0 ? `${hrs} h` : `${hrs} h ${rem} min`
        }

        const duration = fmt(durationSeconds)

        return { ...r, id, summary, duration }
      }) : []
      setRoutes(normalizedRoutes)
    } catch (err: any) {
      setCarriers([])
      setRoutes([])
      let msg = 'An error occurred while searching'
      if (err && typeof err.status === 'number' && err.status >= 500 && err.status < 600) {
        // generic message for server errors (avoid leaking sensitive info)
        msg = 'Error del servidor. Por favor inténtalo más tarde.'
      } else if (err && err.message) {
        msg = err.message
      }
      showToast(msg)
    } finally {
      // no-op
    }
  }

  return (
    <div className="site">
      <header className="site-header">
        <div className="container header-inner">
          <h1 className="brand">GenLogs</h1>
        </div>
      </header>

      <main>
        <div className="container main-inner">
          <section aria-label="search form">
            <SearchForm onSearch={handleSearch} onError={(msg) => setToastMessage(msg)} />
          </section>

          <section aria-label="route results" className="routes">
            <h4>Rutas</h4>
            <ul>
              {routes.length > 0 ? routes.map((r) => (
                <li key={r.id} className="route-item">
                  <span className="route-name">{r.summary || r.label || r.id}</span>
                  {r.duration ? <small className="route-duration muted">{r.duration}</small> : null}
                </li>
              )) : <li className="muted">Introduce origen y destino para ver opciones</li>}
            </ul>
          </section>

          <section aria-label="carrier results" className="carriers">
            <h4>Transportistas</h4>
            <div className="chips">
              {carriers.length > 0 ? carriers.map((c, i) => (
                <span key={`${c.name}-${i}`} className="chip">{c.name}{typeof c.trucksPerDay === 'number' ? ` — ${c.trucksPerDay} camiones/día` : ''}</span>
              )) : <span className="muted">No hay transportistas disponibles</span>}
            </div>
          </section>

          <section className="map">
            <Suspense fallback={null}>
              <Map routes={routes} />
            </Suspense>
          </section>

          {/* toast shown globally (no inline plain-text errors) */}
          <Toast message={toastMessage || ''} onClose={() => setToastMessage(null)} />
        </div>
      </main>

      <footer className="site-footer">
        <div className="container footer-inner">
          <div>© {new Date().getFullYear()} GenLogs</div>
        </div>
      </footer>
    </div>
  )
}

export default App
