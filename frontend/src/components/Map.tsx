import React, { useEffect, useMemo } from 'react'
import { MapContainer, TileLayer, Polyline, CircleMarker, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

type Props = {
  routes?: Array<any>
}

const FitBounds: React.FC<{ positions: [number, number][] }> = ({ positions }) => {
  const map = useMap()
  useEffect(() => {
    if (!positions || positions.length === 0) return
    ;(map as any).fitBounds(positions as any, { padding: [20, 20] })
  }, [map, positions])
  return null
}

const DEFAULT_COLORS = ['#3b82f6', '#06b6d4', '#f97316', '#ef4444', '#a78bfa', '#10b981']

export default function Map({ routes }: Props): React.ReactElement {
  // Build array of route positions arrays
  const allRoutesPositions = useMemo(() => {
    if (!routes || !Array.isArray(routes) || routes.length === 0) return [] as [number, number][][]

    return routes.map((r: any) => {
      // try multiple shapes for path coordinates
      // 1) pathPayload: [[lat,lng],[lat,lng]]
      if (r && r.pathPayload && Array.isArray(r.pathPayload)) {
        return r.pathPayload.map((p: any) => [p[0], p[1]] as [number, number])
      }

      // 2) path: could be [[lat,lng]] or [[lng,lat]]
      if (r && r.path && Array.isArray(r.path)) {
        const first = r.path[0]
        if (Array.isArray(first) && first.length >= 2 && typeof first[0] === 'number' && typeof first[1] === 'number') {
          // detect order by value range (lat between -90 and 90)
          const isLatFirst = Math.abs(first[0]) <= 90
          return r.path.map((p: any) => isLatFirst ? [p[0], p[1]] as [number, number] : [p[1], p[0]] as [number, number])
        }
      }

      // 3) geometry: GeoJSON LineString coordinates (likely [lng,lat])
      if (r && r.geometry && r.geometry.type === 'LineString' && Array.isArray(r.geometry.coordinates)) {
        const first = r.geometry.coordinates[0]
        if (Array.isArray(first) && first.length >= 2) {
          const isLngFirst = Math.abs(first[0]) <= 180 && Math.abs(first[0]) > 90
          // assume [lng,lat] -> convert to [lat,lng]
          return r.geometry.coordinates.map((c: any) => isLngFirst ? [c[1], c[0]] as [number, number] : [c[0], c[1]] as [number, number])
        }
      }

      // 4) coordinates field
      if (r && r.coordinates && Array.isArray(r.coordinates)) {
        const first = r.coordinates[0]
        if (Array.isArray(first) && first.length >= 2) {
          const isLatFirst = Math.abs(first[0]) <= 90
          return r.coordinates.map((p: any) => isLatFirst ? [p[0], p[1]] as [number, number] : [p[1], p[0]] as [number, number])
        }
      }

      return [] as [number, number][]
    })
  }, [routes])

  // compute a combined positions array for bounds
  const combinedPositions = useMemo(() => allRoutesPositions.flat(), [allRoutesPositions])

  const center: [number, number] = combinedPositions && combinedPositions.length ? combinedPositions[Math.floor(combinedPositions.length / 2)] as [number, number] : [20, 0]

  return (
    <div style={{ height: 300 }}>
      <MapContainer center={center} zoom={6} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {combinedPositions && combinedPositions.length ? <FitBounds positions={combinedPositions as any} /> : null}

        {allRoutesPositions.map((positions, idx) => (
          positions && positions.length ? (
            <React.Fragment key={`route-${idx}`}>
              <Polyline positions={positions as any} color={DEFAULT_COLORS[idx % DEFAULT_COLORS.length]} />
              <CircleMarker center={positions[0] as any} radius={6} pathOptions={{ color: 'green' }} />
              <CircleMarker center={positions[positions.length - 1] as any} radius={6} pathOptions={{ color: 'red' }} />
            </React.Fragment>
          ) : null
        ))}

      </MapContainer>
    </div>
  )
}
