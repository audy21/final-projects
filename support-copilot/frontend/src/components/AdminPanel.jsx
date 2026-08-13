import { useState, useEffect } from 'react'

function AdminPanel() {
  const [text, setText] = useState('')
  const [docId, setDocId] = useState('')
  const [docs, setDocs] = useState([])

  const loadDocs = async () => {
    const res = await fetch('/api/kb/list')
    const data = await res.json()
    setDocs(data.documents)
  }

  useEffect(() => {
    (async () => {
      const res = await fetch('/api/kb/list')
      const data = await res.json()
      setDocs(data.documents)
    })()
  }, [])

  const ingest = async () => {
    if (!text.trim() || !docId.trim()) return
    await fetch('/api/kb/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, doc_id: docId })
    })
    setText('')
    setDocId('')
    loadDocs()
  }

  const remove = async (id) => {
    await fetch(`/api/kb/${id}`, { method: 'DELETE' })
    loadDocs()
  }

  return (
    <div className="admin-panel">
      <div className="admin-form">
        <label>document id</label>
        <input value={docId} onChange={(e) => setDocId(e.target.value)} placeholder="faq" />
        <label>content</label>
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={8} placeholder="paste knowledge base text…" />
        <button onClick={ingest} disabled={!text.trim() || !docId.trim()}>ingest</button>
      </div>

      <div className="admin-list">
        <h3>knowledge base ({docs.length})</h3>
        {docs.length === 0 && <p className="admin-empty">empty — ingest something first</p>}
        {docs.map(d => (
          <div key={d.doc_id} className="admin-doc">
            <span className="doc-id">{d.doc_id}</span>
            <span className="doc-chunks">{d.chunks} chunks</span>
            <button className="doc-delete" onClick={() => remove(d.doc_id)}>remove</button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AdminPanel