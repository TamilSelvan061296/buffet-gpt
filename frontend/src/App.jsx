import { useEffect, useRef, useState } from 'react'

const SESSION_KEY = 'buffet-session-id'
const EXAMPLE_QUESTIONS = [
  'How is value investing different from growth investing?',
  'What makes a business worth holding for decades?',
  'When should I avoid buying a stock?',
]

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
  const [messages, setMessages] = useState([])
  const [exampleIndex, setExampleIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const sessionRef = useRef(getSessionId())
  const chatEndRef = useRef(null)
  const hasMessages = messages.length > 0

  useEffect(() => {
    if (hasMessages || question) return undefined
    const interval = window.setInterval(() => {
      setExampleIndex((current) => (current + 1) % EXAMPLE_QUESTIONS.length)
    }, 2800)
    return () => window.clearInterval(interval)
  }, [hasMessages, question])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  function startNewChat() {
    if (loading) return
    const id = crypto.randomUUID()
    localStorage.setItem(SESSION_KEY, id)
    sessionRef.current = id
    setMessages([])
    setQuestion('')
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const text = question.trim()
    if (!text || loading) return

    const assistantId = crypto.randomUUID()
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: 'user', content: text },
      { id: assistantId, role: 'assistant', content: '' },
    ])
    setQuestion('')
    setLoading(true)

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionRef.current,
          message: text,
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
          if (data) {
            const chunk = JSON.parse(data)
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, content: message.content + chunk }
                  : message
              )
            )
          }
        }
      }
    } catch (err) {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === assistantId
            ? { ...message, content: `[error: ${err.message}]`, error: true }
            : message
        )
      )
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

  return (
    <div className={`page ${hasMessages ? 'chat-mode' : 'landing-mode'}`}>
      <main className="hero">
        {hasMessages ? (
          <header className="topbar">
            <div className="brand">
              <div className="portrait" aria-hidden="true">WB</div>
              <div>
                <h1 className="title">Chat Warren Buffett</h1>
                <p className="tagline">
                  Ask Warren Buffett<sup>*</sup> anything.
                </p>
              </div>
            </div>
            <button
              className="new-chat"
              type="button"
              onClick={startNewChat}
              disabled={loading}
            >
              New chat
            </button>
          </header>
        ) : (
          <section className="landing-brand" aria-label="BuffettBot">
            <img
              className="landing-portrait"
              src="/warren-buffet.png"
              alt=""
              onError={(e) => {
                e.currentTarget.style.display = 'none'
              }}
            />
            <p className="landing-subtitle">
              Ask Warren Buffett<sup>*</sup> anything!
            </p>
          </section>
        )}

        {hasMessages && (
          <section className="conversation" aria-live="polite">
            {messages.map((message) => (
              <div
                className={`message ${message.role} ${message.error ? 'error' : ''}`}
                key={message.id}
              >
                <div className="message-label">
                  {message.role === 'user' ? 'You' : 'Buffett'}
                </div>
                <div className="message-body">
                  {message.content}
                  {loading && message.id === messages[messages.length - 1]?.id && (
                    <span className="cursor">▍</span>
                  )}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </section>
        )}

        <form className="ask" onSubmit={handleSubmit}>
          <div className="input-wrap">
            {!hasMessages && !question && (
              <div className="example-placeholder" key={exampleIndex}>
                {EXAMPLE_QUESTIONS[exampleIndex]}
              </div>
            )}
            <textarea
              className="ask-input"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder={hasMessages ? 'Ask a follow-up' : ''}
              rows={1}
              disabled={loading}
              autoFocus
            />
          </div>
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

        <p className="disclaimer">
          <sup>*</sup> This is an AI experience inspired by Warren Buffett&apos;s
          Berkshire Hathaway shareholder letters from 1977–2024. It uses
          retrieval over those letters to answer in his style, but it may still
          get things wrong.
        </p>

        <footer className="credits">
          Built and maintained by{' '}
          <a
            href="https://www.linkedin.com/in/tamil-selvan-murugesan/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Tamil Selvan Murugesan
          </a>
        </footer>
      </main>
    </div>
  )
}
