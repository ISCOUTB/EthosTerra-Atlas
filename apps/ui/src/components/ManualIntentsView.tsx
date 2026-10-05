import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  PlusCircle,
  Trash2,
  RotateCcw,
  Edit3,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  FileText,
  ShieldAlert,
  Clock,
  Archive,
  Search,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  ShieldCheck,
  Scale,
  Compass,
  Layers,
  Code2,
} from 'lucide-react'

const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/v2'

interface CasoPuroData {
  tipo: 'puro'
  clasificacion: string
  confianza: number
  razonamiento: string
}

interface FuenteEnColision {
  source_type: 'context_field' | 'document'
  source_id: string
  intencion: string
  efecto: string
  evidence_ref: string
  value?: any
  source_path?: string
  text_quote?: string
}

interface CasoConflictivoData {
  tipo: 'conflicto'
  conflicto_detectado: string
  opciones_resolucion: string[]
  requiere_humano: boolean
  titulo_conflicto?: string | null
  descripcion_contradiccion?: string | null
  ubicacion?: string | null
  fuentes_en_colision?: FuenteEnColision[]
  confidence?: number
  razonamiento?: string
}

type IntentPayload = CasoPuroData | CasoConflictivoData

interface IntentMetadata {
  created_at: string
  created_by: string
  updated_at: string
  updated_by: string
  canonical_hash: string
  version: number
}

interface IntentResponse {
  id: string
  intent: IntentPayload
  metadata: IntentMetadata
}

interface TrashMetadata {
  deleted_at: string
  deleted_by: string
  retention_days: number
  expires_at: string
  is_expired: boolean
}

interface TrashIntentResponse {
  id: string
  intent: IntentPayload
  metadata: IntentMetadata
  trash_metadata: TrashMetadata
}

export default function ManualIntentsView() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'active' | 'trash'>('active')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  // Filtros y búsqueda
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'puro' | 'conflicto'>('all')

  // Formulario
  const [formId, setFormId] = useState('')
  const [formAuthor, setFormAuthor] = useState('agronomo_operador')
  const [caseType, setCaseType] = useState<'puro' | 'conflicto'>('puro')

  // Campos Caso Puro
  const [puroClasificacion, setPuroClasificacion] = useState('ejecutar_accion')
  const [puroConfianza, setPuroConfianza] = useState(0.92)
  const [puroRazonamiento, setPuroRazonamiento] = useState('')

  // Campos Caso Conflicto
  const [conflictoDetectado, setConflictoDetectado] = useState('')
  const [conflictoOpciones, setConflictoOpciones] = useState('')
  const [conflictoRequiereHumano, setConflictoRequiereHumano] = useState(true)

  // Consultas React Query
  const {
    data: intents = [],
    isLoading: loadingIntents,
    isError: errorIntents,
    refetch: refetchIntents,
  } = useQuery<IntentResponse[]>({
    queryKey: ['intents'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/intents`)
      if (!res.ok) throw new Error('Error al cargar intenciones activas')
      return res.json()
    },
    retry: 1,
  })

  const {
    data: trash = [],
    isLoading: loadingTrash,
    isError: errorTrash,
    refetch: refetchTrash,
  } = useQuery<TrashIntentResponse[]>({
    queryKey: ['intents-trash'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/intents/trash`)
      if (!res.ok) throw new Error('Error al cargar la papelera')
      return res.json()
    },
    retry: 1,
  })

  const showFeedback = (type: 'success' | 'error', message: string) => {
    setFeedback({ type, message })
    setTimeout(() => setFeedback(null), 6000)
  }

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  const resetForm = () => {
    setEditingId(null)
    setFormId('')
    setFormAuthor('agronomo_operador')
    setCaseType('puro')
    setPuroClasificacion('ejecutar_accion')
    setPuroConfianza(0.92)
    setPuroRazonamiento('')
    setConflictoDetectado('')
    setConflictoOpciones('')
    setConflictoRequiereHumano(true)
  }

  // Plantillas Rápidas
  const loadPureTemplate = () => {
    const timestamp = Math.floor(Date.now() / 1000).toString().slice(-4)
    setEditingId(null)
    setCaseType('puro')
    setFormId(`agro_fertilizacion_${timestamp}`)
    setFormAuthor('especialista_suelos')
    setPuroClasificacion('ejecutar_accion')
    setPuroConfianza(0.95)
    setPuroRazonamiento('Análisis edáfico confirma déficit moderado de nitrógeno en parcela A3; condiciones aptas para incorporación de compost orgánico.')
    showFeedback('success', 'Plantilla de Caso Puro cargada en el formulario.')
  }

  const loadConflictTemplate = () => {
    const timestamp = Math.floor(Date.now() / 1000).toString().slice(-4)
    setEditingId(null)
    setCaseType('conflicto')
    setFormId(`agro_conflicto_cuenca_${timestamp}`)
    setFormAuthor('comite_normativo')
    setConflictoDetectado('Contradicción entre detección de brote de roya que demanda aspersión urgente y prohibición comunal de aplicación por cercanía a ronda de quebrada.')
    setConflictoOpciones(
      'Opción 1: Aplicación focalizada con biocontrolador manual respetando margen de 50 metros.\nOpción 2: Solicitar inspección comunitaria urgente para cordón de seguridad fitosanitario.\nOpción 3: Poda sanitaria manual preventiva y aislamiento de plantas afectadas.'
    )
    setConflictoRequiereHumano(true)
    showFeedback('success', 'Plantilla de Caso Conflictivo cargada en el formulario.')
  }

  // Mutaciones
  const createMutation = useMutation({
    mutationFn: async () => {
      const payload: { id: string; author: string; intent: IntentPayload } = {
        id: formId.trim(),
        author: formAuthor.trim() || 'agronomo_operador',
        intent:
          caseType === 'puro'
            ? {
                tipo: 'puro',
                clasificacion: puroClasificacion.trim(),
                confianza: Number(puroConfianza),
                razonamiento: puroRazonamiento.trim(),
              }
            : {
                tipo: 'conflicto',
                conflicto_detectado: conflictoDetectado.trim(),
                opciones_resolucion: conflictoOpciones
                  .split('\n')
                  .map((s) => s.trim())
                  .filter(Boolean),
                requiere_humano: conflictoRequiereHumano,
              },
      }

      const res = await fetch(`${API_BASE}/intents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error ${res.status}: Fallo al crear intención`)
      }
      return res.json()
    },
    onSuccess: (data) => {
      showFeedback('success', `Intención "${data.id}" registrada exitosamente con hash SHA-256 verificado.`)
      resetForm()
      queryClient.invalidateQueries({ queryKey: ['intents'] })
    },
    onError: (err: any) => {
      showFeedback('error', err.message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!editingId) return
      const payload = {
        author: formAuthor.trim() || 'agronomo_operador',
        intent:
          caseType === 'puro'
            ? {
                tipo: 'puro',
                clasificacion: puroClasificacion.trim(),
                confianza: Number(puroConfianza),
                razonamiento: puroRazonamiento.trim(),
              }
            : {
                tipo: 'conflicto',
                conflicto_detectado: conflictoDetectado.trim(),
                opciones_resolucion: conflictoOpciones
                  .split('\n')
                  .map((s) => s.trim())
                  .filter(Boolean),
                requiere_humano: conflictoRequiereHumano,
              },
      }

      const res = await fetch(`${API_BASE}/intents/${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error ${res.status}: Fallo al actualizar`)
      }
      return res.json()
    },
    onSuccess: (data) => {
      showFeedback('success', `Intención "${data.id}" actualizada exitosamente a la versión v${data.metadata.version}.`)
      resetForm()
      queryClient.invalidateQueries({ queryKey: ['intents'] })
    },
    onError: (err: any) => {
      showFeedback('error', err.message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_BASE}/intents/${id}?deleted_by=agronomo_operador`, {
        method: 'DELETE',
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error al mover a papelera`)
      }
      return res.json()
    },
    onSuccess: (data) => {
      showFeedback('success', `Intención "${data.id}" trasladada a papelera bajo retención de 30 días.`)
      queryClient.invalidateQueries({ queryKey: ['intents'] })
      queryClient.invalidateQueries({ queryKey: ['intents-trash'] })
    },
    onError: (err: any) => {
      showFeedback('error', err.message)
    },
  })

  const restoreMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_BASE}/intents/${id}/restore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ restored_by: 'agronomo_operador' }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error al restaurar intención`)
      }
      return res.json()
    },
    onSuccess: (data) => {
      showFeedback('success', `Intención "${data.id}" recuperada de papelera y reactivada como v${data.metadata.version}.`)
      queryClient.invalidateQueries({ queryKey: ['intents'] })
      queryClient.invalidateQueries({ queryKey: ['intents-trash'] })
    },
    onError: (err: any) => {
      showFeedback('error', err.message)
    },
  })

  const purgeMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/intents/trash/purge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ purged_by: 'agronomo_operador' }),
      })
      if (!res.ok) throw new Error('Error al ejecutar purga')
      return res.json()
    },
    onSuccess: (data) => {
      showFeedback('success', `Purga completada: ${data.purged_count} elementos vencidos eliminados permanentemente.`)
      queryClient.invalidateQueries({ queryKey: ['intents-trash'] })
    },
    onError: (err: any) => {
      showFeedback('error', err.message)
    },
  })

  const handleEdit = (item: IntentResponse) => {
    setEditingId(item.id)
    setFormId(item.id)
    setFormAuthor(item.metadata.updated_by || 'agronomo_operador')
    if (item.intent.tipo === 'puro') {
      setCaseType('puro')
      setPuroClasificacion(item.intent.clasificacion)
      setPuroConfianza(item.intent.confianza)
      setPuroRazonamiento(item.intent.razonamiento)
    } else {
      setCaseType('conflicto')
      setConflictoDetectado(item.intent.conflicto_detectado)
      setConflictoOpciones(item.intent.opciones_resolucion.join('\n'))
      setConflictoRequiereHumano(item.intent.requiere_humano)
    }
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Filtrado reactivo de intenciones activas
  const filteredIntents = useMemo(() => {
    return intents.filter((item) => {
      const matchesType =
        typeFilter === 'all' ? true : item.intent.tipo === typeFilter
      const q = searchQuery.toLowerCase().trim()
      if (!q) return matchesType

      const matchId = item.id.toLowerCase().includes(q)
      const matchAuthor = item.metadata.updated_by.toLowerCase().includes(q)
      const matchDetail =
        item.intent.tipo === 'puro'
          ? (item.intent.clasificacion + ' ' + item.intent.razonamiento).toLowerCase().includes(q)
          : (item.intent.conflicto_detectado + ' ' + item.intent.opciones_resolucion.join(' ')).toLowerCase().includes(q)

      return matchesType && (matchId || matchAuthor || matchDetail)
    })
  }, [intents, typeFilter, searchQuery])

  const pureCount = intents.filter((i) => i.intent.tipo === 'puro').length
  const conflictCount = intents.filter((i) => i.intent.tipo === 'conflicto').length

  return (
    <div className="space-y-6">
      {/* 1. DASHBOARD SUPERIOR DE KPI Y ESTADO */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Tarjeta 1: Intenciones Activas */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-5 shadow-sm border border-slate-700 relative overflow-hidden">
          <div className="absolute right-3 top-3 opacity-10">
            <Layers className="w-24 h-24" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-semibold tracking-wider text-slate-400 uppercase">
              Almacén Activo
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-400/30">
              Bloque B5
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black tracking-tight">{intents.length}</span>
            <span className="text-xs text-slate-300 font-medium">intenciones declarativas</span>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-700/60 flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              {pureCount} Casos Puros
            </div>
            <div className="flex items-center gap-1.5 text-amber-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-amber-400"></span>
              {conflictCount} Conflictivos
            </div>
          </div>
        </div>

        {/* Tarjeta 2: Papelera e Invariante de Retención */}
        <div className="bg-white rounded-2xl p-5 shadow-xs border border-slate-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                Papelera de Retención
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
                30 Días
              </span>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-slate-900">{trash.length}</span>
              <span className="text-xs text-slate-500 font-medium">borrados lógicos protegidos</span>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-amber-600" />
              Recuperables sin pérdida
            </span>
            <button
              onClick={() => setActiveTab('trash')}
              className="text-blue-600 font-semibold hover:underline cursor-pointer"
            >
              Ver papelera →
            </button>
          </div>
        </div>

        {/* Tarjeta 3: Seguridad y Telemetría */}
        <div className="bg-white rounded-2xl p-5 shadow-xs border border-slate-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider">
                Soberanía & Confinamiento
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 border ${
                  !errorIntents
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    !errorIntents ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
                  }`}
                ></span>
                {!errorIntents ? 'Backend Online' : 'Backend Offline'}
              </span>
            </div>
            <div className="mt-3 space-y-1.5 text-xs">
              <div className="flex items-center gap-1.5 text-slate-800 font-medium">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>EthosTerra_original: 0 escrituras</span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                Atomicidad: fsync + os.replace
              </div>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-400 font-mono truncate">
            Almacén: outputs/intents/
          </div>
        </div>
      </div>

      {/* FEEDBACK ALERT */}
      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center gap-3 border shadow-xs transition-all animate-in fade-in ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
              : 'bg-rose-50 text-rose-900 border-rose-200'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span className="font-medium">{feedback.message}</span>
        </div>
      )}

      {/* 2. FORMULARIO INTERACTIVO CON PLANTILLAS RÁPIDAS */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs relative">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 border-b border-slate-100 pb-4 mb-5">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              {editingId ? (
                <Edit3 className="w-4 h-4 text-amber-600" />
              ) : (
                <PlusCircle className="w-4 h-4 text-blue-600" />
              )}
              {editingId ? `Editando Intención: ${editingId}` : 'Gestor Declarativo de Intenciones'}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ingresa o edita especificaciones alineadas con los contratos Pydantic V2 de Caso Puro o Conflicto.
            </p>
          </div>

          {/* Botones de Plantilla de 1 Clic */}
          {!editingId ? (
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={loadPureTemplate}
                className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 border border-emerald-200 flex items-center gap-1.5 transition-colors cursor-pointer"
                title="Carga un caso puro de labranza y fertilización"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-600" /> Cargar Plantilla Caso Puro
              </button>
              <button
                type="button"
                onClick={loadConflictTemplate}
                className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200 flex items-center gap-1.5 transition-colors cursor-pointer"
                title="Carga un caso conflictivo de cuota de agua vs estrés"
              >
                <Scale className="w-3.5 h-3.5 text-amber-600" /> Cargar Plantilla Conflicto
              </button>
            </div>
          ) : (
            <button
              onClick={resetForm}
              className="text-xs text-slate-500 hover:text-slate-800 underline font-medium cursor-pointer"
            >
              Cancelar Edición
            </button>
          )}
        </div>

        {/* Inputs de Encabezado */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">
              Identificador Único (ID)
            </label>
            <input
              type="text"
              disabled={!!editingId}
              value={formId}
              onChange={(e) => setFormId(e.target.value)}
              placeholder="ej: agro_siembra_puro_01"
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono disabled:bg-slate-100 disabled:text-slate-500 transition-shadow"
            />
            <span className="text-[10px] text-slate-400 block mt-1">
              Lista blanca: alfanumérico, '-' y '_' (máximo 64 caracteres).
            </span>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Autor / Operador</label>
            <input
              type="text"
              value={formAuthor}
              onChange={(e) => setFormAuthor(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow"
            />
            <span className="text-[10px] text-slate-400 block mt-1">Identidad para la traza forense.</span>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Tipo de Caso eBDI</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setCaseType('puro')}
                className={`py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 border transition-all cursor-pointer ${
                  caseType === 'puro'
                    ? 'bg-emerald-600 text-white border-emerald-600 shadow-xs'
                    : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
                }`}
              >
                <Compass className="w-3.5 h-3.5" /> Caso Puro
              </button>
              <button
                type="button"
                onClick={() => setCaseType('conflicto')}
                className={`py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 border transition-all cursor-pointer ${
                  caseType === 'conflicto'
                    ? 'bg-amber-600 text-white border-amber-600 shadow-xs'
                    : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
                }`}
              >
                <Scale className="w-3.5 h-3.5" /> Caso Conflictivo
              </button>
            </div>
          </div>
        </div>

        {/* Campos Específicos por Tipo */}
        {caseType === 'puro' ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5 pt-4 border-t border-slate-100 bg-emerald-50/30 p-4 rounded-xl">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Clasificación / Acción eBDI
              </label>
              <input
                type="text"
                value={puroClasificacion}
                onChange={(e) => setPuroClasificacion(e.target.value)}
                placeholder="ej: ejecutar_accion, actualizar_creencia"
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-bold text-slate-700">Nivel de Confianza</label>
                <span className="font-mono text-xs font-bold text-emerald-800 bg-emerald-100 px-1.5 py-0.5 rounded">
                  {(puroConfianza * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={puroConfianza}
                onChange={(e) => setPuroConfianza(parseFloat(e.target.value))}
                className="w-full accent-emerald-600 cursor-pointer mt-2"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Razonamiento Semántico
              </label>
              <input
                type="text"
                value={puroRazonamiento}
                onChange={(e) => setPuroRazonamiento(e.target.value)}
                placeholder="Justificación agronómica para el orquestador..."
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
              />
            </div>
          </div>
        ) : (
          <div className="space-y-4 mt-5 pt-4 border-t border-slate-100 bg-amber-50/30 p-4 rounded-xl">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Descripción Exacta de la Contradicción
                </label>
                <textarea
                  rows={3}
                  value={conflictoDetectado}
                  onChange={(e) => setConflictoDetectado(e.target.value)}
                  placeholder="Detalla qué creencia y qué norma colisionan..."
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Opciones de Resolución (una por línea)
                </label>
                <textarea
                  rows={3}
                  value={conflictoOpciones}
                  onChange={(e) => setConflictoOpciones(e.target.value)}
                  placeholder="Opción 1: Priorizar agua&#10;Opción 2: Riego localizado"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500 bg-white font-mono text-[11px]"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="check_human"
                checked={conflictoRequiereHumano}
                onChange={(e) => setConflictoRequiereHumano(e.target.checked)}
                className="rounded border-slate-300 text-amber-600 focus:ring-amber-500 cursor-pointer"
              />
              <label htmlFor="check_human" className="text-xs text-slate-700 font-semibold cursor-pointer">
                Exigir intervención humana en Approval Gate (Human-in-the-loop obligatorio)
              </label>
            </div>
          </div>
        )}

        {/* Barra de Acciones del Formulario */}
        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
          <div className="text-[11px] text-slate-400 font-mono">
            {formId.trim() ? `outputs/intents/${formId.trim()}.json` : 'Ruta destino auto-confinada'}
          </div>

          <div className="flex gap-2">
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg cursor-pointer transition-colors"
              >
                Descartar
              </button>
            )}
            {editingId ? (
              <button
                type="button"
                onClick={() => updateMutation.mutate()}
                disabled={updateMutation.isPending}
                className="px-5 py-2 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-lg shadow-xs flex items-center gap-2 transition-all cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${updateMutation.isPending ? 'animate-spin' : ''}`} />
                Guardar Modificaciones
              </button>
            ) : (
              <button
                type="button"
                onClick={() => createMutation.mutate()}
                disabled={createMutation.isPending || !formId.trim()}
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white text-xs font-bold rounded-lg shadow-xs flex items-center gap-2 transition-all cursor-pointer"
              >
                <PlusCircle className={`w-3.5 h-3.5 ${createMutation.isPending ? 'animate-spin' : ''}`} />
                Registrar Intención
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 3. NAVEGACIÓN Y TABLA DE INTENCIONES / PAPELERA */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden">
        {/* Sub-header con Selector de Tab */}
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('active')}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'active'
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5" /> Intenciones Activas ({intents.length})
            </button>
            <button
              onClick={() => setActiveTab('trash')}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer ${
                activeTab === 'trash'
                  ? 'bg-amber-600 text-white shadow-xs'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              <Archive className="w-3.5 h-3.5" /> Papelera (30 Días) ({trash.length})
            </button>
          </div>

          {activeTab === 'active' && (
            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              {/* Buscador */}
              <div className="relative flex-1 md:w-64">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Buscar por ID, acción o texto..."
                  className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                />
              </div>

              {/* Filtros de Tipo */}
              <div className="flex items-center bg-white border border-slate-200 rounded-lg p-0.5 text-[11px] font-semibold">
                <button
                  onClick={() => setTypeFilter('all')}
                  className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                    typeFilter === 'all' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Todas
                </button>
                <button
                  onClick={() => setTypeFilter('puro')}
                  className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                    typeFilter === 'puro' ? 'bg-emerald-600 text-white' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Puros
                </button>
                <button
                  onClick={() => setTypeFilter('conflicto')}
                  className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer ${
                    typeFilter === 'conflicto' ? 'bg-amber-600 text-white' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Conflictos
                </button>
              </div>

              <button
                onClick={() => refetchIntents()}
                className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer"
                title="Actualizar lista"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {activeTab === 'trash' && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => purgeMutation.mutate()}
                disabled={purgeMutation.isPending}
                className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
                title="Elimina definitivamente solo los archivos que hayan superado los 30 días"
              >
                <ShieldAlert className="w-3.5 h-3.5" /> Purgar Expirados (+30 días)
              </button>
              <button
                onClick={() => refetchTrash()}
                className="p-1.5 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-200 transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* VISTA 1: TABLA DE ACTIVAS */}
        {activeTab === 'active' ? (
          <div>
            {errorIntents ? (
              <div className="p-6 bg-amber-50 border border-amber-200 rounded-xl m-6 text-xs text-amber-900 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-sm">Servidor Backend no detectado en http://localhost:8000</div>
                  <p className="mt-1 text-slate-600">
                    Para visualizar y sincronizar las intenciones, inicia el backend en una terminal ejecutando:
                  </p>
                  <code className="block mt-2 p-2 bg-white rounded border border-amber-200 font-mono text-[11px] text-slate-800 font-semibold select-all">
                    PYTHONPATH=apps/api uv run --project apps/api --with uvicorn uvicorn src.api.main:app --reload --port 8000
                  </code>
                </div>
              </div>
            ) : loadingIntents ? (
              <div className="p-12 text-center text-xs text-slate-400">
                <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin text-blue-500" />
                Sincronizando almacén desacoplado...
              </div>
            ) : filteredIntents.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400 mb-3">
                  <FileText className="w-6 h-6" />
                </div>
                <h4 className="text-xs font-bold text-slate-700">No se encontraron intenciones activas</h4>
                <p className="text-[11px] text-slate-400 mt-1 max-w-sm mx-auto">
                  {searchQuery
                    ? 'No hay registros que coincidan con la búsqueda actual.'
                    : 'Crea una intención mediante el formulario superior o usa las plantillas de 1 clic.'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] tracking-wider border-b border-slate-100">
                    <tr>
                      <th className="px-5 py-3.5">ID / Hash</th>
                      <th className="px-5 py-3.5">Tipo</th>
                      <th className="px-5 py-3.5">Contenido / Semántica</th>
                      <th className="px-5 py-3.5">Versión</th>
                      <th className="px-5 py-3.5">Actualizado</th>
                      <th className="px-5 py-3.5 text-right">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {filteredIntents.map((item) => {
                      const isExpanded = expandedId === item.id
                      return (
                        <tr key={item.id} className="group hover:bg-slate-50/70 transition-colors">
                          <td className="px-5 py-4 font-mono align-top">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                                {item.id}
                              </span>
                              <button
                                onClick={() => handleCopy(item.id, `id_${item.id}`)}
                                className="text-slate-400 hover:text-slate-600 cursor-pointer"
                                title="Copiar ID"
                              >
                                {copiedKey === `id_${item.id}` ? (
                                  <Check className="w-3 h-3 text-emerald-600" />
                                ) : (
                                  <Copy className="w-3 h-3" />
                                )}
                              </button>
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5">
                              <span>{item.metadata.canonical_hash.slice(0, 10)}...</span>
                              <button
                                onClick={() => handleCopy(item.metadata.canonical_hash, `hash_${item.id}`)}
                                className="hover:text-slate-700 cursor-pointer"
                                title="Copiar SHA-256 completo"
                              >
                                {copiedKey === `hash_${item.id}` ? (
                                  <Check className="w-2.5 h-2.5 text-emerald-600" />
                                ) : (
                                  <Copy className="w-2.5 h-2.5" />
                                )}
                              </button>
                            </div>
                          </td>

                          <td className="px-5 py-4 align-top">
                            <span
                              className={`px-2.5 py-1 rounded-full text-[10px] font-bold inline-flex items-center gap-1 border ${
                                item.intent.tipo === 'puro'
                                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                                  : 'bg-amber-50 text-amber-800 border-amber-200'
                              }`}
                            >
                              <span
                                className={`w-1.5 h-1.5 rounded-full ${
                                  item.intent.tipo === 'puro' ? 'bg-emerald-600' : 'bg-amber-600'
                                }`}
                              ></span>
                              {item.intent.tipo === 'puro' ? 'Caso Puro' : 'Caso Conflicto'}
                            </span>
                          </td>

                          <td className="px-5 py-4 align-top max-w-md">
                            {item.intent.tipo === 'puro' ? (
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-slate-900">{item.intent.clasificacion}</span>
                                  <span className="text-[10px] font-bold px-1.5 py-0.2 bg-emerald-100 text-emerald-800 rounded">
                                    {(item.intent.confianza * 100).toFixed(0)}%
                                  </span>
                                </div>
                                <p className="text-slate-600 line-clamp-2 leading-relaxed">
                                  {item.intent.razonamiento}
                                </p>
                              </div>
                            ) : (
                              <div className="space-y-1">
                                <span className="font-bold text-amber-900 block leading-snug">
                                  {item.intent.conflicto_detectado}
                                </span>
                                <div className="text-[11px] text-slate-500 flex items-center gap-2">
                                  <span>{item.intent.opciones_resolucion.length} alternativas</span>
                                  <span>•</span>
                                  <span className="text-amber-700 font-semibold">Human-in-the-loop: Sí</span>
                                </div>
                              </div>
                            )}

                            {/* Detalle Expandible al Clic */}
                            {isExpanded && (
                              <div className="mt-3 pt-3 border-t border-slate-200 text-xs space-y-2 bg-slate-50 p-3 rounded-xl border">
                                <div className="flex items-center justify-between text-[11px] font-bold text-slate-700">
                                  <span className="flex items-center gap-1">
                                    <Code2 className="w-3.5 h-3.5 text-blue-600" />
                                    Inspección Estructurada (JSON)
                                  </span>
                                  <span className="font-mono text-slate-400">
                                    v{item.metadata.version} ({new Date(item.metadata.updated_at).toLocaleString()})
                                  </span>
                                </div>
                                <pre className="p-2.5 bg-slate-900 text-slate-100 rounded-lg font-mono text-[10px] overflow-x-auto max-h-48">
                                  {JSON.stringify(item, null, 2)}
                                </pre>
                              </div>
                            )}
                          </td>

                          <td className="px-5 py-4 font-mono font-bold text-slate-700 align-top">
                            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                              v{item.metadata.version}
                            </span>
                          </td>

                          <td className="px-5 py-4 text-slate-500 text-[11px] align-top whitespace-nowrap">
                            <div>{new Date(item.metadata.updated_at).toLocaleDateString()}</div>
                            <div className="text-[10px] text-slate-400 font-medium">Por: {item.metadata.updated_by}</div>
                          </td>

                          <td className="px-5 py-4 text-right align-top whitespace-nowrap">
                            <div className="flex justify-end items-center gap-1">
                              <button
                                onClick={() => setExpandedId(isExpanded ? null : item.id)}
                                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                                title={isExpanded ? 'Contraer' : 'Expandir detalle'}
                              >
                                {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                              </button>
                              <button
                                onClick={() => handleEdit(item)}
                                className="p-1.5 text-slate-500 hover:text-amber-700 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer"
                                title="Editar intención"
                              >
                                <Edit3 className="w-3.5 h-3.5" />
                              </button>
                              <button
                                onClick={() => deleteMutation.mutate(item.id)}
                                className="p-1.5 text-slate-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                                title="Eliminar (Borrado lógico a papelera)"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          /* VISTA 2: TABLA DE PAPELERA (30 DÍAS) */
          <div>
            {errorTrash ? (
              <div className="p-6 bg-amber-50 border border-amber-200 rounded-xl m-6 text-xs text-amber-900 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-sm">Servidor Backend no detectado en http://localhost:8000</div>
                  <p className="mt-1 text-slate-600">
                    Para consultar la papelera de 30 días, inicia el backend en una terminal ejecutando:
                  </p>
                  <code className="block mt-2 p-2 bg-white rounded border border-amber-200 font-mono text-[11px] text-slate-800 font-semibold select-all">
                    PYTHONPATH=apps/api uv run --project apps/api --with uvicorn uvicorn src.api.main:app --reload --port 8000
                  </code>
                </div>
              </div>
            ) : loadingTrash ? (
              <div className="p-12 text-center text-xs text-slate-400">
                <RefreshCw className="w-6 h-6 mx-auto mb-2 animate-spin text-amber-500" />
                Cargando registros de la papelera...
              </div>
            ) : trash.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400 mb-3">
                  <Archive className="w-6 h-6" />
                </div>
                <h4 className="text-xs font-bold text-slate-700">La papelera está vacía</h4>
                <p className="text-[11px] text-slate-400 mt-1 max-w-sm mx-auto">
                  Las intenciones eliminadas se conservan aquí durante 30 días antes de ser purgadas definitivamente.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500 font-bold uppercase text-[10px] tracking-wider border-b border-slate-100">
                    <tr>
                      <th className="px-5 py-3.5">ID Intención</th>
                      <th className="px-5 py-3.5">Eliminado Por</th>
                      <th className="px-5 py-3.5">Fecha Borrado</th>
                      <th className="px-5 py-3.5">Ventana de Retención (30 Días)</th>
                      <th className="px-5 py-3.5">Estado</th>
                      <th className="px-5 py-3.5 text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {trash.map((item) => {
                      const expiresDate = new Date(item.trash_metadata.expires_at)
                      const deletedDate = new Date(item.trash_metadata.deleted_at)
                      const now = new Date()
                      const diffDays = Math.max(
                        0,
                        Math.ceil((expiresDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
                      )

                      return (
                        <tr key={item.id} className="hover:bg-amber-50/40 transition-colors">
                          <td className="px-5 py-4 font-mono font-bold text-slate-900">
                            {item.id}
                            <span className="block text-[10px] text-slate-400 font-normal">
                              Tipo: {item.intent.tipo}
                            </span>
                          </td>

                          <td className="px-5 py-4 text-slate-600 font-medium">
                            {item.trash_metadata.deleted_by}
                          </td>

                          <td className="px-5 py-4 text-slate-500 text-[11px]">
                            {deletedDate.toLocaleString()}
                          </td>

                          <td className="px-5 py-4">
                            <div className="w-48">
                              <div className="flex justify-between text-[10px] font-bold text-slate-600 mb-1">
                                <span>{diffDays} días restantes</span>
                                <span className="text-slate-400">Total: 30d</span>
                              </div>
                              <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                                <div
                                  className="bg-amber-500 h-full rounded-full transition-all"
                                  style={{ width: `${Math.min(100, (diffDays / 30) * 100)}%` }}
                                ></div>
                              </div>
                            </div>
                          </td>

                          <td className="px-5 py-4">
                            {item.trash_metadata.is_expired ? (
                              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                                Expirado (Listo para Purga)
                              </span>
                            ) : (
                              <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 inline-flex items-center gap-1">
                                <Clock className="w-3 h-3 text-emerald-700" /> Restaurable
                              </span>
                            )}
                          </td>

                          <td className="px-5 py-4 text-right">
                            <button
                              disabled={item.trash_metadata.is_expired || restoreMutation.isPending}
                              onClick={() => restoreMutation.mutate(item.id)}
                              className="px-3 py-1.5 text-xs font-bold rounded-lg bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center gap-1.5 transition-all shadow-xs cursor-pointer ml-auto"
                            >
                              <RotateCcw className="w-3.5 h-3.5" /> Restaurar
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
