import StatusChip from './StatusChip'

function formatRupiah(value) {
  if (value == null) return '—'
  return 'Rp ' + Number(value).toLocaleString('id-ID')
}

export default function InvoiceList({ invoices, selectedId, onSelect }) {
  if (invoices.length === 0) {
    return <p className="empty">No invoices yet. Upload your first file above.</p>
  }

  return (
    <table className="invoice-table">
      <thead>
        <tr>
          <th>File</th>
          <th>Vendor</th>
          <th className="num">Total</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {invoices.map((inv) => (
          <tr
            key={inv.id}
            className={inv.id === selectedId ? 'selected' : ''}
            onClick={() => onSelect(inv.id)}
          >
            <td className="mono">{inv.filename}</td>
            <td>{inv.vendor || '—'}</td>
            <td className="num mono">{formatRupiah(inv.total)}</td>
            <td><StatusChip status={inv.status} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}