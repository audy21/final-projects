import { useRef, useState } from 'react'
import { uploadInvoice } from '../api'

export default function UploadZone({ onUploaded }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function handleFiles(files) {
    setError(null)
    setBusy(true)
    try {
      for (const file of files) {
        await uploadInvoice(file)
      }
      onUploaded()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className={`upload-zone ${dragging ? 'dragging' : ''}`}
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragging(false)
        handleFiles([...e.dataTransfer.files])
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        multiple
        hidden
        onChange={(e) => handleFiles([...e.target.files])}
      />
      <p className="upload-title">{busy ? 'Uploading…' : 'Drop invoices here, or click to choose files'}</p>
      <p className="upload-hint">PDF, PNG, or JPG. Multiple files supported.</p>
      {error && <p className="upload-error">{error}</p>}
    </div>
  )
}