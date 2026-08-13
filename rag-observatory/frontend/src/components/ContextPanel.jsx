function ContextPanel({ context }) {
  if (!context) return null

  const chunks = context.split('\n\n')

  return (
    <div className="context-panel">
      <p className="context-meta">{chunks.length} chunks · {context.length} chars</p>
      <div className="context-chunks">
        {chunks.map((chunk, i) => (
          <div key={i} className="context-chunk">
            <span className="chunk-badge">Chunk {i + 1}</span>
            <p>{chunk}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ContextPanel