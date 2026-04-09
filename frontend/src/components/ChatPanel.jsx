import { useEffect, useRef, useState } from 'react'

export default function ChatPanel({ messages, hintCount, maxHints, resolved, loading, onSend }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = () => {
    const text = input.trim()
    if (!text) return
    onSend(text)
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-200 text-sm">Tutor</h2>
        {hasMessages && (
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              hintCount >= maxHints
                ? 'bg-red-900/60 text-red-300'
                : hintCount > 0
                ? 'bg-yellow-900/40 text-yellow-300'
                : 'bg-gray-800 text-gray-400'
            }`}
          >
            Hints: {hintCount} / {maxHints}
          </span>
        )}
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-0">
        {!hasMessages && (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-600 text-sm text-center">
              Write some code and click <strong className="text-gray-500">Run Code</strong> to start the session.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} maxHints={maxHints} hintCount={hintCount} />
        ))}

        {loading && (
          <div className="flex gap-2 items-start">
            <Avatar role="tutor" />
            <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-2.5 max-w-xs">
              <TypingDots />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Resolved banner */}
      {resolved && (
        <div className="mt-3 bg-green-900/40 border border-green-700/50 rounded-lg px-4 py-3 text-center">
          <p className="text-green-400 font-semibold text-sm">Bug fixed!</p>
          <p className="text-green-500/80 text-xs mt-0.5">
            Run new code to start a fresh session.
          </p>
        </div>
      )}

      {/* Input */}
      {!resolved && (
        <div className="mt-3 flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading || !hasMessages}
            placeholder={hasMessages ? 'Type a message… (Enter to send)' : 'Run code first…'}
            rows={2}
            className="flex-1 resize-none bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim() || !hasMessages}
            className="self-end bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg px-3 py-2 transition-colors"
            aria-label="Send"
          >
            <SendIcon />
          </button>
        </div>
      )}
    </div>
  )
}

function MessageBubble({ msg, maxHints, hintCount }) {
  const isTutor = msg.role === 'tutor'
  const isReveal = msg.isReveal

  return (
    <div className={`flex gap-2 ${isTutor ? 'items-start' : 'items-start flex-row-reverse'}`}>
      <Avatar role={msg.role} />
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isTutor
            ? isReveal
              ? 'bg-amber-900/40 border border-amber-700/50 rounded-tl-sm text-amber-200'
              : 'bg-gray-800 rounded-tl-sm text-gray-200'
            : 'bg-indigo-700 rounded-tr-sm text-white'
        }`}
      >
        {isReveal && (
          <p className="text-xs text-amber-400 font-semibold mb-1 uppercase tracking-wide">
            Answer Revealed
          </p>
        )}
        <p className="whitespace-pre-wrap">{msg.content}</p>
      </div>
    </div>
  )
}

function Avatar({ role }) {
  return (
    <div
      className={`w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${
        role === 'tutor'
          ? 'bg-indigo-700 text-indigo-200'
          : 'bg-gray-700 text-gray-300'
      }`}
    >
      {role === 'tutor' ? 'T' : 'S'}
    </div>
  )
}

function TypingDots() {
  return (
    <div className="flex gap-1 items-center h-4">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  )
}

function SendIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      className="h-5 w-5"
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
    </svg>
  )
}
