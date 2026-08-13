import { useState } from 'react'
import axios from 'axios'
import EmbeddingSpace from './components/EmbeddingSpace'
import ContextPanel from './components/ContextPanel'
import ScoreBars from './components/ScoreBars'
import PipelineFlow from './components/PipelineFlow'

function App() {
  const [query, setQuery] = useState('')
  const [analyzedQuery, setAnalyzedQuery] = useState('')
  const [telemetry, setTelemetry] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleAnalyze = async () => {
    if (!query.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post('/api/analyze', { query, top_k: 5 })
      if (res.data.error) {
        setError(res.data.error)
        setTelemetry(null)
        setAnalyzedQuery('')
      } else {
        setTelemetry(res.data)
        setAnalyzedQuery(query)
      }
    } catch (err) {
      setError('Backend unreachable. Is uvicorn running on :8002?')
      setTelemetry(null)
      setAnalyzedQuery('')
    }
    setLoading(false)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1><span className="prompt">$</span> rag-observatory</h1>
        <p className="tagline">hybrid search · rrf fusion · cross-encoder rerank — traced end to end</p>
      </header>

      <div className="controls">
        <span className="input-prefix">&gt;</span>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          placeholder="ask the index a question…"
        />
        <button onClick={handleAnalyze} disabled={loading || !query.trim()}>
          {loading ? 'running…' : 'run'}
        </button>
      </div>

      <PipelineFlow loading={loading} hasResults={telemetry != null} />

      {error && <div className="error-strip">{error}</div>}

      {telemetry && (
        <div className="results">
          <div className="section-head">
            <h2>retrieval layers</h2>
          </div>
          <ScoreBars telemetry={telemetry} />

          <div className="section-head">
            <h2>context</h2>
          </div>
          <ContextPanel context={telemetry.final_context} />

          <div className="section-head">
            <h2>embedding space</h2>
          </div>
          <EmbeddingSpace query={analyzedQuery} />
        </div>
      )}
    </div>
  )
}

export default App
