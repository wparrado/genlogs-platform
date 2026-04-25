// Runtime-safe base URL resolver for dev, prod, and test environments
// In development use a relative path so Vite's dev server proxy (vite.config.ts) can forward /api to the backend
const isDev = typeof process !== 'undefined' && (process as any).env && (((process as any).env.NODE_ENV === 'development') || (process as any).env.VITE_DEV === 'true')
const BASE_URL: string = (globalThis as any).__VITE_API_BASE_URL__
  ?? (typeof process !== 'undefined' ? (process.env.VITE_API_BASE_URL as string | undefined) : undefined)
  ?? (isDev ? '' : 'http://localhost:8000')

async function parseBody(response: Response) {
  const ct = response.headers.get('content-type') || ''
  try {
    if (ct.includes('application/json')) return await response.json()
    return await response.text()
  } catch {
    return null
  }
}

export async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`)
  if (!response.ok) {
    const body = await parseBody(response)
    const err = new Error(response.statusText || `GET ${path} failed with status ${response.status}`)
    ;(err as any).status = response.status
    ;(err as any).body = body
    throw err
  }
  return response.json() as Promise<T>
}

export async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const b = await parseBody(response)
    const err = new Error(response.statusText || `POST ${path} failed with status ${response.status}`)
    ;(err as any).status = response.status
    ;(err as any).body = b
    throw err
  }
  return response.json() as Promise<T>
}

