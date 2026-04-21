import Editor from '@monaco-editor/react'
import ErrorDisplay from './ErrorDisplay'

const PLACEHOLDER = {
  python: `# Write your Python code here
x = 10
print(y)  # NameError: y is not defined
`,
  java: `// Java entry point must be a public class named Main
public class Main {
    public static void main(String[] args) {
        int[] arr = {1, 2, 3};
        System.out.println(arr[5]); // ArrayIndexOutOfBoundsException
    }
}
`,
}

export default function CodePanel({
  language, setLanguage,
  code, setCode,
  stdout, stderr, exitCode,
  running, onRun, error,
  keepChatOnRun, setKeepChatOnRun,
}) {
  const handleLanguageChange = (lang) => {
    setLanguage(lang)
    if (!code.trim()) setCode(PLACEHOLDER[lang])
  }

  return (
    <div className="flex flex-col h-full">
      {/* Language selector */}
      <div className="flex gap-2 mb-3">
        {['python', 'java'].map((lang) => (
          <button
            key={lang}
            onClick={() => handleLanguageChange(lang)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              language === lang
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200'
            }`}
          >
            {lang === 'python' ? 'Python' : 'Java'}
          </button>
        ))}
      </div>

      {/* Monaco editor */}
      <div className="flex-1 rounded-lg overflow-hidden border border-gray-700 min-h-0">
        <Editor
          height="100%"
          language={language === 'java' ? 'java' : 'python'}
          value={code}
          onChange={(val) => setCode(val ?? '')}
          theme="vs-dark"
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
            renderLineHighlight: 'line',
            padding: { top: 12, bottom: 12 },
            tabSize: language === 'java' ? 4 : 4,
          }}
        />
      </div>

      <label className="mt-3 flex items-start gap-2.5 cursor-pointer select-none">
        <input
          type="checkbox"
          checked={keepChatOnRun}
          onChange={(e) => setKeepChatOnRun(e.target.checked)}
          className="mt-0.5 rounded border-gray-600 bg-gray-800 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-0 focus:ring-offset-gray-950"
        />
        <span className="text-xs text-gray-400 leading-snug">
          Keep tutor chat when re-running
          <span className="block text-gray-600 mt-0.5">
            First run or expired session still starts fresh on the server.
          </span>
        </span>
      </label>

      {/* Run button */}
      <button
        onClick={onRun}
        disabled={running || !code.trim()}
        className="mt-3 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-lg transition-colors"
      >
        {running ? (
          <>
            <Spinner />
            Running…
          </>
        ) : (
          <>
            <span className="text-base">▶</span>
            Run Code
          </>
        )}
      </button>

      {/* API / network error */}
      {error && (
        <div className="mt-2 text-xs text-red-400 bg-red-950/40 rounded px-3 py-2">
          {error}
        </div>
      )}

      {/* Java note */}
      {language === 'java' && (
        <p className="mt-2 text-xs text-gray-500">
          Note: Java code must have a public class named <code className="text-gray-400">Main</code> with a{' '}
          <code className="text-gray-400">main</code> method.
        </p>
      )}

      {/* Output */}
      <ErrorDisplay stdout={stdout} stderr={stderr} exitCode={exitCode} />
    </div>
  )
}

function Spinner() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v8H4z"
      />
    </svg>
  )
}
