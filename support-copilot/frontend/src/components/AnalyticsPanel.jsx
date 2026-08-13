import { useState, useEffect } from 'react'

function AnalyticsPanel() {
  const [data, setData] = useState(null)

  useEffect(() => {
    const load = async () => {
      const res = await fetch('/api/analytics')
      setData(await res.json())
    }
    load()
    const interval = setInterval(load, 5000)
    return () => clearInterval(interval)
  }, [])

  if (!data) return <div className="analytics-panel"><p className="admin-empty">loading…</p></div>

  const recent = (data.recent || []).slice().reverse()

  return (
    <div className="analytics-panel">
      <div className="stat-cards">
        <div className="stat-card">
          <span className="stat-label">queries</span>
          <span className="stat-value">{data.total_queries}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">escalation</span>
          <span className="stat-value">{(data.escalation_rate * 100).toFixed(0)}%</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">satisfaction</span>
          <span className="stat-value">
            {data.satisfaction_rate !== null ? (data.satisfaction_rate * 100).toFixed(0) + '%' : '—'}
          </span>
        </div>
      </div>

      <div className="recent-queries">
        <h3>recent queries</h3>
        {recent.length === 0 && <p className="admin-empty">no queries yet</p>}
        {recent.map((r, i) => (
          <div key={i} className={`query-row ${r.escalated ? 'esc' : ''}`}>
            <span className="query-text">{r.query}</span>
            <span className="query-conf">conf {r.confidence.toFixed(2)}</span>
            <span className="query-rating">{r.escalated ? '→ human' : (r.rating || '—')}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AnalyticsPanel