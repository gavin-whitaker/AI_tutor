import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

export async function runCode(sessionId, language, code) {
  const res = await api.post('/run', { session_id: sessionId, language, code })
  return res.data
}

export async function sendMessage(sessionId, message) {
  const res = await api.post('/chat', { session_id: sessionId, message })
  return res.data
}
