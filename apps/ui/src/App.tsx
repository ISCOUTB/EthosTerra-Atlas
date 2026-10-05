import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Clasificador from './components/Clasificador'
import DocumentPipelineView from './components/DocumentPipelineView'
import ManualIntentsView from './components/ManualIntentsView'
import { FileCode, Layers, ShieldCheck, BookmarkCheck } from 'lucide-react'

const queryClient = new QueryClient()

function App() {
  const [activeModule, setActiveModule] = useState<'pipeline' | 'intents' | 'legacy'>('intents')

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex justify-between items-center sticky top-0 z-50">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <span className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-black text-sm">
                eBDI
              </span>
              <div>
                <h1 className="text-base font-bold text-slate-900 leading-tight">
                  EthosTerra Knowledge Studio
                </h1>
                <p className="text-[11px] text-slate-500 font-mono">Semana 8 — CRUD Manual B5</p>
              </div>
            </div>

            <nav className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
              <button
                onClick={() => setActiveModule('intents')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-all ${
                  activeModule === 'intents'
                    ? 'bg-white text-blue-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <BookmarkCheck className="w-3.5 h-3.5" />
                Intenciones Manuales (B5)
              </button>
              <button
                onClick={() => setActiveModule('pipeline')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-all ${
                  activeModule === 'pipeline'
                    ? 'bg-white text-blue-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <FileCode className="w-3.5 h-3.5" />
                Pipeline Documental eBDI
              </button>
              <button
                onClick={() => setActiveModule('legacy')}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold flex items-center gap-2 transition-all ${
                  activeModule === 'legacy'
                    ? 'bg-white text-blue-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                Clasificador Legacy (Semana 5)
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" /> Offline-First DMR
            </span>
          </div>
        </header>

        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          {activeModule === 'intents' ? (
            <ManualIntentsView />
          ) : activeModule === 'pipeline' ? (
            <DocumentPipelineView />
          ) : (
            <Clasificador />
          )}
        </main>
      </div>
    </QueryClientProvider>
  )
}


export default App
