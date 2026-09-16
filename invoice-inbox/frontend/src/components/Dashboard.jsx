import { useEffect, useState } from 'react'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts'
import * as api from '../api'

function formatRupiah(value) {
  return 'Rp ' + Number(value).toLocaleString('id-ID')
}

function shortRupiah(value) {
  if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + 'B'
  if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + 'M'
  if (value >= 1_000) return Math.round(value / 1_000) + 'k'
  return String(value)
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    const load = () => api.getStats().then(setStats)
    load()
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [])

  if (!stats) return <p className="empty">Loading…</p>

  const { counts, total_spend, by_vendor, by_month } = stats

  return (
    <div className="dashboard">
      <div className="cards">
        <div className="card">
          <span className="card-label">Total approved spend</span>
          <span className="card-value mono">{formatRupiah(total_spend)}</span>
        </div>
        <div className="card">
          <span className="card-label">Needs review</span>
          <span className="card-value mono">{counts.needs_review}</span>
        </div>
        <div className="card">
          <span className="card-label">Approved</span>
          <span className="card-value mono">{counts.approved}</span>
        </div>
        <div className="card">
          <span className="card-label">Failed</span>
          <span className="card-value mono">{counts.failed}</span>
        </div>
      </div>

      <div className="chart-block">
        <div className="chart-head">
          <h2>Spend by vendor</h2>
          <a className="btn" href={api.exportUrl()}>Download CSV</a>
        </div>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={by_vendor} layout="vertical" margin={{ top: 4, right: 40, bottom: 4, left: 8 }}>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="vendor" width={160} tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value) => [formatRupiah(value), 'Total']}
              contentStyle={{ background: '#fff', border: '1px solid #e4e4e7', borderRadius: 3, fontSize: 13 }}
            />
            <Bar dataKey="total" fill="#18181b" barSize={14} radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="chart-block">
        <h2>Spend by month</h2>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={by_month} margin={{ top: 8, right: 24, bottom: 4, left: 8 }}>
            <XAxis dataKey="month" tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={shortRupiah} tick={{ fontSize: 12 }} width={56} />
            <Tooltip
              formatter={(value) => [formatRupiah(value), 'Total']}
              contentStyle={{ background: '#fff', border: '1px solid #e4e4e7', borderRadius: 3, fontSize: 13 }}
            />
            <Line type="monotone" dataKey="total" stroke="#059669" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}