import { useState } from 'react'

// --- SVG Icons Components (Inline for portability) ---
const SearchIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
)

const BuildingIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
  </svg>
)

const PhoneIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
  </svg>
)

const ChevronDown = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
  </svg>
)

function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [engine, setEngine] = useState('local')
  const [showDetails, setShowDetails] = useState(false)

  const production = false;
  const productionUrl = '13.50.100.103';

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query) return

    setLoading(true)
    setError(null)
    setResult(null)
    setShowDetails(false)

    try {
      const response = await fetch(`http://${production ? productionUrl : 'localhost'}:8000/search?query=${encodeURIComponent(query)}&engine=${encodeURIComponent(engine)}`)
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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col items-center justify-center p-4 font-sans text-slate-800">
      
      {/* Main Card Container */}
      <div className="w-full max-w-2xl bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-white/50 overflow-hidden transition-all duration-300">
        
        {/* Header Section */}
        <div className="p-8 md:p-10 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 mb-4 shadow-sm">
             <BuildingIcon className="w-6 h-6" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 mb-2">
            Trova Numero Ambulatorio
          </h1>
          <p className="text-slate-500 max-w-md mx-auto">
            Il motore di ricerca intelligente per trovare contatti medici e strutture sanitarie in pochi secondi.
          </p>
        </div>

        <div className="px-8 md:px-10 pb-10">
          {/* Search Form */}
          <form onSubmit={handleSearch} className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <SearchIcon className={`h-5 w-5 transition-colors ${loading ? 'text-indigo-500 animate-pulse' : 'text-slate-400 group-focus-within:text-indigo-500'}`} />
            </div>
            <input
              type="text"
              className="block w-full pl-11 pr-32 py-4 bg-slate-50 border border-slate-200 rounded-2xl leading-5 text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
              placeholder="Es. Cardiologia San Raffaele Milano..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading || !query}
              className="absolute right-2 top-2 bottom-2 px-6 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:hover:bg-indigo-600 transition-all shadow-md hover:shadow-lg focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </span>
              ) : 'Cerca'}
            </button>
          </form>

          {/* Engine Toggle (Segmented Control) */}
          <div className="mt-6 flex justify-center">
            <div className="bg-slate-100 p-1 rounded-xl inline-flex relative shadow-inner">
              <button
                onClick={() => setEngine('local')}
                className={`relative z-10 px-6 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                  engine === 'local' 
                    ? 'bg-white text-indigo-600 shadow-sm ring-1 ring-black/5' 
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                Ricerca Locale
              </button>
              <button
                onClick={() => setEngine('deepsearch')}
                className={`relative z-10 px-6 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                  engine === 'deepsearch' 
                    ? 'bg-white text-indigo-600 shadow-sm ring-1 ring-black/5' 
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                AI DeepSearch
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-6 p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm text-center animate-fadeIn">
              {error}
            </div>
          )}

          {/* Results Section */}
          {result && (
            <div className="mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* Off-Topic Result */}
              {result.phone_number === 'Off-Topic' ? (
                <div className="p-6 rounded-2xl bg-amber-50 border border-amber-100 text-center">
                  <div className="text-amber-600 font-semibold mb-1">Richiesta Fuori Contesto</div>
                  <p className="text-sm text-amber-700">Per favore, inserisci una ricerca relativa a medici o strutture sanitarie.</p>
                </div>
              ) : result.phone_number === 'Not Found' ? (
                 <div className="p-6 rounded-2xl bg-slate-50 border border-slate-100 text-center">
                  <div className="text-slate-600 font-semibold mb-1">Nessun risultato trovato</div>
                  <p className="text-sm text-slate-500">Abbiamo provato con Google e AI ma non abbiamo trovato un numero diretto.</p>
                </div>
              ) : (
                /* Success Result */
                <div className="bg-white rounded-2xl border border-slate-100 shadow-lg shadow-indigo-500/5 overflow-hidden">
                  
                  {/* Main Header */}
                  <div className="bg-gradient-to-r from-indigo-600 to-indigo-500 p-6 text-white">
                    <div className="text-indigo-100 text-xs font-semibold uppercase tracking-wider mb-1">Ambulatorio Trovato</div>
                    <h2 className="text-xl font-bold truncate">{result.query}</h2>
                  </div>

                  {/* Main Phone Display */}
                  <div className="p-6">
                    <div className="flex items-center gap-4 mb-6">
                      <div className="flex-shrink-0 w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center">
                        <PhoneIcon className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="text-sm text-slate-500">Numero di Telefono</div>
                        <div className="text-2xl font-bold text-slate-800 tracking-tight">{result.phone_number}</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm border-t border-slate-100 pt-4">
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400">Fonte:</span>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          result.source.includes('OpenAI') ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                        }`}>
                          {result.source}
                        </span>
                      </div>
                    </div>
                    
                    {/* Details Dropdown */}
                    {result.details && result.details.length > 0 && (
                      <div className="mt-4">
                        <button
                          onClick={() => setShowDetails(!showDetails)}
                          className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-slate-100 transition-colors text-sm text-slate-600 group"
                        >
                          <span>Mostra dettagli sorgente</span>
                          <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showDetails ? 'rotate-180' : ''}`} />
                        </button>

                        <div className={`overflow-hidden transition-all duration-300 ease-in-out ${showDetails ? 'max-h-96 opacity-100 mt-2' : 'max-h-0 opacity-0'}`}>
                          <div className="space-y-2 pl-1 pr-1 pb-1">
                            {result.details.map((item, index) => (
                              <div key={index} className="p-3 bg-white border border-slate-200 rounded-lg text-xs shadow-sm">
                                <div className="font-medium text-slate-700 truncate mb-1">{item.url}</div>
                                <div className="flex items-center justify-between">
                                   <span className={`${item.phone === result.phone_number ? 'text-green-600 font-bold' : 'text-slate-400'}`}>
                                     {item.phone}
                                   </span>
                                   <span className="text-slate-400 bg-slate-100 px-2 py-0.5 rounded">{item.method}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Footer / Disclaimer */}
      <p className="mt-6 text-xs text-slate-400 text-center max-w-sm">
        Nota: Questo strumento è limitato al contesto medico. I risultati sono generati automaticamente e vanno verificati.
      </p>
    </div>
  )
}

export default App