import React, { useEffect } from 'react'
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

export default function Map({ routes }: Props): React.ReactElement {
  const positions = routes && routes.length && routes[0].pathPayload ? routes[0].pathPayload.map((p: any) => [p[0], p[1]]) : null
  const center: [number, number] = positions && positions.length ? positions[Math.floor(positions.length / 2)] as [number, number] : [20, 0]

  return (
    <div style={{ height: 300 }}>
      <MapContainer center={center} zoom={6} style={{ height: '100%', width: '100%' }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {positions && positions.length ? <FitBounds positions={positions as any} /> : null}
        {positions && positions.length ? <Polyline positions={positions as any} color="blue" /> : null}
        {positions && positions.length ? <>
          <CircleMarker center={positions[0] as any} radius={6} pathOptions={{ color: 'green' }} />
          <CircleMarker center={positions[positions.length - 1] as any} radius={6} pathOptions={{ color: 'red' }} />
        </> : null}
      </MapContainer>
    </div>
  )
}
