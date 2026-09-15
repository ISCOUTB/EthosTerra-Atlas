import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Clasificador from './components/Clasificador'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <header className="bg-white border-b border-slate-200 px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold text-slate-800">eBDI-LLM Auditor</h1>
            <nav className="flex gap-4 ml-6">
              <a href="#" className="text-blue-600 font-medium">Clasificador</a>
              <a href="#" className="text-slate-500 hover:text-slate-700">Historial</a>
            </nav>
          </div>
          <div className="text-slate-400 text-sm flex items-center gap-2">
            ⚙️ Ajustes
          </div>
        </header>
        <main className="flex-1 max-w-7xl w-full mx-auto p-6">
          <Clasificador />
        </main>
      </div>
    </QueryClientProvider>
  )
}

export default App
