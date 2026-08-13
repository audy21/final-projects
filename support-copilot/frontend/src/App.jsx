import { useState } from 'react'
import ChatWidget from './components/ChatWidget'
import AdminPanel from './components/AdminPanel'
import AnalyticsPanel from './components/AnalyticsPanel'

function App() {
  const [tab, setTab] = useState('chat')

  const tabs = ['chat', 'admin', 'analytics']

  return (
    <main className="app">
      <header className="app-header">
        <h1><span className="prompt">$</span> support-copilot</h1>
        <p className="tagline">kb-backed answers · confidence-gated escalation · human handoff</p>
      </header>

      <nav className="tabs">
        {tabs.map(t => (
          <button
            key={t}
            className={`tab ${tab === t ? 'active' : ''}`}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === 'chat' && <ChatWidget />}
      {tab === 'admin' && <AdminPanel />}
      {tab === 'analytics' && <AnalyticsPanel />}
    </main>
  )
}

export default App