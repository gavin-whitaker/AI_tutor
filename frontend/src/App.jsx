import CodePanel from './components/CodePanel'
import ChatPanel from './components/ChatPanel'
import { useSession } from './hooks/useSession'

export default function App() {
  const session = useSession()

  return (
    <div className="flex flex-col h-screen bg-gray-950">
      {/* Top bar */}
      <header className="flex items-center px-6 py-3 border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-indigo-600 rounded-md flex items-center justify-center text-white text-sm font-bold">
            S
          </div>
          <span className="font-semibold text-gray-100 text-sm tracking-tight">
            Socratic Debugging Tutor
          </span>
        </div>
        <p className="ml-4 text-xs text-gray-500 hidden sm:block">
          Fix your bugs by reasoning through them, not just Googling the answer.
        </p>
      </header>

      {/* Main layout */}
      <main className="flex flex-1 overflow-hidden gap-0">
        {/* Left — code */}
        <div className="flex flex-col w-1/2 border-r border-gray-800 p-5 overflow-hidden">
          <CodePanel
            language={session.language}
            setLanguage={session.setLanguage}
            code={session.code}
            setCode={session.setCode}
            stdout={session.stdout}
            stderr={session.stderr}
            exitCode={session.exitCode}
            running={session.running}
            onRun={session.runCode}
            error={session.error}
          />
        </div>

        {/* Right — chat */}
        <div className="flex flex-col w-1/2 p-5 overflow-hidden">
          <ChatPanel
            messages={session.messages}
            hintCount={session.hintCount}
            maxHints={session.maxHints}
            resolved={session.resolved}
            loading={session.chatLoading}
            onSend={session.sendMessage}
          />
        </div>
      </main>
    </div>
  )
}
