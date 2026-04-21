import { useState, useCallback } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { runCode as apiRunCode, sendMessage as apiSendMessage } from '../api/client'

const SESSION_ID = uuidv4()

export function useSession() {
  const [language, setLanguage] = useState('python')
  const [code, setCode] = useState('')
  const [stdout, setStdout] = useState('')
  const [stderr, setStderr] = useState('')
  const [exitCode, setExitCode] = useState(null)
  const [messages, setMessages] = useState([]) // { role: 'tutor'|'student', content, isReveal? }
  const [hintCount, setHintCount] = useState(0)
  const [maxHints] = useState(5)
  const [resolved, setResolved] = useState(false)
  const [keepChatOnRun, setKeepChatOnRun] = useState(false)
  const [running, setRunning] = useState(false)
  const [chatLoading, setChatLoading] = useState(false)
  const [error, setError] = useState(null)

  const runCode = useCallback(async () => {
    if (!code.trim()) return
    setRunning(true)
    setError(null)

    try {
      const data = await apiRunCode(SESSION_ID, language, code, keepChatOnRun)
      setStdout(data.stdout)
      setStderr(data.stderr)
      setExitCode(data.exit_code)
      // Older backends omit conversation_reset; treat missing as full reset.
      if (data.conversation_reset !== false) {
        setMessages([{ role: 'tutor', content: data.tutor_message }])
        setHintCount(0)
      }
      setResolved(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run code. Is the backend running?')
    } finally {
      setRunning(false)
    }
  }, [code, language, keepChatOnRun])

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || resolved) return
    setChatLoading(true)

    setMessages((prev) => [...prev, { role: 'student', content: text }])

    try {
      const data = await apiSendMessage(SESSION_ID, text)
      const isReveal = data.hint_count >= data.max_hints && !data.resolved
      setMessages((prev) => [
        ...prev,
        { role: 'tutor', content: data.reply, isReveal },
      ])
      setHintCount(data.hint_count)
      setResolved(data.resolved)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'tutor',
          content: "I'm having trouble responding right now, please try again.",
        },
      ])
    } finally {
      setChatLoading(false)
    }
  }, [resolved])

  return {
    language, setLanguage,
    code, setCode,
    stdout, stderr, exitCode,
    messages,
    hintCount, maxHints,
    resolved,
    keepChatOnRun, setKeepChatOnRun,
    running, chatLoading,
    error,
    runCode,
    sendMessage,
  }
}
