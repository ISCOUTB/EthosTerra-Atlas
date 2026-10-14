import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Clasificador from './components/Clasificador'
import DocumentPipelineView from './components/DocumentPipelineView'
import ManualIntentsView from './components/ManualIntentsView'
import AtlasView from './components/AtlasView'
import { GlobalNav } from './components/layout/GlobalNav'
import { SubNav, type NavItem } from './components/layout/SubNav'
import { Tile } from './components/ui/Tile'
import { FileCode, Layers, BookmarkCheck, Compass } from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { LoginView } from './components/auth/LoginView'

const queryClient = new QueryClient()

type ModuleId = 'atlas' | 'intents' | 'pipeline' | 'legacy'

const modules: NavItem<ModuleId>[] = [
  { id: 'atlas', label: 'Atlas Territorial (AT-1)', icon: Compass },
  { id: 'intents', label: 'Intenciones Manuales (B5)', icon: BookmarkCheck },
  { id: 'pipeline', label: 'Pipeline Documental eBDI', icon: FileCode },
  { id: 'legacy', label: 'Clasificador Legacy (Semana 5)', icon: Layers },
]

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth()
  const [activeModule, setActiveModule] = useState<ModuleId>('atlas')

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f7f5f0] text-sm text-[#66635b]">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full border-2 border-[#0066cc] border-t-transparent animate-spin" />
          <span>Verificando estado de seguridad soberana...</span>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginView />
  }

  return (
    <div className="flex min-h-screen flex-col bg-parchment">
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-100 focus:rounded-lg focus:bg-canvas focus:px-4 focus:py-2"
      >
        Saltar al contenido
      </a>
      <header className="sticky top-0 z-50">
        <GlobalNav />
        <SubNav items={modules} active={activeModule} onSelect={setActiveModule} />
      </header>

      <main id="contenido" className="flex-1">
        <Tile tone="parchment">
          {activeModule === 'atlas' ? (
            <AtlasView />
          ) : activeModule === 'intents' ? (
            <ManualIntentsView />
          ) : activeModule === 'pipeline' ? (
            <DocumentPipelineView />
          ) : (
            <Clasificador />
          )}
        </Tile>
      </main>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
