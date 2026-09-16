const LABELS = {
  queued: 'Queued',
  extracting: 'Extracting',
  needs_review: 'Needs Review',
  approved: 'Approved',
  failed: 'Failed'
}

export default function StatusChip({ status }) {
  return <span className={`chip chip-${status}`}>{LABELS[status] || status}</span>
}