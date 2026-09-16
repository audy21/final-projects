import { useCallback, useEffect, useState } from 'react'
import * as api from './api'
import UploadZone from './components/UploadZone'
import InvoiceList from './components/InvoiceList'
import ReviewPanel from './components/ReviewPanel'
import Dashboard from './components/Dashboard'

export default function App() {
  const [tab, setTab] = useState('inbox')
  const [invoices, setInvoices] = useState([])
  const [selectedId, setSelectedId] = useState(null)

  const refresh = useCallback(async () => {
    const data = await api.listInvoices()
    setInvoices(data)
  }, [])

  useEffect(() => {
    (async () => {
      const data = await api.listInvoices()
      setInvoices(data)
    })()
  }, [])

  useEffect(() => {
    const pending = invoices.some((inv) => ['queued', 'extracting'].includes(inv.status))
    if (!pending) return
    const timer = setInterval(refresh, 2500)
    return () => clearInterval(timer)
  }, [invoices, refresh])

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Invoice Inbox</h1>
          <p className="tagline">Invoice processing automation for finance teams</p>
        </div>
        <nav className="tabs">
          <button className={tab === 'inbox' ? 'active' : ''} onClick={() => setTab('inbox')}>Inbox</button>
          <button className={tab === 'dashboard' ? 'active' : ''} onClick={() => setTab('dashboard')}>Dashboard</button>
        </nav>
      </header>

      {tab === 'inbox' && (
        <>
          <UploadZone onUploaded={refresh} />
          {selectedId ? (
            <>
              <button className="back-link" onClick={() => setSelectedId(null)}>← Back to list</button>
              <ReviewPanel invoiceId={selectedId} onChanged={refresh} />
            </>
          ) : (
            <InvoiceList invoices={invoices} selectedId={selectedId} onSelect={setSelectedId} />
          )}
        </>
      )}
      {tab === 'dashboard' && <Dashboard />}
    </div>
  )
}