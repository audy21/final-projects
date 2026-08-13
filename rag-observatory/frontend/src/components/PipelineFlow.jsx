function PipelineFlow({ loading, hasResults }) {
  const steps = ['Query', 'Hybrid Search', 'RRF Fusion', 'Rerank', 'Context']

  return (
    <div className="pipeline">
      {steps.map((step, i) => {
        let state = 'idle'
        if (hasResults) state = 'done'
        else if (loading && i === 0) state = 'loading'

        return (
          <div key={step} className="pipeline-step">
            <div className={`step-dot ${state}`}>{state === 'loading' ? '' : i + 1}</div>
            <span className={`step-label ${state}`}>{step}</span>
            {i < steps.length - 1 && <div className={`step-line ${state === 'done' ? 'done' : ''}`} />}
          </div>
        )
      })}
    </div>
  )
}

export default PipelineFlow
