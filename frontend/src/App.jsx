import { useState } from 'react'

function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`http://localhost:8000/search?query=${encodeURIComponent(query)}`)
      if (!response.ok) {
        throw new Error('Network response was not ok')
      }
      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError('Errore durante la ricerca. Riprova.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg overflow-hidden md:max-w-2xl">
        <div className="md:flex">
          <div className="p-8 w-full">
            <div className="uppercase tracking-wide text-sm text-indigo-500 font-semibold mb-1">Ricerca Automatica</div>
            <h1 className="block mt-1 text-2xl leading-tight font-medium text-black">Trova Numero Ambulatorio</h1>
            <p className="mt-2 text-gray-500">Inserisci il nome dell'ambulatorio per trovare il numero di telefono.</p>

            <form onSubmit={handleSearch} className="mt-6 flex gap-2">
              <input
                type="text"
                className="w-full px-4 py-2 border rounded-lg text-gray-700 focus:outline-none focus:border-indigo-500"
                placeholder="Es. Ambulatorio San Marco Milano"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 focus:outline-none disabled:bg-indigo-300 transition-colors"
              >
                {loading ? '...' : 'Cerca'}
              </button>
            </form>

            <div className="mt-8">
              {loading && <div className="text-gray-600 text-center animate-pulse">Ricerca in corso...</div>}
              {error && <div className="text-red-500 text-center">{error}</div>}

              {result && (
                <div className="bg-gray-100 p-4 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-800">Risultato:</h3>
                  <div className="mt-2 text-gray-700">
                    <p><span className="font-bold">Ambulatorio:</span> {result.query}</p>
                    <p><span className="font-bold">Telefono:</span> {result.phone_number}</p>
                    <p><span className="font-bold">Fonte:</span> <span className={`inline-block px-2 py-0.5 rounded text-xs ${result.source === 'OpenAI' ? 'bg-green-200 text-green-800' : 'bg-blue-200 text-blue-800'}`}>{result.source}</span></p>
                  </div>
                  {result.phone_number === 'Not Found' && (
                    <p className="mt-4 text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                      Non siamo riusciti a trovare il numero. Abbiamo provato con Google e AI.
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
