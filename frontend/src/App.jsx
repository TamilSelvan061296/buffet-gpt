import { useRef, useState } from 'react'

const SESSION_KEY = 'buffet-session-id'

function getSessionId() {
  let id = localStorage.getItem(SESSION_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(SESSION_KEY, id)
  }
  return id
}

export default function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const sessionRef = useRef(getSessionId())

  async function handleSubmit(e) {
    e.preventDefault()
    if (!question.trim() || loading) return
    setAnswer('')
    setError(null)
    setLoading(true)

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionRef.current,
          message: question,
        }),
      })
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      outer: while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop()
        for (const evt of events) {
          let data = ''
          let type = 'message'
          for (const line of evt.split('\n')) {
            if (line.startsWith('data: ')) data = line.slice(6)
            else if (line.startsWith('event: ')) type = line.slice(7)
          }
          if (type === 'end') break outer
          if (data) setAnswer((prev) => prev + JSON.parse(data))
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const showResponse = loading || answer || error

  return (
    <div className="page">
      <main className="hero">
        <div className="portrait" aria-hidden="true">WB</div>

        <h1 className="title">Chat Warren Buffet</h1>
        <p className="tagline">
          Ask Warren Buffett<sup>*</sup> anything!
        </p>

        <form className="ask" onSubmit={handleSubmit}>
          <textarea
            className="ask-input"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="What's your philosophy on holding stocks for the long term?"
            rows={1}
            disabled={loading}
            autoFocus
          />
          <button
            className="send-btn"
            type="submit"
            disabled={loading || !question.trim()}
            aria-label="Send"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </form>

        {showResponse && (
          <section className="response">
            <div className="response-label">Response</div>
            <div className="response-body">
              {error ? <span className="error">[error: {error}]</span> : answer}
              {loading && <span className="cursor">▍</span>}
            </div>
          </section>
        )}

        <p className="disclaimer">
          <sup>*</sup> This is not actually Warren Buffett (obviously!). It
          summarizes what he&apos;s said in his Berkshire Hathaway shareholder
          letters using a retrieval system over the 1977–2024 letters and an
          LLM. It&apos;s not perfect — if something looks off, take it with a
          grain of salt.
        </p>

        <section className="cards">
          {/* Drop affiliate links into href below */}
          <a className="card" href="#" target="_blank" rel="noopener noreferrer">
            <div className="card-title">THE BOOK</div>
            <div className="card-body">
              <strong>Berkshire Hathaway Letters to Shareholders</strong>
              <span>By Warren Buffett</span>
            </div>
          </a>
          <a className="card" href="#" target="_blank" rel="noopener noreferrer">
            <div className="card-title">THE CHART</div>
            <div className="card-body">
              <strong>50 Years of Berkshire Hathaway</strong>
              <span>Wall print</span>
            </div>
          </a>
        </section>

        <footer className="credits">
          chatwarrenbuffet.com — built on the 1977–2024 shareholder letters.
        </footer>
      </main>
    </div>
  )
}
