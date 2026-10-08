import { useState, useMemo, useEffect } from 'react'
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
  Code2,
  ArrowLeft,
} from 'lucide-react'

const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/v2'

// -----------------------------------------------------------------------------
// CONTRATOS Y TIPOS FORMALES PYDANTIC V2 (BLOQUE B5)
// -----------------------------------------------------------------------------

export interface HumanReviewData {
  status: 'pendiente' | 'aprobado' | 'observado' | 'rechazado'
  reviewer: string
  reviewed_at: string | null
  comments: string
  decision_rationale: string
  requires_additional_review: boolean
}

export interface CasoPuroData {
  tipo: 'puro'
  clasificacion: string
  confianza: number
  razonamiento: string
}

export interface FuenteEnColision {
  source_type: 'context_field' | 'document'
  source_id: string
  intencion: string
  efecto: string
  evidence_ref: string
  value?: unknown
  source_path?: string
  text_quote?: string
}

export interface CasoConflictivoData {
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

export type IntentPayload = CasoPuroData | CasoConflictivoData

export interface IntentMetadata {
  created_at: string
  created_by: string
  updated_at: string
  updated_by: string
  canonical_hash: string
  version: number
}

export interface IntentResponse {
  id: string
  intent: IntentPayload
  metadata: IntentMetadata
  human_review: HumanReviewData
}

export interface TrashMetadata {
  deleted_at: string
  deleted_by: string
  retention_days: number
  expires_at: string
  is_expired: boolean
}

export interface TrashIntentResponse {
  id: string
  intent: IntentPayload
  metadata: IntentMetadata
  trash_metadata: TrashMetadata
  human_review: HumanReviewData
}

interface IntentDraft {
  id: string
  author: string
  caseType: 'puro' | 'conflicto'
  clasificacion: string
  confianza: number
  razonamiento: string
  conflicto_detectado: string
  opciones_resolucion_text: string
  titulo_conflicto: string
  ubicacion: string
  requiere_humano: boolean
  review_status: 'pendiente' | 'aprobado' | 'observado' | 'rechazado'
  reviewer: string
  comments: string
  decision_rationale: string
  requires_additional_review: boolean
}

// -----------------------------------------------------------------------------
// UTILIDADES DETERMINISTAS Y CANÓNICAS
// -----------------------------------------------------------------------------

function canonicalStringify(obj: unknown): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj)
  }
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalStringify).join(',') + ']'
  }
  const record = obj as Record<string, unknown>
  const keys = Object.keys(record).sort()
  return '{' + keys.map((k) => JSON.stringify(k) + ':' + canonicalStringify(record[k])).join(',') + '}'
}

async function computeSha256(text: string): Promise<string> {
  if (typeof window !== 'undefined' && window.crypto?.subtle) {
    try {
      const encoder = new TextEncoder()
      const data = encoder.encode(text)
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', data)
      const hashArray = Array.from(new Uint8Array(hashBuffer))
      return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
    } catch {
      return 'sha256-error'
    }
  }
  return 'sha256-preview'
}

const DEFAULT_DRAFT: IntentDraft = {
  id: '',
  author: 'investigador_principal',
  caseType: 'puro',
  clasificacion: 'ejecutar_accion',
  confianza: 0.95,
  razonamiento: '',
  conflicto_detectado: '',
  opciones_resolucion_text: '',
  titulo_conflicto: '',
  ubicacion: 'parcela_a1',
  requiere_humano: true,
  review_status: 'pendiente',
  reviewer: 'investigador_principal',
  comments: '',
  decision_rationale: '',
  requires_additional_review: false,
}

// -----------------------------------------------------------------------------
// COMPONENTE PRINCIPAL: MANUAL INTENTS VIEW (BLOQUE B5)
// -----------------------------------------------------------------------------

export default function ManualIntentsView() {
  const queryClient = useQueryClient()

  // Navegación: 'inventory' | 'editor'
  const [viewMode, setViewMode] = useState<'inventory' | 'editor'>('inventory')
  const [activeTab, setActiveTab] = useState<'active' | 'trash'>('active')
  const [auditTab, setAuditTab] = useState<'diff' | 'json'>('diff')

  // Estado del borrador
  const [originalItem, setOriginalItem] = useState<IntentResponse | null>(null)
  const [draft, setDraft] = useState<IntentDraft>(DEFAULT_DRAFT)

  // Filtros de inventario
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<'all' | 'puro' | 'conflicto'>('all')

  // Telemetría local y estado de copiado
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [liveHash, setLiveHash] = useState<string>('')

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
      if (!res.ok) throw new Error('Error al consultar almacén de intenciones')
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
      if (!res.ok) throw new Error('Error al consultar papelera de retención')
      return res.json()
    },
    retry: 1,
  })

  const showFeedback = (type: 'success' | 'error', message: string) => {
    setFeedback({ type, message })
    setTimeout(() => setFeedback(null), 5000)
  }

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 1800)
  }

  // ---------------------------------------------------------------------------
  // CONSTRUCCIÓN DEL PAYLOAD SEMÁNTICO Y LIVE HASH ESTIMADO
  // ---------------------------------------------------------------------------

  const liveIntentPayload = useMemo(() => {
    if (draft.caseType === 'puro') {
      return {
        tipo: 'puro' as const,
        clasificacion: draft.clasificacion.trim(),
        confianza: Number(draft.confianza),
        razonamiento: draft.razonamiento.trim(),
      }
    } else {
      return {
        tipo: 'conflicto' as const,
        conflicto_detectado: draft.conflicto_detectado.trim(),
        opciones_resolucion: draft.opciones_resolucion_text
          .split('\n')
          .map((s) => s.trim())
          .filter(Boolean),
        requiere_humano: draft.requiere_humano,
        ...(draft.titulo_conflicto.trim() ? { titulo_conflicto: draft.titulo_conflicto.trim() } : {}),
        ...(draft.ubicacion.trim() ? { ubicacion: draft.ubicacion.trim() } : {}),
      }
    }
  }, [draft])

  const fullLiveRequestJson = useMemo(() => {
    return {
      ...(originalItem ? {} : { id: draft.id.trim() }),
      author: draft.author.trim() || 'investigador_principal',
      intent: liveIntentPayload,
      human_review: {
        status: draft.review_status,
        reviewer: draft.reviewer.trim() || 'investigador_principal',
        reviewed_at: new Date().toISOString(),
        comments: draft.comments.trim(),
        decision_rationale: draft.decision_rationale.trim(),
        requires_additional_review: draft.requires_additional_review,
      },
    }
  }, [originalItem, draft, liveIntentPayload])

  useEffect(() => {
    let isMounted = true
    computeSha256(canonicalStringify(liveIntentPayload)).then((h) => {
      if (isMounted) setLiveHash(h)
    })
    return () => {
      isMounted = false
    }
  }, [liveIntentPayload])

  // ---------------------------------------------------------------------------
  // MOTOR DE DIFF EN VIVO (ESTADO EN DISCO VS BORRADOR ACTUAL)
  // ---------------------------------------------------------------------------

  const diffItems = useMemo(() => {
    if (!originalItem) return []
    const diffs: { field: string; label: string; original: string; current: string }[] = []

    if (originalItem.metadata.updated_by !== draft.author) {
      diffs.push({
        field: 'author',
        label: 'Autor / Operador',
        original: originalItem.metadata.updated_by,
        current: draft.author,
      })
    }

    if (originalItem.intent.tipo !== draft.caseType) {
      diffs.push({
        field: 'tipo',
        label: 'Tipo de Caso',
        original: originalItem.intent.tipo === 'puro' ? 'Caso Puro' : 'Caso Conflictivo',
        current: draft.caseType === 'puro' ? 'Caso Puro' : 'Caso Conflictivo',
      })
    }

    if (draft.caseType === 'puro') {
      const origPuro = originalItem.intent.tipo === 'puro' ? (originalItem.intent as CasoPuroData) : null
      if (origPuro) {
        if (origPuro.clasificacion !== draft.clasificacion) {
          diffs.push({
            field: 'clasificacion',
            label: 'Clasificación',
            original: origPuro.clasificacion,
            current: draft.clasificacion,
          })
        }
        if (Math.abs(origPuro.confianza - draft.confianza) > 0.001) {
          diffs.push({
            field: 'confianza',
            label: 'Confianza',
            original: `${(origPuro.confianza * 100).toFixed(0)}%`,
            current: `${(draft.confianza * 100).toFixed(0)}%`,
          })
        }
        if (origPuro.razonamiento !== draft.razonamiento) {
          diffs.push({
            field: 'razonamiento',
            label: 'Razonamiento',
            original: origPuro.razonamiento || '(vacío)',
            current: draft.razonamiento || '(vacío)',
          })
        }
      }
    } else {
      const origConf = originalItem.intent.tipo === 'conflicto' ? (originalItem.intent as CasoConflictivoData) : null
      if (origConf) {
        if (origConf.conflicto_detectado !== draft.conflicto_detectado) {
          diffs.push({
            field: 'conflicto_detectado',
            label: 'Contradicción',
            original: origConf.conflicto_detectado,
            current: draft.conflicto_detectado,
          })
        }
        const origOps = origConf.opciones_resolucion.join('\n')
        if (origOps !== draft.opciones_resolucion_text.trim()) {
          diffs.push({
            field: 'opciones_resolucion',
            label: 'Opciones de Resolución',
            original: origConf.opciones_resolucion.join(' | ') || '(ninguna)',
            current: draft.opciones_resolucion_text.split('\n').filter(Boolean).join(' | ') || '(ninguna)',
          })
        }
        if (origConf.requiere_humano !== draft.requiere_humano) {
          diffs.push({
            field: 'requiere_humano',
            label: 'Intervención Humana (HITL)',
            original: origConf.requiere_humano ? 'Obligatorio' : 'Opcional',
            current: draft.requiere_humano ? 'Obligatorio' : 'Opcional',
          })
        }
        if ((origConf.titulo_conflicto || '') !== draft.titulo_conflicto) {
          diffs.push({
            field: 'titulo_conflicto',
            label: 'Título de Conflicto',
            original: origConf.titulo_conflicto || '(sin título)',
            current: draft.titulo_conflicto || '(sin título)',
          })
        }
        if ((origConf.ubicacion || '') !== draft.ubicacion) {
          diffs.push({
            field: 'ubicacion',
            label: 'Ubicación / Parcela',
            original: origConf.ubicacion || '(sin asignar)',
            current: draft.ubicacion || '(sin asignar)',
          })
        }
      }
    }

    // Revisión Humana Separada
    const origRev = originalItem.human_review || {
      status: 'pendiente',
      reviewer: 'investigador_principal',
      comments: '',
      decision_rationale: '',
      requires_additional_review: false,
    }

    if (origRev.status !== draft.review_status) {
      diffs.push({
        field: 'review_status',
        label: 'Dictamen de Revisión',
        original: origRev.status,
        current: draft.review_status,
      })
    }
    if (origRev.reviewer !== draft.reviewer) {
      diffs.push({
        field: 'reviewer',
        label: 'Evaluador Responsable',
        original: origRev.reviewer,
        current: draft.reviewer,
      })
    }
    if (origRev.decision_rationale !== draft.decision_rationale) {
      diffs.push({
        field: 'decision_rationale',
        label: 'Justificación de la Decisión',
        original: origRev.decision_rationale || '(ninguna)',
        current: draft.decision_rationale || '(ninguna)',
      })
    }
    if (origRev.comments !== draft.comments) {
      diffs.push({
        field: 'comments',
        label: 'Observaciones de Campo',
        original: origRev.comments || '(ninguna)',
        current: draft.comments || '(ninguna)',
      })
    }
    if (origRev.requires_additional_review !== draft.requires_additional_review) {
      diffs.push({
        field: 'requires_additional_review',
        label: 'Segunda Revisión Requerida',
        original: origRev.requires_additional_review ? 'Sí' : 'No',
        current: draft.requires_additional_review ? 'Sí' : 'No',
      })
    }

    return diffs
  }, [originalItem, draft])

  // ---------------------------------------------------------------------------
  // VALIDACIONES DE FORMULARIO E INTEGRIDAD METODOLÓGICA
  // ---------------------------------------------------------------------------

  const isValidId = useMemo(() => {
    if (originalItem) return true
    return /^[a-zA-Z0-9_-]{1,64}$/.test(draft.id.trim())
  }, [originalItem, draft.id])

  const isReviewComplete = useMemo(() => {
    if (draft.review_status === 'aprobado' || draft.review_status === 'rechazado') {
      return draft.reviewer.trim().length > 0 && draft.decision_rationale.trim().length > 0
    }
    return true
  }, [draft.review_status, draft.reviewer, draft.decision_rationale])

  const hasChanges = diffItems.length > 0


  // Prevención de salida accidental si hay cambios sin guardar
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasChanges])

  // ---------------------------------------------------------------------------
  // TRANSICIONES DE VISTA Y ACCIONES DE BORRADOR
  // ---------------------------------------------------------------------------

  const openEditorForEdit = (item: IntentResponse) => {
    setOriginalItem(item)
    const rev = item.human_review || {
      status: 'pendiente',
      reviewer: item.metadata.updated_by || 'investigador_principal',
      comments: '',
      decision_rationale: '',
      requires_additional_review: false,
    }

    if (item.intent.tipo === 'puro') {
      setDraft({
        id: item.id,
        author: item.metadata.updated_by || 'investigador_principal',
        caseType: 'puro',
        clasificacion: item.intent.clasificacion,
        confianza: item.intent.confianza,
        razonamiento: item.intent.razonamiento,
        conflicto_detectado: '',
        opciones_resolucion_text: '',
        titulo_conflicto: '',
        ubicacion: 'parcela_a1',
        requiere_humano: true,
        review_status: rev.status || 'pendiente',
        reviewer: rev.reviewer || item.metadata.updated_by || 'investigador_principal',
        comments: rev.comments || '',
        decision_rationale: rev.decision_rationale || '',
        requires_additional_review: rev.requires_additional_review || false,
      })
    } else {
      setDraft({
        id: item.id,
        author: item.metadata.updated_by || 'investigador_principal',
        caseType: 'conflicto',
        clasificacion: 'ejecutar_accion',
        confianza: 0.9,
        razonamiento: '',
        conflicto_detectado: item.intent.conflicto_detectado,
        opciones_resolucion_text: item.intent.opciones_resolucion.join('\n'),
        titulo_conflicto: item.intent.titulo_conflicto || '',
        ubicacion: item.intent.ubicacion || 'parcela_a1',
        requiere_humano: item.intent.requiere_humano,
        review_status: rev.status || 'pendiente',
        reviewer: rev.reviewer || item.metadata.updated_by || 'investigador_principal',
        comments: rev.comments || '',
        decision_rationale: rev.decision_rationale || '',
        requires_additional_review: rev.requires_additional_review || false,
      })
    }
    setViewMode('editor')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const openEditorForCreate = () => {
    setOriginalItem(null)
    setDraft({
      ...DEFAULT_DRAFT,
      id: `intent_${Date.now().toString().slice(-6)}`,
    })
    setViewMode('editor')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleReturnToInventory = () => {
    if (hasChanges) {
      const confirmDiscard = window.confirm(
        'Existen modificaciones locales sin persistir en la consola. ¿Deseas descartar los cambios y volver al inventario?'
      )
      if (!confirmDiscard) return
    }
    setViewMode('inventory')
    setOriginalItem(null)
  }

  const handleDiscardChanges = () => {
    if (originalItem) {
      openEditorForEdit(originalItem)
      showFeedback('success', 'Modificaciones descartadas. Borrador restaurado a la versión en disco.')
    } else {
      setDraft({
        ...DEFAULT_DRAFT,
        id: `intent_${Date.now().toString().slice(-6)}`,
      })
      showFeedback('success', 'Formulario reiniciado.')
    }
  }

  const loadPureTemplate = () => {
    setDraft((prev) => ({
      ...prev,
      caseType: 'puro',
      clasificacion: 'ejecutar_accion',
      confianza: 0.95,
      razonamiento:
        'Análisis edáfico confirma déficit moderado de nitrógeno en parcela A3; condiciones aptas para incorporación de compost orgánico.',
      review_status: 'aprobado',
      reviewer: 'investigador_principal',
      decision_rationale: 'Conforme a la rotación agronómica y plan de fertilización sustentable de EthosTerra.',
      comments: 'Dosis recomendada: 1.5 kg/m2 en banda localizada.',
    }))
    showFeedback('success', 'Plantilla de Caso Puro cargada.')
  }

  const loadConflictTemplate = () => {
    setDraft((prev) => ({
      ...prev,
      caseType: 'conflicto',
      conflicto_detectado:
        'Contradicción entre detección de brote de roya que demanda aspersión fitosanitaria y restricción comunal de aplicación por colindancia con ronda de quebrada.',
      opciones_resolucion_text:
        'Opción 1: Aplicación focalizada con biocontrolador manual respetando margen de 50 metros.\nOpción 2: Solicitar inspección comunitaria urgente para cordón de seguridad fitosanitario.\nOpción 3: Poda sanitaria manual preventiva y aislamiento de plantas afectadas.',
      requiere_humano: true,
      titulo_conflicto: 'Colisión Restricción Hídrica vs Fitopatología',
      ubicacion: 'parcela_a1',
      review_status: 'observado',
      reviewer: 'investigador_principal',
      decision_rationale: 'Riesgo ambiental de escorrentía requiere protocolo de deliberación comunitaria.',
      comments: 'Escalado para revisión en comité normativo veredal.',
    }))
    showFeedback('success', 'Plantilla de Caso Conflictivo cargada.')
  }

  // ---------------------------------------------------------------------------
  // MUTACIONES API (CRUD B5)
  // ---------------------------------------------------------------------------

  const createMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/intents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fullLiveRequestJson),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error ${res.status}: Fallo al crear la intención`)
      }
      return res.json()
    },
    onSuccess: (data: IntentResponse) => {
      showFeedback('success', `Intención "${data.id}" registrada exitosamente en outputs/intents/.`)
      queryClient.invalidateQueries({ queryKey: ['intents'] })
      openEditorForEdit(data)
    },
    onError: (err: Error) => {
      showFeedback('error', err.message)
    },
  })

  const updateMutation = useMutation({
    mutationFn: async () => {
      if (!originalItem) return
      const res = await fetch(`${API_BASE}/intents/${originalItem.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fullLiveRequestJson),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error ${res.status}: Fallo al actualizar la intención`)
      }
      return res.json()
    },
    onSuccess: (data: IntentResponse) => {
      showFeedback('success', `Intención "${data.id}" actualizada a la versión v${data.metadata.version}.`)
      queryClient.invalidateQueries({ queryKey: ['intents'] })
      openEditorForEdit(data)
    },
    onError: (err: Error) => {
      showFeedback('error', err.message)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_BASE}/intents/${id}?deleted_by=${encodeURIComponent(draft.author)}`, {
        method: 'DELETE',
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error al trasladar intención a papelera`)
      }
      return res.json()
    },
    onSuccess: (data: TrashIntentResponse) => {
      showFeedback('success', `Intención "${data.id}" trasladada a papelera (30 días de retención).`)
      queryClient.invalidateQueries({ queryKey: ['intents'] })
      queryClient.invalidateQueries({ queryKey: ['intents-trash'] })
      if (viewMode === 'editor' && originalItem?.id === data.id) {
        setViewMode('inventory')
        setOriginalItem(null)
      }
    },
    onError: (err: Error) => {
      showFeedback('error', err.message)
    },
  })

  const restoreMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`${API_BASE}/intents/${id}/restore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ restored_by: 'investigador_principal' }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Error al restaurar intención`)
      }
      return res.json()
    },
    onSuccess: (data: IntentResponse) => {
      showFeedback('success', `Intención "${data.id}" restaurada exitosamente como v${data.metadata.version}.`)
      queryClient.invalidateQueries({ queryKey: ['intents'] })
      queryClient.invalidateQueries({ queryKey: ['intents-trash'] })
    },
    onError: (err: Error) => {
      showFeedback('error', err.message)
    },
  })

  const purgeMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/intents/trash/purge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ purged_by: 'investigador_principal' }),
      })
      if (!res.ok) throw new Error('Error al ejecutar purga')
      return res.json()
    },
    onSuccess: (data: { purged_count: number }) => {
      showFeedback('success', `Purga completada: ${data.purged_count} registros vencidos eliminados definitivamente.`)
      queryClient.invalidateQueries({ queryKey: ['intents-trash'] })
    },
    onError: (err: Error) => {
      showFeedback('error', err.message)
    },
  })

  const canSave = useMemo(() => {
    if (!isValidId) return false
    if (!isReviewComplete) return false
    if (draft.caseType === 'puro') {
      if (!draft.clasificacion.trim()) return false
    } else {
      if (!draft.conflicto_detectado.trim()) return false
      if (!draft.opciones_resolucion_text.trim()) return false
    }
    if (originalItem) {
      return hasChanges && !updateMutation.isPending
    }
    return !createMutation.isPending
  }, [isValidId, isReviewComplete, draft, originalItem, hasChanges, updateMutation.isPending, createMutation.isPending])

  // Filtrado de inventario
  const filteredIntents = useMemo(() => {
    return intents.filter((item) => {
      const matchesType = typeFilter === 'all' ? true : item.intent.tipo === typeFilter
      const q = searchQuery.toLowerCase().trim()
      if (!q) return matchesType

      const matchId = item.id.toLowerCase().includes(q)
      const matchAuthor = item.metadata.updated_by.toLowerCase().includes(q)
      const matchReviewer = (item.human_review?.reviewer || '').toLowerCase().includes(q)
      const matchDetail =
        item.intent.tipo === 'puro'
          ? (item.intent.clasificacion + ' ' + item.intent.razonamiento).toLowerCase().includes(q)
          : (item.intent.conflicto_detectado + ' ' + item.intent.opciones_resolucion.join(' ')).toLowerCase().includes(q)

      return matchesType && (matchId || matchAuthor || matchReviewer || matchDetail)
    })
  }, [intents, typeFilter, searchQuery])

  const pureCount = intents.filter((i) => i.intent.tipo === 'puro').length
  const conflictCount = intents.filter((i) => i.intent.tipo === 'conflicto').length

  // ===========================================================================
  // RENDER: VISTA 1 — INVENTARIO DE INTENCIONES (ESTÉTICA APPLE-LIKE / GALLERY)
  // ===========================================================================

  if (viewMode === 'inventory') {
    return (
      <div className="space-y-8 max-w-7xl mx-auto">
        {/* KPI CARDS: SUPERFICIES PEARL LIMPIAS SIN GRADIENTES NI SOMBRAS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="bg-white rounded-2xl p-6 border border-[#e5e5ea] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-medium tracking-wide text-[#86868b] uppercase">
                Almacén Activo
              </span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-medium bg-[#f5f5f7] text-[#1d1d1f]">
                Bloque B5
              </span>
            </div>
            <div className="my-4 flex items-baseline gap-2">
              <span className="text-4xl font-semibold tracking-tight text-[#1d1d1f]">{intents.length}</span>
              <span className="text-xs text-[#86868b]">intenciones declarativas</span>
            </div>
            <div className="pt-3 border-t border-[#f0f0f0] flex items-center gap-4 text-xs text-[#86868b]">
              <span className="inline-flex items-center gap-1.5 text-[#1d1d1f]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#34c759]"></span>
                {pureCount} Puros
              </span>
              <span className="inline-flex items-center gap-1.5 text-[#1d1d1f]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#ff9500]"></span>
                {conflictCount} Conflictivos
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-[#e5e5ea] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-medium tracking-wide text-[#86868b] uppercase">
                Papelera de Retención
              </span>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#f5f5f7] text-[#86868b]">
                30 Días
              </span>
            </div>
            <div className="my-4 flex items-baseline gap-2">
              <span className="text-4xl font-semibold tracking-tight text-[#1d1d1f]">{trash.length}</span>
              <span className="text-xs text-[#86868b]">borrados recuperables</span>
            </div>
            <div className="pt-3 border-t border-[#f0f0f0] flex items-center justify-between text-xs">
              <span className="text-[#86868b] flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#86868b]" />
                Soft-delete atómico
              </span>
              <button
                onClick={() => setActiveTab('trash')}
                className="text-[#0066cc] font-medium hover:underline cursor-pointer"
              >
                Ver papelera →
              </button>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 border border-[#e5e5ea] flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-medium tracking-wide text-[#86868b] uppercase">
                Confinamiento & Soberanía
              </span>
              <span
                className={`px-2 py-0.5 rounded-full text-[11px] font-medium flex items-center gap-1 ${
                  !errorIntents ? 'bg-[#f0fdf4] text-[#166534]' : 'bg-[#fef2f2] text-[#991b1b]'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${!errorIntents ? 'bg-[#34c759]' : 'bg-[#ff3b30]'}`}
                ></span>
                {!errorIntents ? 'Almacén Conectado' : 'Sin Conexión'}
              </span>
            </div>
            <div className="my-4 space-y-1 text-xs text-[#1d1d1f]">
              <div className="flex items-center gap-1.5 font-medium">
                <ShieldCheck className="w-4 h-4 text-[#34c759] shrink-0" />
                <span>EthosTerra_original: 0 escrituras</span>
              </div>
              <div className="text-[11px] text-[#86868b] font-mono">
                Persistencia: fsync + os.replace
              </div>
            </div>
            <div className="pt-3 border-t border-[#f0f0f0] text-[11px] text-[#86868b] font-mono truncate">
              outputs/intents/*.json
            </div>
          </div>
        </div>

        {/* FEEDBACK INLINE */}
        {feedback && (
          <div
            className={`p-4 rounded-xl text-xs flex items-center gap-3 border transition-all ${
              feedback.type === 'success'
                ? 'bg-[#f0fdf4] text-[#166534] border-[#bbf7d0]'
                : 'bg-[#fef2f2] text-[#991b1b] border-[#fecaca]'
            }`}
          >
            {feedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-[#34c759] shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-[#ff3b30] shrink-0" />
            )}
            <span className="font-medium">{feedback.message}</span>
          </div>
        )}

        {/* TABLA PRINCIPAL DE INVENTARIO */}
        <div className="bg-white border border-[#e5e5ea] rounded-2xl overflow-hidden">
          {/* Sub-nav de tabla */}
          <div className="px-6 py-4 border-b border-[#f0f0f0] flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-[#fafafc]">
            <div className="flex items-center gap-1.5 bg-[#f5f5f7] p-1 rounded-full text-xs font-medium">
              <button
                onClick={() => setActiveTab('active')}
                className={`px-3.5 py-1 rounded-full transition-all cursor-pointer ${
                  activeTab === 'active'
                    ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                    : 'text-[#86868b] hover:text-[#1d1d1f]'
                }`}
              >
                Activas ({intents.length})
              </button>
              <button
                onClick={() => setActiveTab('trash')}
                className={`px-3.5 py-1 rounded-full transition-all cursor-pointer ${
                  activeTab === 'trash'
                    ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                    : 'text-[#86868b] hover:text-[#1d1d1f]'
                }`}
              >
                Papelera ({trash.length})
              </button>
            </div>

            <div className="flex items-center gap-3 w-full md:w-auto">
              {activeTab === 'active' && (
                <>
                  <div className="relative flex-1 md:w-56">
                    <Search className="w-3.5 h-3.5 text-[#86868b] absolute left-3 top-2.5" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Buscar por ID, autor, término..."
                      className="w-full pl-8 pr-3 py-1.5 text-xs rounded-full border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] bg-white text-[#1d1d1f]"
                    />
                  </div>

                  <div className="flex items-center bg-[#f5f5f7] p-1 rounded-full text-[11px] font-medium text-[#86868b]">
                    <button
                      onClick={() => setTypeFilter('all')}
                      className={`px-2.5 py-0.5 rounded-full transition-all cursor-pointer ${
                        typeFilter === 'all' ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold' : 'hover:text-[#1d1d1f]'
                      }`}
                    >
                      Todas
                    </button>
                    <button
                      onClick={() => setTypeFilter('puro')}
                      className={`px-2.5 py-0.5 rounded-full transition-all cursor-pointer ${
                        typeFilter === 'puro' ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold' : 'hover:text-[#1d1d1f]'
                      }`}
                    >
                      Puros
                    </button>
                    <button
                      onClick={() => setTypeFilter('conflicto')}
                      className={`px-2.5 py-0.5 rounded-full transition-all cursor-pointer ${
                        typeFilter === 'conflicto' ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold' : 'hover:text-[#1d1d1f]'
                      }`}
                    >
                      Conflictos
                    </button>
                  </div>

                  <button
                    onClick={openEditorForCreate}
                    className="px-4 py-1.5 bg-[#0066cc] hover:bg-[#0071e3] text-white text-xs font-medium rounded-full flex items-center gap-1.5 transition-colors cursor-pointer"
                  >
                    <PlusCircle className="w-3.5 h-3.5" /> Nueva Intención
                  </button>
                </>
              )}

              {activeTab === 'trash' && (
                <button
                  onClick={() => purgeMutation.mutate()}
                  disabled={purgeMutation.isPending}
                  className="px-3.5 py-1.5 bg-[#ff3b30] hover:bg-[#e03126] text-white rounded-full text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                  title="Elimina definitivamente solo los registros que hayan superado los 30 días"
                >
                  <ShieldAlert className="w-3.5 h-3.5" /> Purgar Expirados (+30 días)
                </button>
              )}

              <button
                onClick={() => {
                  refetchIntents()
                  refetchTrash()
                }}
                className="p-1.5 text-[#86868b] hover:text-[#1d1d1f] rounded-full hover:bg-[#f5f5f7] transition-colors cursor-pointer"
                title="Actualizar listado"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* VISTA ACTIVAS */}
          {activeTab === 'active' ? (
            <div>
              {errorIntents ? (
                <div className="p-8 text-center text-xs text-[#86868b]">
                  <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-[#ff9500]" />
                  <div className="font-semibold text-sm text-[#1d1d1f]">Servidor Backend no detectado</div>
                  <p className="mt-1 text-xs text-[#86868b]">Inicia la API FastAPI en el puerto 8000 para sincronizar.</p>
                </div>
              ) : loadingIntents ? (
                <div className="p-16 text-center text-xs text-[#86868b]">
                  <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-[#86868b]" />
                  Consultando catálogo de intenciones...
                </div>
              ) : filteredIntents.length === 0 ? (
                <div className="p-16 text-center">
                  <div className="w-12 h-12 rounded-full bg-[#f5f5f7] flex items-center justify-center mx-auto text-[#86868b] mb-3">
                    <FileText className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-semibold text-[#1d1d1f]">No hay intenciones registradas</h4>
                  <p className="text-xs text-[#86868b] mt-1 max-w-sm mx-auto">
                    {searchQuery
                      ? 'No se encontraron coincidencias para la búsqueda.'
                      : 'Comienza creando una nueva intención declarativa manual.'}
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#fafafc] text-[#86868b] font-medium text-[11px] uppercase tracking-wider border-b border-[#f0f0f0]">
                      <tr>
                        <th className="px-6 py-3.5 font-normal">Identificador</th>
                        <th className="px-6 py-3.5 font-normal">Tipo</th>
                        <th className="px-6 py-3.5 font-normal">Semántica Declarativa</th>
                        <th className="px-6 py-3.5 font-normal">Dictamen Humano</th>
                        <th className="px-6 py-3.5 font-normal">Versión</th>
                        <th className="px-6 py-3.5 font-normal">Actualización</th>
                        <th className="px-6 py-3.5 text-right font-normal">Acciones</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f0f0f0] text-[#1d1d1f]">
                      {filteredIntents.map((item) => {
                        const isExpanded = expandedId === item.id
                        const revStatus = item.human_review?.status || 'pendiente'
                        return (
                          <tr key={item.id} className="hover:bg-[#fafafc] transition-colors">
                            <td className="px-6 py-4 font-mono text-[14px] align-top">
                              <div className="flex items-center gap-1.5">
                                <span className="font-semibold text-[#1d1d1f]">{item.id}</span>
                                <button
                                  onClick={() => handleCopy(item.id, `id_${item.id}`)}
                                  className="text-[#86868b] hover:text-[#1d1d1f] cursor-pointer p-0.5"
                                  title="Copiar ID"
                                >
                                  {copiedKey === `id_${item.id}` ? (
                                    <Check className="w-3.5 h-3.5 text-[#34c759]" />
                                  ) : (
                                    <Copy className="w-3.5 h-3.5" />
                                  )}
                                </button>
                              </div>
                              <div className="flex items-center gap-1 text-[11px] text-[#86868b] mt-0.5">
                                <span>{item.metadata.canonical_hash.slice(0, 10)}...</span>
                                <button
                                  onClick={() => handleCopy(item.metadata.canonical_hash, `hash_${item.id}`)}
                                  className="hover:text-[#1d1d1f] cursor-pointer p-0.5"
                                  title="Copiar hash completo"
                                >
                                  {copiedKey === `hash_${item.id}` ? (
                                    <Check className="w-2.5 h-2.5 text-[#34c759]" />
                                  ) : (
                                    <Copy className="w-2.5 h-2.5" />
                                  )}
                                </button>
                              </div>
                            </td>

                            <td className="px-6 py-4 align-top">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium inline-flex items-center gap-1.5 ${
                                  item.intent.tipo === 'puro'
                                    ? 'bg-[#f0fdf4] text-[#166534]'
                                    : 'bg-[#fffbeb] text-[#92400e]'
                                }`}
                              >
                                <span
                                  className={`w-1.5 h-1.5 rounded-full ${
                                    item.intent.tipo === 'puro' ? 'bg-[#34c759]' : 'bg-[#ff9500]'
                                  }`}
                                ></span>
                                {item.intent.tipo === 'puro' ? 'Caso Puro' : 'Conflictivo'}
                              </span>
                            </td>

                            <td className="px-6 py-4 align-top max-w-xs md:max-w-md">
                              {item.intent.tipo === 'puro' ? (
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-[#1d1d1f]">{item.intent.clasificacion}</span>
                                    <span className="text-[11px] font-medium text-[#166534] bg-[#f0fdf4] px-1.5 py-0.2 rounded-md">
                                      {(item.intent.confianza * 100).toFixed(0)}%
                                    </span>
                                  </div>
                                  <p className="text-[#86868b] text-xs line-clamp-2 leading-relaxed">
                                    {item.intent.razonamiento}
                                  </p>
                                </div>
                              ) : (
                                <div className="space-y-1">
                                  <span className="font-semibold text-[#1d1d1f] block leading-snug">
                                    {item.intent.conflicto_detectado}
                                  </span>
                                  <div className="text-[11px] text-[#86868b] flex items-center gap-2">
                                    <span>{item.intent.opciones_resolucion.length} alternativas</span>
                                    <span>•</span>
                                    <span className="text-[#92400e] font-medium">HITL Obligatorio</span>
                                  </div>
                                </div>
                              )}

                              {isExpanded && (
                                <div className="mt-3 pt-3 border-t border-[#f0f0f0] text-xs space-y-1.5 bg-[#f5f5f7] p-3 rounded-xl border border-[#e5e5ea]">
                                  <div className="flex items-center justify-between text-[11px] font-medium text-[#86868b]">
                                    <span className="flex items-center gap-1">
                                      <Code2 className="w-3.5 h-3.5 text-[#86868b]" />
                                      JSON Estructurado
                                    </span>
                                    <span className="font-mono text-[#86868b]">
                                      v{item.metadata.version} ({new Date(item.metadata.updated_at).toLocaleDateString()})
                                    </span>
                                  </div>
                                  <pre className="p-3 bg-white text-[#1d1d1f] rounded-lg font-mono text-[10px] overflow-x-auto max-h-48 border border-[#e5e5ea] leading-relaxed">
                                    {JSON.stringify(item, null, 2)}
                                  </pre>
                                </div>
                              )}
                            </td>

                            <td className="px-6 py-4 align-top">
                              <span
                                className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium inline-flex items-center gap-1.5 ${
                                  revStatus === 'aprobado'
                                    ? 'bg-[#f0fdf4] text-[#166534]'
                                    : revStatus === 'observado'
                                      ? 'bg-[#fffbeb] text-[#92400e]'
                                      : revStatus === 'rechazado'
                                        ? 'bg-[#fef2f2] text-[#991b1b]'
                                        : 'bg-[#f5f5f7] text-[#86868b]'
                                }`}
                              >
                                <span
                                  className={`w-1.5 h-1.5 rounded-full ${
                                    revStatus === 'aprobado'
                                      ? 'bg-[#34c759]'
                                      : revStatus === 'observado'
                                        ? 'bg-[#ff9500]'
                                        : revStatus === 'rechazado'
                                          ? 'bg-[#ff3b30]'
                                          : 'bg-[#86868b]'
                                  }`}
                                ></span>
                                {revStatus.toUpperCase()}
                              </span>
                              {item.human_review?.reviewer && (
                                <span className="block text-[11px] text-[#86868b] mt-1 font-mono truncate max-w-[120px]">
                                  {item.human_review.reviewer}
                                </span>
                              )}
                            </td>

                            <td className="px-6 py-4 font-mono text-xs text-[#1d1d1f] align-top">
                              <span className="px-2 py-0.5 rounded-md bg-[#f5f5f7] text-[#1d1d1f]">
                                v{item.metadata.version}
                              </span>
                            </td>

                            <td className="px-6 py-4 text-[#86868b] text-[11px] align-top whitespace-nowrap">
                              <div>{new Date(item.metadata.updated_at).toLocaleDateString()}</div>
                              <div className="text-[10px] text-[#86868b] font-mono mt-0.5">{item.metadata.updated_by}</div>
                            </td>

                            <td className="px-6 py-4 text-right align-top whitespace-nowrap">
                              <div className="flex justify-end items-center gap-1.5">
                                <button
                                  onClick={() => setExpandedId(isExpanded ? null : item.id)}
                                  className="p-1.5 text-[#86868b] hover:text-[#1d1d1f] rounded-full hover:bg-[#f5f5f7] transition-colors cursor-pointer"
                                  title={isExpanded ? 'Contraer' : 'Inspeccionar JSON'}
                                >
                                  {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                                </button>
                                <button
                                  onClick={() => openEditorForEdit(item)}
                                  className="px-3 py-1 text-xs font-medium rounded-full bg-[#f5f5f7] hover:bg-[#e5e5ea] text-[#1d1d1f] flex items-center gap-1 transition-colors cursor-pointer"
                                  title="Abrir en Consola Experta B5"
                                >
                                  <Edit3 className="w-3 h-3 text-[#0066cc]" /> Editar
                                </button>
                                <button
                                  onClick={() => deleteMutation.mutate(item.id)}
                                  className="p-1.5 text-[#86868b] hover:text-[#ff3b30] rounded-full hover:bg-[#fef2f2] transition-colors cursor-pointer"
                                  title="Mover a papelera (30 días)"
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
            /* VISTA PAPELERA */
            <div>
              {errorTrash ? (
                <div className="p-8 text-center text-xs text-[#86868b]">
                  <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-[#ff9500]" />
                  <div className="font-semibold text-sm text-[#1d1d1f]">Servidor no detectado</div>
                </div>
              ) : loadingTrash ? (
                <div className="p-16 text-center text-xs text-[#86868b]">
                  <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-[#86868b]" />
                  Cargando papelera...
                </div>
              ) : trash.length === 0 ? (
                <div className="p-16 text-center">
                  <div className="w-12 h-12 rounded-full bg-[#f5f5f7] flex items-center justify-center mx-auto text-[#86868b] mb-3">
                    <Archive className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-semibold text-[#1d1d1f]">La papelera está vacía</h4>
                  <p className="text-xs text-[#86868b] mt-1 max-w-sm mx-auto">
                    Los registros eliminados se resguardan aquí durante 30 días antes de su purga definitiva.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-[#fafafc] text-[#86868b] font-medium text-[11px] uppercase tracking-wider border-b border-[#f0f0f0]">
                      <tr>
                        <th className="px-6 py-3.5 font-normal">Identificador</th>
                        <th className="px-6 py-3.5 font-normal">Eliminado Por</th>
                        <th className="px-6 py-3.5 font-normal">Fecha de Borrado</th>
                        <th className="px-6 py-3.5 font-normal">Ventana de Retención</th>
                        <th className="px-6 py-3.5 font-normal">Estado</th>
                        <th className="px-6 py-3.5 text-right font-normal">Acción</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#f0f0f0] text-[#1d1d1f]">
                      {trash.map((item) => {
                        const expiresDate = new Date(item.trash_metadata.expires_at)
                        const deletedDate = new Date(item.trash_metadata.deleted_at)
                        const now = new Date()
                        const diffDays = Math.max(
                          0,
                          Math.ceil((expiresDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
                        )

                        return (
                          <tr key={item.id} className="hover:bg-[#fafafc] transition-colors">
                            <td className="px-6 py-4 font-mono text-[14px] font-semibold text-[#1d1d1f]">
                              {item.id}
                              <span className="block text-[11px] text-[#86868b] font-normal">
                                {item.intent.tipo === 'puro' ? 'Caso Puro' : 'Caso Conflicto'}
                              </span>
                            </td>

                            <td className="px-6 py-4 text-[#86868b] font-mono text-[11px]">
                              {item.trash_metadata.deleted_by}
                            </td>

                            <td className="px-6 py-4 text-[#86868b] text-[11px]">
                              {deletedDate.toLocaleString()}
                            </td>

                            <td className="px-6 py-4">
                              <div className="w-40">
                                <div className="flex justify-between text-[11px] text-[#86868b] mb-1">
                                  <span>{diffDays} días restantes</span>
                                  <span>30d</span>
                                </div>
                                <div className="w-full bg-[#f5f5f7] h-1.5 rounded-full overflow-hidden">
                                  <div
                                    className="bg-[#ff9500] h-full rounded-full transition-all"
                                    style={{ width: `${Math.min(100, (diffDays / 30) * 100)}%` }}
                                  ></div>
                                </div>
                              </div>
                            </td>

                            <td className="px-6 py-4">
                              {item.trash_metadata.is_expired ? (
                                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#fef2f2] text-[#991b1b]">
                                  Expirado
                                </span>
                              ) : (
                                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#f0fdf4] text-[#166534] inline-flex items-center gap-1">
                                  <Clock className="w-3 h-3 text-[#34c759]" /> Restaurable
                                </span>
                              )}
                            </td>

                            <td className="px-6 py-4 text-right">
                              <button
                                disabled={item.trash_metadata.is_expired || restoreMutation.isPending}
                                onClick={() => restoreMutation.mutate(item.id)}
                                className="px-3.5 py-1 text-xs font-medium rounded-full bg-[#0066cc] hover:bg-[#0071e3] text-white disabled:opacity-30 disabled:pointer-events-none inline-flex items-center gap-1.5 transition-colors cursor-pointer ml-auto"
                              >
                                <RotateCcw className="w-3 h-3" /> Restaurar
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

  // ===========================================================================
  // RENDER: VISTA 2 — CONSOLA EXPERTA B5 (ESTÉTICA APPLE-LIKE / REVISIÓN RIGUROSA)
  // ===========================================================================

  const isEditing = originalItem !== null
  const currentVersion = originalItem ? originalItem.metadata.version : 1
  const nextVersion = originalItem ? originalItem.metadata.version + 1 : 1
  const canonicalHashOnDisk = originalItem ? originalItem.metadata.canonical_hash : ''
  const isHashIdentical = canonicalHashOnDisk === liveHash

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-16">
      {/* 1. ENCABEZADO SUPERIOR: CONTEXT BAR FROSTED STICKY (PATRÓN APPLE) */}
      <div className="bg-white/90 backdrop-blur-md border border-[#e5e5ea] rounded-2xl px-6 py-3 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 sticky top-4 z-30 shadow-xs">
        {/* Lado izquierdo: navegación y contexto */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleReturnToInventory}
            className="text-xs text-[#0066cc] hover:underline inline-flex items-center gap-1 font-medium transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Volver al inventario
          </button>

          <span className="text-[#d2d2d7]">/</span>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#86868b] font-medium hidden sm:inline">Consola B5</span>
            <span className="font-mono text-xs font-semibold text-[#1d1d1f]">
              {draft.id || 'nueva_intencion'}
            </span>
            <span className="px-2 py-0.5 rounded-full text-[11px] font-mono text-[#86868b] bg-[#f5f5f7]">
              v{currentVersion}
            </span>
          </div>
        </div>

        {/* Lado derecho: estado de revisión, hash oficial, sincronización y acción primaria */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Badge sutil de Dictamen */}
          <span
            className={`px-3 py-0.5 rounded-full text-xs font-medium inline-flex items-center gap-1.5 ${
              draft.review_status === 'aprobado'
                ? 'bg-[#f0fdf4] text-[#166534]'
                : draft.review_status === 'observado'
                  ? 'bg-[#fffbeb] text-[#92400e]'
                  : draft.review_status === 'rechazado'
                    ? 'bg-[#fef2f2] text-[#991b1b]'
                    : 'bg-[#f5f5f7] text-[#86868b]'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                draft.review_status === 'aprobado'
                  ? 'bg-[#34c759]'
                  : draft.review_status === 'observado'
                    ? 'bg-[#ff9500]'
                    : draft.review_status === 'rechazado'
                      ? 'bg-[#ff3b30]'
                      : 'bg-[#86868b]'
              }`}
            ></span>
            {draft.review_status.toUpperCase()}
          </span>

          {/* Hash Oficial Resumido en Disco */}
          {canonicalHashOnDisk ? (
            <div className="hidden lg:flex items-center gap-1 text-[12px] font-mono text-[#86868b]">
              <span>Hash en disco:</span>
              <span className="text-[#1d1d1f]">{canonicalHashOnDisk.slice(0, 8)}...</span>
              <button
                onClick={() => handleCopy(canonicalHashOnDisk, 'top_hash')}
                className="hover:text-[#1d1d1f] cursor-pointer p-0.5"
                title="Copiar hash oficial"
              >
                {copiedKey === 'top_hash' ? (
                  <Check className="w-3 h-3 text-[#34c759]" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
              </button>
            </div>
          ) : (
            <span className="hidden lg:inline text-[11px] font-mono text-[#86868b]">
              Borrador no persistido
            </span>
          )}

          {/* Estado de sincronización local */}
          {isEditing && (
            <span
              className={`text-[11px] font-medium px-2 py-0.5 rounded-full hidden sm:inline-flex items-center gap-1 ${
                hasChanges ? 'bg-[#fffbeb] text-[#92400e]' : 'bg-[#f5f5f7] text-[#86868b]'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${hasChanges ? 'bg-[#ff9500] animate-pulse' : 'bg-[#34c759]'}`}
              ></span>
              {hasChanges ? 'Modificado localmente' : 'Sincronizado'}
            </span>
          )}

          {/* Acciones principales en header */}
          <div className="flex items-center gap-2">
            {hasChanges && (
              <button
                type="button"
                onClick={handleDiscardChanges}
                className="text-xs text-[#0066cc] hover:underline font-medium cursor-pointer"
              >
                Descartar
              </button>
            )}

            {isEditing ? (
              <button
                type="button"
                onClick={() => updateMutation.mutate()}
                disabled={!canSave}
                className="px-4 py-1.5 bg-[#0066cc] hover:bg-[#0071e3] disabled:opacity-30 disabled:pointer-events-none text-white text-xs font-medium rounded-full transition-all cursor-pointer flex items-center gap-1.5"
                title={!canSave ? 'Completa los campos obligatorios o realiza cambios para guardar' : undefined}
              >
                <RefreshCw className={`w-3 h-3 ${updateMutation.isPending ? 'animate-spin' : ''}`} />
                Guardar cambios (v{currentVersion} → v{nextVersion})
              </button>
            ) : (
              <button
                type="button"
                onClick={() => createMutation.mutate()}
                disabled={!canSave}
                className="px-4 py-1.5 bg-[#0066cc] hover:bg-[#0071e3] disabled:opacity-30 disabled:pointer-events-none text-white text-xs font-medium rounded-full transition-all cursor-pointer flex items-center gap-1.5"
                title={!canSave ? 'Ingresa un identificador válido y completa los campos' : undefined}
              >
                <PlusCircle className={`w-3 h-3 ${createMutation.isPending ? 'animate-spin' : ''}`} />
                Registrar intención (v1)
              </button>
            )}
          </div>
        </div>
      </div>

      {/* FEEDBACK INLINE */}
      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center gap-3 border transition-all ${
            feedback.type === 'success'
              ? 'bg-[#f0fdf4] text-[#166534] border-[#bbf7d0]'
              : 'bg-[#fef2f2] text-[#991b1b] border-[#fecaca]'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-[#34c759] shrink-0" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-[#ff3b30] shrink-0" />
          )}
          <span className="font-medium">{feedback.message}</span>
        </div>
      )}

      {/* 2. GRID PRINCIPAL: 8 COLS LIENZO EDITORIAL / 4 COLS INSPECTOR LATERAL */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* COLUMNA PRINCIPAL (8 COLS): LIENZO DE TRABAJO CONTINUO */}
        <div className="lg:col-span-8 bg-white border border-[#e5e5ea] rounded-2xl p-8 space-y-8">
          {/* HEADER EDITORIAL DEL DOCUMENTO */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-mono font-medium text-[#86868b] uppercase tracking-wider">
                {draft.caseType === 'puro' ? 'Caso Puro • Especificación' : 'Caso Conflictivo • Especificación'}
              </span>
              {!isEditing && (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={loadPureTemplate}
                    className="text-xs text-[#0066cc] hover:underline cursor-pointer flex items-center gap-1"
                  >
                    <Sparkles className="w-3 h-3" /> Plantilla Puro
                  </button>
                  <span className="text-[#d2d2d7]">•</span>
                  <button
                    type="button"
                    onClick={loadConflictTemplate}
                    className="text-xs text-[#0066cc] hover:underline cursor-pointer flex items-center gap-1"
                  >
                    <Scale className="w-3 h-3" /> Plantilla Conflicto
                  </button>
                </div>
              )}
            </div>

            <h1 className="text-2xl font-semibold tracking-tight text-[#1d1d1f]">
              {isEditing ? `Intención: ${draft.id}` : 'Nueva Intención Declarativa'}
            </h1>
            <p className="text-sm text-[#86868b] leading-relaxed">
              Consola experta para el registro, edición y deliberación humana de intenciones declarativas (Bloque B5).
            </p>

            {/* Fila de metadatos tipo Mac Inspector */}
            <div className="pt-3 border-t border-[#f0f0f0] flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-[#86868b] font-mono">
              <span>
                Almacenamiento:{' '}
                <span className="text-[#1d1d1f]">outputs/intents/{draft.id || '...'}.json</span>
              </span>
              <span>•</span>
              <span>
                Operador: <span className="text-[#1d1d1f]">{draft.author}</span>
              </span>
              {isEditing && originalItem && (
                <>
                  <span>•</span>
                  <span>
                    Actualizado: {new Date(originalItem.metadata.updated_at).toLocaleDateString()}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* SECCIÓN 1: IDENTIDAD Y AUTORÍA */}
          <div className="space-y-4 pt-2">
            <h2 className="text-base font-semibold tracking-tight text-[#1d1d1f]">
              1. Identidad y Autoría del Registro
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                  Identificador Único (ID)
                </label>
                <input
                  type="text"
                  disabled={isEditing}
                  value={draft.id}
                  onChange={(e) => setDraft((prev) => ({ ...prev, id: e.target.value }))}
                  placeholder="ej: siembra_maiz_parcela_01"
                  className={`w-full px-3.5 py-2 text-[14px] font-mono rounded-xl border focus:outline-none focus:ring-2 focus:ring-[#0066cc]/10 bg-white disabled:bg-[#f5f5f7] disabled:text-[#86868b] transition-all ${
                    !isValidId && !isEditing && draft.id.length > 0
                      ? 'border-[#ff3b30] focus:border-[#ff3b30]'
                      : 'border-[#e5e5ea] focus:border-[#0066cc]'
                  }`}
                />
                <span className="text-[11px] text-[#86868b] block mt-1">
                  Alfanumérico, guion o guion bajo (inmutable tras su creación).
                </span>
                {!isValidId && !isEditing && draft.id.length > 0 && (
                  <span className="text-[11px] text-[#ff3b30] block mt-0.5">
                    Debe contener entre 1 y 64 caracteres alfanuméricos sin espacios ni caracteres especiales.
                  </span>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                  Autor / Operador Técnico
                </label>
                <input
                  type="text"
                  value={draft.author}
                  onChange={(e) => setDraft((prev) => ({ ...prev, author: e.target.value }))}
                  className="w-full px-3.5 py-2 text-xs rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white text-[#1d1d1f] transition-all"
                />
                <span className="text-[11px] text-[#86868b] block mt-1">
                  Firma de auditoría para la trazabilidad del registro.
                </span>
              </div>
            </div>
          </div>

          <div className="border-t border-[#f0f0f0]"></div>

          {/* SECCIÓN 2: SEMÁNTICA DECLARATIVA DE LA INTENCIÓN */}
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div>
                <h2 className="text-base font-semibold tracking-tight text-[#1d1d1f]">
                  2. Semántica Declarativa
                </h2>
                <p className="text-xs text-[#86868b] mt-0.5">
                  Estructuración formal de la intención (Caso Puro o Caso Conflictivo).
                </p>
              </div>

              {/* Selector segmentado tipo pastilla Apple */}
              <div className="flex items-center bg-[#f5f5f7] p-1 rounded-full text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setDraft((prev) => ({ ...prev, caseType: 'puro' }))}
                  className={`px-3.5 py-1 rounded-full transition-all cursor-pointer ${
                    draft.caseType === 'puro'
                      ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                      : 'text-[#86868b] hover:text-[#1d1d1f]'
                  }`}
                >
                  Caso Puro
                </button>
                <button
                  type="button"
                  onClick={() => setDraft((prev) => ({ ...prev, caseType: 'conflicto' }))}
                  className={`px-3.5 py-1 rounded-full transition-all cursor-pointer ${
                    draft.caseType === 'conflicto'
                      ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                      : 'text-[#86868b] hover:text-[#1d1d1f]'
                  }`}
                >
                  Caso Conflictivo
                </button>
              </div>
            </div>

            {draft.caseType === 'puro' ? (
              /* CAMPOS ESTRICTOS DE CASO PURO */
              <div className="space-y-5 pt-1">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                      Clasificación de la Intención
                    </label>
                    <input
                      type="text"
                      value={draft.clasificacion}
                      onChange={(e) => setDraft((prev) => ({ ...prev, clasificacion: e.target.value }))}
                      placeholder="ej: ejecutar_accion"
                      className="w-full px-3.5 py-2 text-xs rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white text-[#1d1d1f]"
                    />
                    <div className="flex gap-1.5 mt-2 flex-wrap">
                      {['ejecutar_accion', 'actualizar_creencia', 'consultar_estado', 'observar_entorno'].map(
                        (tag) => (
                          <button
                            key={tag}
                            type="button"
                            onClick={() => setDraft((prev) => ({ ...prev, clasificacion: tag }))}
                            className="text-[11px] px-2.5 py-0.5 rounded-full bg-[#f5f5f7] hover:bg-[#e5e5ea] text-[#86868b] hover:text-[#1d1d1f] font-mono cursor-pointer transition-colors"
                          >
                            {tag}
                          </button>
                        )
                      )}
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="text-xs font-semibold text-[#1d1d1f]">Nivel de Confianza</label>
                      <span className="font-mono text-xs font-semibold text-[#1d1d1f] bg-[#f5f5f7] px-2 py-0.5 rounded-md">
                        {(draft.confianza * 100).toFixed(0)}%
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={draft.confianza}
                      onChange={(e) => setDraft((prev) => ({ ...prev, confianza: parseFloat(e.target.value) }))}
                      className="w-full accent-[#0066cc] cursor-pointer mt-2"
                    />
                    <span className="text-[11px] text-[#86868b] block mt-1">
                      Criterio de certeza asignado a la intención declarativa.
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                    Razonamiento Semántico
                  </label>
                  <textarea
                    rows={4}
                    value={draft.razonamiento}
                    onChange={(e) => setDraft((prev) => ({ ...prev, razonamiento: e.target.value }))}
                    placeholder="Describe la justificación de la intención, contexto causal o premisas agronómicas..."
                    className="w-full px-3.5 py-2.5 text-xs text-[#1d1d1f] leading-relaxed rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white"
                  />
                </div>
              </div>
            ) : (
              /* CAMPOS ESTRICTOS DE CASO CONFLICTIVO */
              <div className="space-y-5 pt-1">
                <div>
                  <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                    Descripción de la Contradicción o Conflicto
                  </label>
                  <textarea
                    rows={3}
                    value={draft.conflicto_detectado}
                    onChange={(e) => setDraft((prev) => ({ ...prev, conflicto_detectado: e.target.value }))}
                    placeholder="Detalla con precisión la colisión entre normas, recursos escasos o metas contrapuestas..."
                    className="w-full px-3.5 py-2.5 text-xs text-[#1d1d1f] leading-relaxed rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                    Opciones de Resolución (una por línea)
                  </label>
                  <textarea
                    rows={3}
                    value={draft.opciones_resolucion_text}
                    onChange={(e) => setDraft((prev) => ({ ...prev, opciones_resolucion_text: e.target.value }))}
                    placeholder="Opción 1: Aplicación focalizada con margen de seguridad&#10;Opción 2: Escalamiento a inspección comunitaria&#10;Opción 3: Poda preventiva y aislamiento"
                    className="w-full px-3.5 py-2.5 text-xs font-mono text-[11px] text-[#1d1d1f] rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div>
                    <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                      Título Descriptivo del Conflicto (opcional)
                    </label>
                    <input
                      type="text"
                      value={draft.titulo_conflicto}
                      onChange={(e) => setDraft((prev) => ({ ...prev, titulo_conflicto: e.target.value }))}
                      placeholder="ej: Colisión Cuota Hídrica vs Fitopatología"
                      className="w-full px-3.5 py-2 text-xs rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white text-[#1d1d1f]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                      Ubicación / Parcela (opcional)
                    </label>
                    <input
                      type="text"
                      value={draft.ubicacion}
                      onChange={(e) => setDraft((prev) => ({ ...prev, ubicacion: e.target.value }))}
                      placeholder="ej: parcela_a1"
                      className="w-full px-3.5 py-2 text-xs rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white text-[#1d1d1f]"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="check_human_loop"
                    checked={draft.requiere_humano}
                    onChange={(e) => setDraft((prev) => ({ ...prev, requiere_humano: e.target.checked }))}
                    className="rounded border-[#e5e5ea] text-[#0066cc] focus:ring-[#0066cc] cursor-pointer"
                  />
                  <label htmlFor="check_human_loop" className="text-xs text-[#1d1d1f] font-medium cursor-pointer">
                    Intervención humana obligatoria en el ciclo (Human-in-the-loop requerido)
                  </label>
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-[#f0f0f0]"></div>

          {/* SECCIÓN 3: REVISIÓN HUMANA SEPARADA (PERSISTIDA FORMALMENTE) */}
          <div className="space-y-5">
            <div>
              <h2 className="text-base font-semibold tracking-tight text-[#1d1d1f]">
                3. Revisión Humana Separada
              </h2>
              <p className="text-xs text-[#86868b] mt-0.5">
                Dictamen explícito y justificación metodológica independiente del payload semántico.
              </p>
            </div>

            {/* Selector de 4 Estados en Pastilla Continua */}
            <div>
              <label className="block text-xs font-semibold text-[#1d1d1f] mb-2">
                Dictamen de Revisión
              </label>
              <div className="bg-[#f5f5f7] p-1 rounded-full grid grid-cols-4 gap-1 text-xs">
                {(
                  [
                    { id: 'pendiente', label: 'Pendiente', dot: 'bg-[#86868b]' },
                    { id: 'aprobado', label: 'Aprobado', dot: 'bg-[#34c759]' },
                    { id: 'observado', label: 'Observado', dot: 'bg-[#ff9500]' },
                    { id: 'rechazado', label: 'Rechazado', dot: 'bg-[#ff3b30]' },
                  ] as const
                ).map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setDraft((prev) => ({ ...prev, review_status: opt.id }))}
                    className={`py-1.5 rounded-full transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                      draft.review_status === opt.id
                        ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold'
                        : 'text-[#86868b] hover:text-[#1d1d1f]'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${opt.dot}`}></span>
                    <span>{opt.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                  Evaluador Responsable
                </label>
                <input
                  type="text"
                  value={draft.reviewer}
                  onChange={(e) => setDraft((prev) => ({ ...prev, reviewer: e.target.value }))}
                  placeholder="ej: investigador_principal"
                  className="w-full px-3.5 py-2 text-xs rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white text-[#1d1d1f]"
                />
              </div>

              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="check_add_review"
                  checked={draft.requires_additional_review}
                  onChange={(e) => setDraft((prev) => ({ ...prev, requires_additional_review: e.target.checked }))}
                  className="rounded border-[#e5e5ea] text-[#0066cc] focus:ring-[#0066cc] cursor-pointer"
                />
                <label htmlFor="check_add_review" className="text-xs text-[#1d1d1f] font-medium cursor-pointer">
                  Requiere segunda revisión o escalamiento
                </label>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-[#1d1d1f]">
                  Justificación de la Decisión
                </label>
                {(draft.review_status === 'aprobado' || draft.review_status === 'rechazado') && (
                  <span className="text-[11px] font-medium text-[#92400e]">
                    Obligatoria para emitir dictamen
                  </span>
                )}
              </div>
              <textarea
                rows={3}
                value={draft.decision_rationale}
                onChange={(e) => setDraft((prev) => ({ ...prev, decision_rationale: e.target.value }))}
                placeholder="Fundamento metodológico por el cual se valida, observa o rechaza este caso..."
                className={`w-full px-3.5 py-2.5 text-xs text-[#1d1d1f] leading-relaxed rounded-xl border focus:outline-none focus:ring-2 focus:ring-[#0066cc]/10 bg-white ${
                  !isReviewComplete && (draft.review_status === 'aprobado' || draft.review_status === 'rechazado')
                    ? 'border-[#ff9500] focus:border-[#ff9500]'
                    : 'border-[#e5e5ea] focus:border-[#0066cc]'
                }`}
              />
              {!isReviewComplete && (draft.review_status === 'aprobado' || draft.review_status === 'rechazado') && (
                <span className="text-[11px] text-[#92400e] block mt-1">
                  Para registrar el dictamen como &quot;Aprobado&quot; o &quot;Rechazado&quot;, es obligatorio ingresar el evaluador responsable y la justificación.
                </span>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#1d1d1f] mb-1.5">
                Observaciones Metodológicas y Notas de Campo
              </label>
              <textarea
                rows={2}
                value={draft.comments}
                onChange={(e) => setDraft((prev) => ({ ...prev, comments: e.target.value }))}
                placeholder="Notas complementarias, contexto de recolección o recomendaciones operativas..."
                className="w-full px-3.5 py-2.5 text-xs text-[#1d1d1f] leading-relaxed rounded-xl border border-[#e5e5ea] focus:outline-none focus:border-[#0066cc] focus:ring-2 focus:ring-[#0066cc]/10 bg-white"
              />
            </div>
          </div>

          <div className="border-t border-[#f0f0f0]"></div>

          {/* SECCIÓN 4: CONFINAMIENTO Y SOBERANÍA (WHISPER FOOTNOTE) */}
          <div className="p-4 rounded-xl bg-[#f5f5f7] border border-[#e5e5ea] text-xs text-[#86868b] font-mono leading-relaxed flex items-start gap-3">
            <ShieldCheck className="w-4 h-4 text-[#34c759] shrink-0 mt-0.5" />
            <div>
              <strong className="text-[#1d1d1f]">Almacenamiento Confinado B5:</strong> Los registros se persisten
              atómicamente en <code className="text-[#1d1d1f]">outputs/intents/</code> mediante escritura en archivo
              temporal y reemplazo seguro (<code className="text-[#1d1d1f]">fsync + os.replace</code>). El entorno
              multiagente en <code className="text-[#1d1d1f]">EthosTerra_original/</code> permanece protegido con{' '}
              <strong className="text-[#1d1d1f]">0 escrituras directas</strong>.
            </div>
          </div>
        </div>

        {/* COLUMNA LATERAL (4 COLS): INSPECTOR DE AUDITORÍA SILENCIOSO */}
        <div className="lg:col-span-4 bg-[#fafafc] border border-[#e5e5ea] rounded-2xl p-6 space-y-6 sticky top-20">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[#86868b]">
                Inspector de Auditoría
              </span>

              {/* Selector Diff / Payload */}
              <div className="flex items-center bg-[#f5f5f7] p-0.5 rounded-full text-[11px] font-medium text-[#86868b]">
                <button
                  type="button"
                  onClick={() => setAuditTab('diff')}
                  className={`px-2.5 py-0.5 rounded-full transition-all cursor-pointer ${
                    auditTab === 'diff' ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold' : 'hover:text-[#1d1d1f]'
                  }`}
                >
                  Diff ({diffItems.length})
                </button>
                <button
                  type="button"
                  onClick={() => setAuditTab('json')}
                  className={`px-2.5 py-0.5 rounded-full transition-all cursor-pointer ${
                    auditTab === 'json' ? 'bg-white text-[#1d1d1f] shadow-xs font-semibold' : 'hover:text-[#1d1d1f]'
                  }`}
                >
                  JSON
                </button>
              </div>
            </div>

            {/* ESTADO DE SINCRONIZACIÓN */}
            <div className="mt-3">
              {!isEditing ? (
                <div className="p-3 bg-white rounded-xl text-xs text-[#86868b] border border-[#e5e5ea] flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-[#0066cc] shrink-0" />
                  <span>Modo creación: constituirá la versión canónica inicial v1.</span>
                </div>
              ) : !hasChanges ? (
                <div className="p-3 bg-white rounded-xl text-xs text-[#1d1d1f] border border-[#e5e5ea] flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#34c759] shrink-0" />
                  <span>Sincronizado con versión en disco (v{currentVersion}).</span>
                </div>
              ) : (
                <div className="p-3 bg-[#fffbeb] rounded-xl text-xs border border-[#fef3c7] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#ff9500] animate-pulse"></span>
                    <span className="font-medium text-[#92400e]">
                      {diffItems.length} {diffItems.length === 1 ? 'cambio pendiente' : 'cambios pendientes'}
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-[#92400e]">
                    v{currentVersion} → v{nextVersion}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* CONTENIDO DEL INSPECTOR: DIFF */}
          {auditTab === 'diff' && (
            <div className="space-y-2.5">
              {!isEditing ? (
                <div className="p-4 bg-white rounded-xl border border-[#e5e5ea] text-xs text-[#86868b] text-center">
                  El diff estará disponible tras persistir la versión inicial v1.
                </div>
              ) : !hasChanges ? (
                <div className="p-4 bg-white rounded-xl border border-[#e5e5ea] text-xs text-[#86868b] text-center">
                  Sin diferencias respecto a la versión en disco (v{currentVersion}).
                </div>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {diffItems.map((d) => (
                    <div key={d.field} className="p-3 bg-white rounded-xl border border-[#e5e5ea] text-xs space-y-1">
                      <div className="font-medium text-[#1d1d1f]">{d.label}</div>
                      <div className="space-y-0.5 font-mono text-[11px]">
                        <div className="text-[#86868b] line-through truncate">- {d.original}</div>
                        <div className="text-[#1d1d1f] font-semibold truncate">+ {d.current}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* CONTENIDO DEL INSPECTOR: JSON */}
          {auditTab === 'json' && (
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[10px] text-[#86868b] font-mono">
                <span>Payload Pydantic V2</span>
                <button
                  onClick={() => handleCopy(JSON.stringify(fullLiveRequestJson, null, 2), 'payload_json')}
                  className="text-[#0066cc] hover:underline flex items-center gap-1 font-medium cursor-pointer"
                >
                  {copiedKey === 'payload_json' ? (
                    <Check className="w-3 h-3 text-[#34c759]" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                  Copiar
                </button>
              </div>
              <pre className="p-3 bg-white text-[#1d1d1f] rounded-xl font-mono text-[10px] overflow-x-auto max-h-64 border border-[#e5e5ea] leading-relaxed">
                {JSON.stringify(fullLiveRequestJson, null, 2)}
              </pre>
            </div>
          )}

          {/* INTEGRIDAD CRIPTOGRÁFICA Y TRAZABILIDAD */}
          <div className="pt-3 border-t border-[#f0f0f0] space-y-2 text-xs">
            <div className="flex items-center justify-between text-[11px] text-[#86868b]">
              <span className="flex items-center gap-1 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-[#86868b]" />
                Hashes SHA-256
              </span>
              <span className="font-mono text-[10px]">
                {isHashIdentical ? 'Inalterado' : 'Mutará al guardar'}
              </span>
            </div>

            <div className="font-mono text-[12px] bg-white p-3 rounded-xl border border-[#e5e5ea] text-[#1d1d1f] space-y-2">
              {isEditing && (
                <div className="space-y-0.5">
                  <div className="text-[10px] text-[#86868b]">Oficial en disco (v{currentVersion}):</div>
                  <div className="text-[11px] text-[#1d1d1f] break-all">{canonicalHashOnDisk || '—'}</div>
                </div>
              )}
              <div className="space-y-0.5 pt-1 border-t border-[#f0f0f0]">
                <div className="text-[10px] text-[#86868b]">Estimado local (provisional):</div>
                <div className="text-[11px] font-semibold text-[#0066cc] break-all">{liveHash || '—'}</div>
              </div>
            </div>

            {/* Metadatos de auditoría en disco */}
            {isEditing && originalItem && (
              <div className="p-3 bg-white rounded-xl border border-[#e5e5ea] space-y-1.5 text-[11px] text-[#86868b]">
                <div className="flex justify-between">
                  <span>Creado por:</span>
                  <span className="font-mono text-[#1d1d1f]">{originalItem.metadata.created_by}</span>
                </div>
                <div className="flex justify-between">
                  <span>Fecha creación:</span>
                  <span className="text-[#1d1d1f]">{new Date(originalItem.metadata.created_at).toLocaleString()}</span>
                </div>
                <div className="flex justify-between pt-1 border-t border-[#f0f0f0]">
                  <span>Última edición por:</span>
                  <span className="font-mono text-[#1d1d1f]">{originalItem.metadata.updated_by}</span>
                </div>
                <div className="flex justify-between">
                  <span>Fecha edición:</span>
                  <span className="text-[#1d1d1f]">{new Date(originalItem.metadata.updated_at).toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>

          {/* ACCIONES DE CICLO DE VIDA EN SIDEBAR */}
          <div className="pt-3 border-t border-[#f0f0f0] space-y-2">
            {isEditing ? (
              <button
                type="button"
                onClick={() => updateMutation.mutate()}
                disabled={!canSave}
                className="w-full py-2 bg-[#0066cc] hover:bg-[#0071e3] disabled:opacity-30 disabled:pointer-events-none text-white text-xs font-medium rounded-full transition-colors cursor-pointer text-center"
              >
                Guardar modificaciones (v{currentVersion} → v{nextVersion})
              </button>
            ) : (
              <button
                type="button"
                onClick={() => createMutation.mutate()}
                disabled={!canSave}
                className="w-full py-2 bg-[#0066cc] hover:bg-[#0071e3] disabled:opacity-30 disabled:pointer-events-none text-white text-xs font-medium rounded-full transition-colors cursor-pointer text-center"
              >
                Registrar intención canónica (v1)
              </button>
            )}

            <button
              type="button"
              onClick={handleDiscardChanges}
              disabled={!hasChanges && isEditing}
              className="w-full text-center text-xs text-[#0066cc] hover:underline py-1 disabled:opacity-30 disabled:pointer-events-none cursor-pointer"
            >
              Descartar modificaciones
            </button>

            {isEditing && (
              <div className="pt-2 border-t border-[#f0f0f0]">
                <button
                  type="button"
                  onClick={() => {
                    const confirmDel = window.confirm(
                      `¿Confirmas el traslado de la intención "${originalItem?.id}" a la papelera de 30 días?`
                    )
                    if (confirmDel && originalItem) {
                      deleteMutation.mutate(originalItem.id)
                    }
                  }}
                  disabled={deleteMutation.isPending}
                  className="w-full text-center text-xs text-[#86868b] hover:text-[#ff3b30] py-1 transition-colors cursor-pointer"
                >
                  Mover a papelera (30 días de retención)
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
