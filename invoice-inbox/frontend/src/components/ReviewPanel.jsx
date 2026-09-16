import { useEffect, useState } from 'react'
import * as api from '../api'
import ConfidenceBadge from './ConfidenceBadge'
import StatusChip from './StatusChip'

const FIELD_LABELS = {
  vendor: 'Vendor',
  invoice_number: 'Invoice No.',
  invoice_date: 'Date',
  due_date: 'Due Date',
  currency: 'Currency',
  subtotal: 'Subtotal',
  tax: 'Tax',
  total: 'Total'
}

function formatRupiah(value) {
  if (value == null || value === '') return ''
  return 'Rp ' + Number(value).toLocaleString('id-ID')
}

export default function ReviewPanel({ invoiceId, onChanged }) {
  const [invoice, setInvoice] = useState(null)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    (async () => {
      const data = await api.getInvoice(invoiceId)
      setMessage(null)
      setInvoice(data)
      setForm({
        vendor: data.vendor || '',
        invoice_number: data.invoice_number || '',
        invoice_date: data.invoice_date || '',
        due_date: data.due_date || '',
        currency: data.currency || 'IDR',
        subtotal: data.subtotal ?? '',
        tax: data.tax ?? '',
        total: data.total ?? ''
      })
    })()
  }, [invoiceId])

  if (!invoice) return <div className="review-panel"><p className="empty">Loading…</p></div>

  const isPdf = invoice.file_type === 'pdf'
  const confidence = invoice.field_confidence || {}
  const editable = invoice.status !== 'approved'

  async function save() {
    setSaving(true)
    setMessage(null)
    try {
      const payload = { ...form }
      for (const key of ['subtotal', 'tax', 'total']) {
        payload[key] = form[key] === '' ? null : Number(form[key])
      }
      await api.updateInvoice(invoice.id, payload)
      setMessage('Changes saved.')
      onChanged()
    } catch (err) {
      setMessage(err.message)
    } finally {
      setSaving(false)
    }
  }

  async function approve() {
    await api.approveInvoice(invoice.id)
    onChanged()
  }

  async function retry() {
    await api.retryInvoice(invoice.id)
    onChanged()
  }

  return (
    <div className="review-panel">
      <div className="review-head">
        <div>
          <p className="review-file mono">{invoice.filename}</p>
          <StatusChip status={invoice.status} />
        </div>
        <div className="review-actions">
          {invoice.status === 'failed' && (
            <button className="btn" onClick={retry}>Retry</button>
          )}
          {editable && (
            <>
              <button className="btn" onClick={save} disabled={saving}>Save</button>
              <button className="btn btn-approve" onClick={approve}>Approve</button>
            </>
          )}
        </div>
      </div>

      {message && <p className="review-message">{message}</p>}
      {invoice.error && <p className="review-error">{invoice.error}</p>}

      <div className="review-grid">
        <div className="preview">
          {isPdf
            ? <iframe title="preview" src={api.fileUrl(invoice.id)} />
            : <img src={api.fileUrl(invoice.id)} alt={invoice.filename} />}
        </div>

        <div className="fields">
          {Object.entries(FIELD_LABELS).map(([key, label]) => (
            <div className="field" key={key}>
              <label>
                {label}
                <ConfidenceBadge value={confidence[key]} />
              </label>
              <input
                value={form[key]}
                disabled={!editable}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                className={['subtotal', 'tax', 'total'].includes(key) ? 'mono' : ''}
              />
              {['subtotal', 'tax', 'total'].includes(key) && form[key] !== '' && (
                <span className="field-hint mono">{formatRupiah(form[key])}</span>
              )}
            </div>
          ))}

          {Array.isArray(invoice.line_items) && invoice.line_items.length > 0 && (
            <div className="line-items">
              <p className="line-items-title">Line items</p>
              <table className="invoice-table">
                <thead>
                  <tr><th>Description</th><th className="num">Qty</th><th className="num">Price</th><th className="num">Amount</th></tr>
                </thead>
                <tbody>
                  {invoice.line_items.map((item, i) => (
                    <tr key={i}>
                      <td>{item.description}</td>
                      <td className="num mono">{item.qty}</td>
                      <td className="num mono">{formatRupiah(item.unit_price)}</td>
                      <td className="num mono">{formatRupiah(item.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}