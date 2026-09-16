export default function ConfidenceBadge({ value }) {
  if (value == null) return null
  const pct = Math.round(value * 100)
  let level = 'low'
  if (value >= 0.8) level = 'high'
  else if (value >= 0.5) level = 'mid'
  return <span className={`confidence confidence-${level}`}>{pct}%</span>
}