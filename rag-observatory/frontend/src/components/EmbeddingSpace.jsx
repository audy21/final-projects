import { useEffect, useState } from 'react'
import axios from 'axios'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer } from 'recharts'

function SpaceTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null
  const point = payload[0].payload

  return (
    <div className="space-tooltip">
      <span className="space-tooltip-text">{point.text}</span>
      <span className="space-tooltip-coords">
        ({point.x.toFixed(2)}, {point.y.toFixed(2)})
      </span>
    </div>
  )
}

function EmbeddingSpace({ query }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    if (!query) return
    axios.get('/api/embedding-space', { params: { query } })
      .then(res => setData(res.data))
      .catch(() => {})
  }, [query])

  if (!data || data.error) return null

  return (
    <div className="embed-panel">
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <XAxis type="number" dataKey="x" stroke="#555" />
          <YAxis type="number" dataKey="y" stroke="#555" />
          <ZAxis range={[80, 80]} />
          <Tooltip
            content={<SpaceTooltip />}
            cursor={{ strokeDasharray: '3 3', stroke: '#6d6a5e' }}
          />
          <Scatter name="chunks" data={data.chunks} fill="#6b7d8a" />
          <Scatter name="query" data={[data.query]} fill="#d4a24e" shape="star" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}

export default EmbeddingSpace