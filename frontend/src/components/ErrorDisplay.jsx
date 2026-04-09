export default function ErrorDisplay({ stdout, stderr, exitCode }) {
  if (exitCode === null) return null

  const hasOutput = stdout || stderr

  return (
    <div className="mt-3">
      <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
        Output
      </div>
      {!hasOutput && exitCode === 0 && (
        <div className="text-xs text-green-400 font-mono bg-gray-900 rounded px-3 py-2">
          (no output — code ran successfully)
        </div>
      )}
      {stdout && (
        <pre className="text-xs font-mono bg-gray-900 rounded px-3 py-2 text-gray-200 whitespace-pre-wrap break-all max-h-28 overflow-y-auto">
          {stdout}
        </pre>
      )}
      {stderr && (
        <pre className="text-xs font-mono bg-gray-900 rounded px-3 py-2 text-red-400 whitespace-pre-wrap break-all max-h-28 overflow-y-auto mt-1">
          {stderr}
        </pre>
      )}
    </div>
  )
}
