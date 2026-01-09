import { useState } from 'react'

function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const production = false;
  const productionUrl = '13.50.100.103';
  const [showDetails, setShowDetails] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query) return

    setLoading(true)
    setError(null)
    setResult(null)
    setShowDetails(false)

    try {
      const response = await fetch(`http://${production ? productionUrl : 'localhost'}:8000/search?query=${encodeURIComponent(query)}`)
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
            <p className="text-xs text-indigo-400 mt-1">Nota: La ricerca è limitata al contesto medico/ambulatoriale.</p>

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
                <div className={`p-4 rounded-lg border ${result.phone_number === 'Off-Topic' ? 'bg-red-50 border-red-200' : 'bg-gray-100 border-gray-200'}`}>
                  <h3 className="text-lg font-semibold text-gray-800">Risultato:</h3>
                  {result.phone_number === 'Off-Topic' ? (
                    <div className="mt-2 text-red-700">
                      <p className="font-bold">Richiesta non valida.</p>
                      <p className="text-sm mt-1">Per favora inserisci una ricerca relativa ad ambulatori, medici o strutture sanitarie.</p>
                    </div>
                  ) : (
                    <div className="mt-2 text-gray-700 space-y-2">
                      <div><span className="font-bold">Ambulatorio:</span> {result.query}</div>
                      <div><span className="font-bold">Telefono:</span> {result.phone_number}</div>

                      {/* Main Source / Consensus Info */}
                      <div>
                        <span className="font-bold">Fonte Principale:</span>
                        <span className={`ml-2 inline-block px-2 py-0.5 rounded text-xs ${result.source.includes('OpenAI') ? 'bg-green-200 text-green-800' : 'bg-blue-200 text-blue-800'}`}>
                          {result.source}
                        </span>
                      </div>

                      {/* Dropdown for Details */}
                      {result.details && result.details.length > 0 && (
                        <div className="mt-4 pt-2 border-t border-gray-200">
                          <button
                            onClick={() => setShowDetails(!showDetails)}
                            className="text-sm text-indigo-600 hover:text-indigo-800 focus:outline-none flex items-center"
                          >
                            {showDetails ? 'Nascondi dettagli' : 'Mostra altre fonti'}
                            <svg className={`w-4 h-4 ml-1 transform transition-transform ${showDetails ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>

                          {showDetails && (
                            <div className="mt-2 space-y-2">
                              {result.details.map((item, index) => (
                                <div key={index} className="text-xs bg-white p-2 rounded border border-gray-200">
                                  <div className="font-semibold text-gray-600 truncate">{item.url}</div>
                                  <div className={`mt-1 ${item.phone === result.phone_number ? 'text-green-600 font-bold' : 'text-gray-500'}`}>
                                    {item.phone}
                                    <span className="text-gray-400 font-normal ml-1">({item.method})</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

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
