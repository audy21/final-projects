import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LabelList } from 'recharts'

function ScoreTooltip({ active, payload, layer }) {
  if (!active || !payload || !payload.length) return null
  const item = payload[0].payload
  const rank = payload[0].index + 1

  return (
    <div className="score-tooltip">
      <div className="score-tooltip-head">
        <span className="score-tooltip-layer">{layer}</span>
        <span className="score-tooltip-rank">#{rank}</span>
        <span className="score-tooltip-value">{item.score.toFixed(4)}</span>
      </div>
      <p className="score-tooltip-text">{item.chunk}</p>
    </div>
  )
}

function ScoreBars({ telemetry }) {
  const layers = ['semantic', 'bm25', 'rrf', 'rerank']
  const colors = { semantic: '#8a7d5c', bm25: '#6b7d8a', rrf: '#7d8a6b', rerank: '#d4a24e' }

  return (
    <div className="score-grid">
      {layers.map(layer => (
        <div key={layer} className="score-panel">
          <h3 style={{ color: colors[layer] }}>{layer}</h3>
          <ResponsiveContainer width="100%" height={Math.max(90, (telemetry[layer] || []).length * 34 + 30)}>
            <BarChart data={telemetry[layer] || []} layout="vertical" margin={{ top: 4, right: 64, bottom: 4, left: 0 }}>
              <XAxis type="number" hide />
              <YAxis type="category" dataKey="chunk" hide />
              <Tooltip content={<ScoreTooltip layer={layer} />} cursor={{ fill: 'rgba(212,162,78,0.05)' }} />
              <Bar dataKey="score" fill={colors[layer]} barSize={12} radius={[0, 3, 3, 0]}>
                <LabelList
                  dataKey="score"
                  position="right"
                  formatter={(v) => v.toFixed(4)}
                  fill="#8f8c7f"
                  fontSize={10}
                  fontFamily="ui-monospace, Menlo, monospace"
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  )
}

export default ScoreBars
