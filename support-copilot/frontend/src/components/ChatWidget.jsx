import { useState, useRef, useEffect } from 'react'

function ChatWidget() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [status, setStatus] = useState('idle') // idle | retrieving | streaming | escalated | done
  const [confidence, setConfidence] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [rating, setRating] = useState(null)
  const [connError, setConnError] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, status])

  const send = () => {
    if (!input.trim() || status === 'retrieving' || status === 'streaming') return

    setMessages(m => [...m, { role: 'user', content: input }])
    setStatus('retrieving')
    setConfidence(null)
    setRating(null)
    setConnError(false)

    const es = new EventSource(`/api/chat?query=${encodeURIComponent(input)}`)

    es.addEventListener('retrieval', (e) => {
      const d = JSON.parse(e.data)
      setConfidence(d.confidence)
      setStatus('streaming')
    })

    es.addEventListener('token', (e) => {
      setMessages(m => {
        const copy = [...m]
        const last = copy[copy.length - 1]
        if (last && last.role === 'assistant') {
          last.content += e.data
        } else {
          copy.push({ role: 'assistant', content: e.data })
        }
        return copy
      })
    })

    es.addEventListener('escalate', (e) => {
      const d = JSON.parse(e.data)
      setStatus('escalated')
      setConfidence(d.confidence)
      es.close()
    })

    es.addEventListener('done', (e) => {
      const d = JSON.parse(e.data)
      setSessionId(d.session_id)
      setStatus('done')
      es.close()
    })

    es.onerror = () => {
      setStatus('idle')
      setConnError(true)
      es.close()
    }

    setInput('')
  }

  const sendFeedback = async (val) => {
    if (!sessionId) return
    setRating(val)
    await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, rating: val })
    })
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>no conversation yet</p>
            <p className="chat-empty-hint">try: "how do i reset my password?" or "my cat ate my invoice"</p>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <span className="msg-role">{m.role === 'user' ? 'you' : 'bot'}</span>
            <p className="msg-text">{m.content}</p>
          </div>
        ))}

        {status === 'retrieving' && (
          <div className="msg assistant">
            <span className="msg-role">bot</span>
            <p className="msg-text typing">searching knowledge base…</p>
          </div>
        )}

        {status === 'escalated' && (
          <div className="msg escalate">
            <span className="msg-role">handoff</span>
            <p className="msg-text">confidence {confidence.toFixed(2)} is below threshold — a human will take over.</p>
          </div>
        )}
      </div>

      <div className="chat-status">
        {connError && (
          <div className="conn-error">
            <span>connection failed</span>
            <button onClick={() => setConnError(false)}>dismiss</button>
          </div>
        )}
        {confidence !== null && (
          <span className={`confidence ${confidence < 0.55 ? 'low' : 'ok'}`}>
            confidence {confidence.toFixed(2)}
          </span>
        )}
        {status === 'done' && (
          <div className="feedback">
            <span>helpful?</span>
            <button className={rating === 'up' ? 'picked' : ''} onClick={() => sendFeedback('up')}>yes</button>
            <button className={rating === 'down' ? 'picked' : ''} onClick={() => sendFeedback('down')}>no</button>
          </div>
        )}
      </div>

      <div className="chat-input">
        <span className="input-prefix">&gt;</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="ask the knowledge base…"
        />
        <button onClick={send} disabled={!input.trim() || status === 'retrieving' || status === 'streaming'}>send</button>
      </div>
    </div>
  )
}

export default ChatWidget