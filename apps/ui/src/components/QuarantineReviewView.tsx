import { useEffect, useState } from 'react'
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  Layers,
  Database,
  UserCheck,
  RefreshCw,
  Send,
  FileText,
  Brain,
  Sparkles,
  AlertOctagon,
  Code,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Zap,
  Target,
  X,
  Edit3,
  Save,
  FileCode,
  Activity,
  Cpu,
  Upload,
  Plus,
  Trash2,
  Globe,
  FileUp,
} from 'lucide-react'

const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/v2'

export interface AuthorizedSeed {
  seed_id: string
  url: string
  entity: string
  title: string
  territory_scope: string
  instrument_type: string
  pipeline_type: string
  document_format: string
  added_by: string
  added_at: string
  is_active: boolean
}

export interface TerritorialBeliefItem {
  belief_id: string
  source_id: string
  pillar: string
  topic: string
  belief_key?: string
  trigger_condition?: string
  executable_action?: string
  action_operation_type?: string | null
  behavioral_effect?: string
  activation_rule_template?: string
  raw_excerpt: string
  ebdi_belief_assertion: string
  target_municipalities: string[]
  applicable_divipolas: string[]
  confidence: number
  verification_status: 'verified_verbatim' | 'hallucination_rejected'
  collision_detected?: boolean
  collision_reason?: string | null
  curation_status?: 'admitted_ebdi' | 'dismissed_noise' | 'pending'
  curation_notes?: string | null
  curator_id?: string | null
  curation_timestamp_utc?: string | null
}

export interface TerritorialBeliefExtractionResult {
  source_id: string
  instrument_title: string
  document_sha256: string
  extraction_timestamp_utc: string
  model_used: string
  extraction_method: string
  total_beliefs_extracted: number
  verified_beliefs_count: number
  rejected_hallucinations_count: number
  beliefs: TerritorialBeliefItem[]
}

export interface ReviewEvent {
  event_id: string
  timestamp_utc: string
  reviewer_id: string
  reviewer_auth_mode: string
  decision: string
  review_notes: string
  previous_status?: string | null
  event_type?: string
  is_valid_human_approval?: boolean
}

export interface QuarantineDocument {
  source_id: string
  title: string
  entity: string
  instrument_type?: string | null
  territory_scope: string
  status: string
  approval_status: string
  previous_source_id?: string | null
  approval_notes: string
  canonical_url: string
  sha256: string
  byte_size: number
  allowed_for_training: boolean
  usage_state: string
  approval_timestamp?: string | null
  reviewer_id?: string | null
  reviewer_auth_mode?: string | null
  review_events?: ReviewEvent[]
  content_path?: string
  download_date?: string
  provenance_class?: string
}

export interface RegisteredCandidate {
  source_id: string
  title: string
  entity: string
  instrument_type: string
  territory_scope: string
  status: string
  approval_status: string
  previous_source_id?: string | null
  approval_notes?: string | null
  canonical_url: string
  sha256?: string | null
  byte_size?: number | null
  allowed_for_training: boolean
  usage_state: string
  approval_timestamp?: string | null
  reviewer_id?: string | null
  is_downloaded: boolean
  notes?: string
  selection_reason?: string | null
  review_notes?: string | null
  instruction_feedback?: string | null
  retry_count?: number
  max_retries?: number
  search_status?: string
}

export function QuarantineReviewView() {
  const [documents, setDocuments] = useState<QuarantineDocument[]>([])
  const [candidates, setCandidates] = useState<RegisteredCandidate[]>([])
  const [activeSectionTab, setActiveSectionTab] = useState<'candidates' | 'downloaded' | 'all'>('candidates')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const pendingCandidatesCount = candidates.filter(
    (c) => !c.is_downloaded && c.status !== 'rejected'
  ).length

  // Modal de revisión
  const [selectedDoc, setSelectedDoc] = useState<QuarantineDocument | null>(null)
  const [decision, setDecision] = useState<'approved_for_context' | 'rejected' | 'pending_context_review'>(
    'pending_context_review'
  )
  const [reviewerId, setReviewerId] = useState('investigador_ebdi_01')
  const [reviewNotes, setReviewNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Modal de Descarte con Retroalimentación Adaptativa HITL
  const [rejectingCandidate, setRejectingCandidate] = useState<RegisteredCandidate | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [rejectRequestSearch, setRejectRequestSearch] = useState(true)
  const [rejectInstruction, setRejectInstruction] = useState('')
  const [submittingReject, setSubmittingReject] = useState(false)

  // Modal de visualización y extracción de Creencias eBDI
  const [beliefsDoc, setBeliefsDoc] = useState<QuarantineDocument | null>(null)
  const [beliefsData, setBeliefsData] = useState<TerritorialBeliefExtractionResult | null>(null)
  const [loadingBeliefs, setLoadingBeliefs] = useState(false)
  // Estados para barra de progreso y telemetría de extracción
  const [extractingBeliefs, setExtractingBeliefs] = useState(false)
  const [extractionProgress, setExtractionProgress] = useState(0)
  const [extractionElapsed, setExtractionElapsed] = useState(0)
  const [extractionPhase, setExtractionPhase] = useState<1 | 2 | 3 | 4>(1)
  const [extractionStageText, setExtractionStageText] = useState('')
  const [beliefsError, setBeliefsError] = useState<string | null>(null)

  // Estados de Adquisición y Candidatos HITL
  const [acquiringId, setAcquiringId] = useState<string | null>(null)

  // Modal de Carga Manual de PDF
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadTitle, setUploadTitle] = useState('')
  const [uploadEntity, setUploadEntity] = useState('')
  const [uploadScope, setUploadScope] = useState('Montes de María')
  const [uploadInstrument, setUploadInstrument] = useState('PDM')
  const [uploadReviewer, setUploadReviewer] = useState('investigador_ebdi_01')
  const [uploading, setUploading] = useState(false)

  // Panel de Semillas Autorizadas para Rastreo
  const [showSeedsPanel, setShowSeedsPanel] = useState(false)
  const [seeds, setSeeds] = useState<AuthorizedSeed[]>([])
  const [loadingSeeds, setLoadingSeeds] = useState(false)
  const [scanningSeeds, setScanningSeeds] = useState(false)
  const [newSeedUrl, setNewSeedUrl] = useState('')
  const [newSeedEntity, setNewSeedEntity] = useState('')
  const [newSeedTitle, setNewSeedTitle] = useState('')
  const [newSeedScope, setNewSeedScope] = useState('Montes de María')
  const [newSeedInstrument, setNewSeedInstrument] = useState('PDM')
  const [addingSeed, setAddingSeed] = useState(false)

  const handleOpenBeliefs = async (doc: QuarantineDocument) => {
    setBeliefsDoc(doc)
    setBeliefsData(null)
    setBeliefsError(null)
    setLoadingBeliefs(true)
    try {
      const res = await fetch(`${API_BASE}/atlas/artifacts/${doc.source_id}/beliefs`)
      if (res.ok) {
        const data = await res.json()
        setBeliefsData(data)
      } else if (res.status === 404) {
        setBeliefsData(null)
      } else {
        const errJson = await res.json().catch(() => ({}))
        setBeliefsError(errJson.detail || `HTTP ${res.status}`)
      }
    } catch (err: any) {
      setBeliefsError(err.message)
    } finally {
      setLoadingBeliefs(false)
    }
  }

  const handleRunExtraction = async (sourceId: string) => {
    setExtractingBeliefs(true)
    setExtractionProgress(5)
    setExtractionElapsed(0)
    setExtractionPhase(1)
    setExtractionStageText('Iniciando tarea de extracción soberana en segundo plano...')
    setBeliefsError(null)

    const startTime = Date.now()
    const timer = setInterval(() => {
      const elapsedSec = Math.floor((Date.now() - startTime) / 1000)
      setExtractionElapsed(elapsedSec)
    }, 500)

    try {
      const res = await fetch(`${API_BASE}/atlas/artifacts/${sourceId}/extract-beliefs?force_reextract=true`, {
        method: 'POST',
      })
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || `HTTP ${res.status}`)
      }

      if (res.status === 202) {
        // Modo asíncrono desacoplado: sondeo de telemetría en tiempo real
        let completed = false
        let attempts = 0
        const maxAttempts = 180 // Máximo 6 minutos de sondeo cada 2 segundos

        while (!completed && attempts < maxAttempts) {
          await new Promise((r) => setTimeout(r, 2000))
          attempts++

          const statusRes = await fetch(`${API_BASE}/atlas/artifacts/${sourceId}/extraction-status`)
          if (!statusRes.ok) continue
          const jobData = await statusRes.json()

          if (jobData.progress_percent > 0) {
            setExtractionProgress(jobData.progress_percent)
          }

          if (jobData.current_chunk > 0 && jobData.total_chunks > 0) {
            setExtractionPhase(2)
            setExtractionStageText(`Inferencia soberana en gemma4:e4b: Fragmento ${jobData.current_chunk} de ${jobData.total_chunks}...`)
          } else if (jobData.message) {
            setExtractionStageText(jobData.message)
          }

          if (jobData.status === 'completed' && jobData.result) {
            completed = true
            setExtractionPhase(4)
            setExtractionStageText('Extracción completada con éxito. Consolidando artefacto territorial...')
            setExtractionProgress(100)
            await new Promise((r) => setTimeout(r, 600))
            setBeliefsData(jobData.result)
            break
          }

          if (jobData.status === 'failed') {
            throw new Error(jobData.error || jobData.message || 'La extracción en segundo plano falló.')
          }
        }

        if (!completed && attempts >= maxAttempts) {
          throw new Error('Tiempo límite de espera superado durante la extracción en segundo plano.')
        }
      } else {
        const data: TerritorialBeliefExtractionResult = await res.json()
        setExtractionPhase(4)
        setExtractionStageText('Extracción completada con éxito. Consolidando artefacto territorial...')
        setExtractionProgress(100)
        await new Promise((r) => setTimeout(r, 600))
        setBeliefsData(data)
      }
    } catch (err: any) {
      setBeliefsError(err.name === 'TypeError' ? 'Error de conexión: No se pudo comunicar con el servidor API.' : `Error extrayendo creencias: ${err.message}`)
    } finally {
      clearInterval(timer)
      setExtractingBeliefs(false)
    }
  }

  const [viewJsonBeliefId, setViewJsonBeliefId] = useState<string | null>(null)
  const [copiedBeliefId, setCopiedBeliefId] = useState<string | null>(null)
  const [curatingBeliefId, setCuratingBeliefId] = useState<string | null>(null)
  const [ocrRunning, setOcrRunning] = useState(false)
  const [ocrMessage, setOcrMessage] = useState<string | null>(null)

  // Estado para Edición Humana Granular (Modo Amigable / JSON)
  const [editingBelief, setEditingBelief] = useState<TerritorialBeliefItem | null>(null)
  const [editTab, setEditTab] = useState<'friendly' | 'json'>('friendly')
  const [editJsonStr, setEditJsonStr] = useState<string>('')
  const [savingEdit, setSavingEdit] = useState<boolean>(false)
  const [editError, setEditError] = useState<string | null>(null)

  // Estado para Compilación a YAML
  const [compilingYaml, setCompilingYaml] = useState<boolean>(false)
  const [compiledYamlResult, setCompiledYamlResult] = useState<any | null>(null)
  const [showYamlViewer, setShowYamlViewer] = useState<boolean>(false)
  const [activeYamlTab, setActiveYamlTab] = useState<'goals' | 'plans'>('goals')
  const [copiedYamlId, setCopiedYamlId] = useState<string | null>(null)

  const handleStartEdit = (belief: TerritorialBeliefItem) => {
    setEditingBelief({ ...belief })
    setEditJsonStr(JSON.stringify(belief, null, 2))
    setEditTab('friendly')
    setEditError(null)
  }

  const handleSaveEdit = async () => {
    if (!editingBelief || !beliefsDoc) return
    setSavingEdit(true)
    setEditError(null)
    try {
      let payloadToSave: any = {}
      if (editTab === 'json') {
        try {
          const parsed = JSON.parse(editJsonStr)
          payloadToSave = {
            editor_id: reviewerId || 'investigador_ebdi_01',
            topic: parsed.topic,
            trigger_condition: parsed.trigger_condition,
            executable_action: parsed.executable_action,
            action_operation_type: parsed.action_operation_type,
            behavioral_effect: parsed.behavioral_effect,
            activation_rule_template: parsed.activation_rule_template,
            raw_excerpt: parsed.raw_excerpt,
            ebdi_belief_assertion: parsed.ebdi_belief_assertion,
            target_municipalities: parsed.target_municipalities,
            confidence: parsed.confidence,
            edit_notes: 'Edición en modo JSON crudo por investigador',
          }
        } catch (jsonErr: any) {
          throw new Error(`JSON inválido: ${jsonErr.message}`)
        }
      } else {
        payloadToSave = {
          editor_id: reviewerId || 'investigador_ebdi_01',
          topic: editingBelief.topic,
          trigger_condition: editingBelief.trigger_condition,
          executable_action: editingBelief.executable_action,
          action_operation_type: editingBelief.action_operation_type,
          behavioral_effect: editingBelief.behavioral_effect,
          activation_rule_template: editingBelief.activation_rule_template,
          raw_excerpt: editingBelief.raw_excerpt,
          ebdi_belief_assertion: editingBelief.ebdi_belief_assertion,
          target_municipalities: editingBelief.target_municipalities,
          confidence: editingBelief.confidence,
          edit_notes: 'Edición en modo amigable por investigador',
        }
      }

      const res = await fetch(
        `${API_BASE}/atlas/artifacts/${beliefsDoc.source_id}/beliefs/${editingBelief.belief_id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payloadToSave),
        }
      )
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || `HTTP ${res.status}`)
      }
      const updatedBelief: TerritorialBeliefItem = await res.json()
      setBeliefsData((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          beliefs: prev.beliefs.map((b) => (b.belief_id === updatedBelief.belief_id ? updatedBelief : b)),
        }
      })
      setEditingBelief(null)
    } catch (err: any) {
      setEditError(err.message)
    } finally {
      setSavingEdit(false)
    }
  }

  const handleCompileYamls = async (sourceId: string) => {
    setCompilingYaml(true)
    setBeliefsError(null)
    try {
      const res = await fetch(`${API_BASE}/atlas/artifacts/${sourceId}/compile-yaml`, {
        method: 'POST',
      })
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || `HTTP ${res.status}`)
      }
      const report = await res.json()
      setCompiledYamlResult(report)
      setShowYamlViewer(true)
    } catch (err: any) {
      setBeliefsError(`Error compilando a YAML: ${err.message}`)
    } finally {
      setCompilingYaml(false)
    }
  }

  const handleCurateBelief = async (
    sourceId: string,
    beliefId: string,
    curationDecision: 'admitted_ebdi' | 'dismissed_noise' | 'pending',
    notes = ''
  ) => {
    setCuratingBeliefId(beliefId)
    try {
      const res = await fetch(`${API_BASE}/atlas/artifacts/${sourceId}/beliefs/${beliefId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: curationDecision,
          curator_id: reviewerId || 'investigador_ebdi_01',
          notes: notes || `Curación manual del investigador: ${curationDecision}`,
        }),
      })
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || `HTTP ${res.status}`)
      }
      const updatedBelief: TerritorialBeliefItem = await res.json()
      setBeliefsData((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          beliefs: prev.beliefs.map((b) => (b.belief_id === beliefId ? updatedBelief : b)),
        }
      })
    } catch (err: any) {
      setBeliefsError(`Error curando creencia: ${err.message}`)
    } finally {
      setCuratingBeliefId(null)
    }
  }

  const handleRunOcr = async (sourceId: string) => {
    setOcrRunning(true)
    setOcrMessage(null)
    try {
      const res = await fetch(`${API_BASE}/atlas/artifacts/${sourceId}/ocr`, {
        method: 'POST',
      })
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setOcrMessage(`OCR completado con éxito: ${data.characters_extracted.toLocaleString()} caracteres extraídos.`)
      // Refrescar creencias tras OCR
      await handleRunExtraction(sourceId)
    } catch (err: any) {
      setBeliefsError(`Error en OCR local: ${err.message}`)
    } finally {
      setOcrRunning(false)
    }
  }

  const handleCopyJson = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedBeliefId(id)
    setTimeout(() => setCopiedBeliefId(null), 2000)
  }

  const fetchArtifacts = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/atlas/artifacts/quarantine`)
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }
      const data = await res.json()
      setDocuments(data.documents || [])
      setCandidates(data.registered_candidates || [])
    } catch (err: any) {
      setError(`No se pudieron cargar los artefactos del servidor local: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const fetchSeeds = async () => {
    setLoadingSeeds(true)
    try {
      const res = await fetch(`${API_BASE}/atlas/seeds`)
      if (res.ok) {
        const data = await res.json()
        setSeeds(data.seeds || [])
      }
    } catch {
      // Ignorar error silenciosamente
    } finally {
      setLoadingSeeds(false)
    }
  }

  useEffect(() => {
    fetchArtifacts()
    fetchSeeds()
  }, [])

  const handleAddSeed = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSeedUrl.trim()) return
    setAddingSeed(true)
    try {
      const res = await fetch(`${API_BASE}/atlas/seeds`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: newSeedUrl.trim(),
          entity: newSeedEntity.trim() || 'Entidad Oficial Territorial',
          title: newSeedTitle.trim() || 'Instrumento Territorial',
          territory_scope: newSeedScope.trim() || 'Montes de María',
          instrument_type: newSeedInstrument,
          added_by: 'investigador_ebdi_01',
        }),
      })
      if (res.ok) {
        setNewSeedUrl('')
        setNewSeedEntity('')
        setNewSeedTitle('')
        fetchSeeds()
        setFeedback({
          type: 'success',
          message: 'Semilla oficial de rastreo autorizada registrada exitosamente.',
        })
      } else {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Error registrando semilla')
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message })
    } finally {
      setAddingSeed(false)
    }
  }

  const handleDeleteSeed = async (seedId: string) => {
    try {
      const res = await fetch(`${API_BASE}/atlas/seeds/${seedId}`, { method: 'DELETE' })
      if (res.ok) {
        fetchSeeds()
        setFeedback({ type: 'success', message: 'Semilla eliminada.' })
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message })
    }
  }

  const handleScanSeeds = async () => {
    setScanningSeeds(true)
    try {
      const res = await fetch(`${API_BASE}/atlas/seeds/scan`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        fetchArtifacts()
        setFeedback({
          type: 'success',
          message: `Rastreo completado: ${data.count} fuentes propuestas para validación humana (cero auto-aprobación).`,
        })
      } else {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Error escaneando semillas')
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message })
    } finally {
      setScanningSeeds(false)
    }
  }

  const handleApproveAndAcquireCandidate = async (cand: RegisteredCandidate) => {
    setAcquiringId(cand.source_id)
    try {
      if (cand.status !== 'approved_for_acquisition') {
        const revRes = await fetch(`${API_BASE}/atlas/candidates/review`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_id: cand.source_id,
            reviewer_id: 'investigador_ebdi_01',
            decision: 'approve',
            review_notes: 'Aprobado formalmente tras inspección humana del enlace oficial.',
          }),
        })
        if (!revRes.ok && revRes.status !== 409) {
          const err = await revRes.json().catch(() => ({}))
          throw new Error(err.detail || 'Error al autorizar candidato')
        }
      }

      const acqRes = await fetch(`${API_BASE}/atlas/acquire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: cand.source_id,
          requester_id: 'investigador_ebdi_01',
        }),
      })

      if (!acqRes.ok) {
        const err = await acqRes.json().catch(() => ({}))
        throw new Error(err.detail || `Error en descarga: HTTP ${acqRes.status}`)
      }

      setFeedback({
        type: 'success',
        message: `Documento '${cand.title}' adquirido exitosamente al almacenamiento local soberano.`,
      })
      fetchArtifacts()
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Fallo adquiriendo candidato: ${err.message}` })
    } finally {
      setAcquiringId(null)
    }
  }

  const handleOpenRejectModal = (cand: RegisteredCandidate) => {
    setRejectingCandidate(cand)
    setRejectReason('')
    setRejectRequestSearch(true)
    setRejectInstruction('')
  }

  const handleSubmitRejectFeedback = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!rejectingCandidate) return
    if (!rejectReason.trim()) {
      setFeedback({ type: 'error', message: 'El motivo del descarte es obligatorio (mínimo 5 caracteres).' })
      return
    }

    setSubmittingReject(true)
    try {
      const revRes = await fetch(`${API_BASE}/atlas/candidates/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: rejectingCandidate.source_id,
          reviewer_id: reviewerId || 'investigador_ebdi_01',
          decision: 'reject',
          review_notes: rejectReason.trim(),
          request_alternative_search: rejectRequestSearch,
          instruction_feedback: rejectInstruction.trim() || undefined,
        }),
      })

      if (!revRes.ok) {
        const err = await revRes.json().catch(() => ({}))
        throw new Error(err.detail || 'Error al descartar candidato')
      }

      const reviewData = await revRes.json()
      const msg = reviewData.adaptive_message || `Candidato '${rejectingCandidate.title}' descartado exitosamente.`
      setFeedback({ type: 'success', message: msg })
      setRejectingCandidate(null)
      fetchArtifacts()
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Error procesando descarte: ${err.message}` })
    } finally {
      setSubmittingReject(false)
    }
  }

  const handleUploadFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadFile) return
    setUploading(true)

    try {
      const reader = new FileReader()
      const base64Promise = new Promise<string>((resolve, reject) => {
        reader.onload = () => resolve(reader.result as string)
        reader.onerror = reject
      })
      reader.readAsDataURL(uploadFile)
      const b64 = await base64Promise

      const res = await fetch(`${API_BASE}/atlas/artifacts/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: uploadFile.name,
          file_base64: b64,
          title: uploadTitle.trim() || undefined,
          entity: uploadEntity.trim() || undefined,
          territory_scope: uploadScope.trim() || 'Montes de María',
          instrument_type: uploadInstrument,
          reviewer_id: uploadReviewer.trim() || 'investigador_ebdi_01',
        }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const created = await res.json()
      setFeedback({
        type: 'success',
        message: `Documento '${created.title}' (${created.source_id}) cargado exitosamente a cuarentena con SHA-256 verificado.`,
      })
      setShowUploadModal(false)
      setUploadFile(null)
      setUploadTitle('')
      setUploadEntity('')
      fetchArtifacts()
    } catch (err: any) {
      setFeedback({ type: 'error', message: `Error al cargar documento: ${err.message}` })
    } finally {
      setUploading(false)
    }
  }

  const handleOpenReview = (doc: QuarantineDocument) => {
    setSelectedDoc(doc)
    setDecision(
      (doc.status as any) === 'approved_for_context' || (doc.status as any) === 'rejected'
        ? (doc.status as any)
        : 'pending_context_review'
    )
    setReviewerId(doc.reviewer_id || 'investigador_ebdi_01')
    setReviewNotes('')
    setFeedback(null)
  }

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDoc) return

    if (!reviewerId.trim() || !reviewNotes.trim()) {
      setFeedback({
        type: 'error',
        message: 'El identificador del revisor y las notas de revisión son obligatorios.',
      })
      return
    }

    setSubmitting(true)
    setFeedback(null)

    try {
      const res = await fetch(`${API_BASE}/atlas/artifacts/context-review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_id: selectedDoc.source_id,
          reviewer_id: reviewerId.trim(),
          decision: decision,
          review_notes: reviewNotes.trim(),
        }),
      })

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}))
        throw new Error(errJson.detail || `HTTP ${res.status}`)
      }

      const updatedRecord: QuarantineDocument = await res.json()
      setFeedback({
        type: 'success',
        message: `Decisión registrada exitosamente para '${updatedRecord.source_id}': nuevo estado '${updatedRecord.status}'.`,
      })
      setSelectedDoc(null)
      fetchArtifacts()
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: `Error al registrar la revisión: ${err.message}`,
      })
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'approved_for_context':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#34c759]/15 text-[#248a3d] border border-[#34c759]/30">
            <CheckCircle2 className="w-3.5 h-3.5" /> Aprobado para Contexto
          </span>
        )
      case 'rejected':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#ff3b30]/15 text-[#d70015] border border-[#ff3b30]/30">
            <XCircle className="w-3.5 h-3.5" /> Rechazado
          </span>
        )
      case 'revised_2026':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#5856d6]/15 text-[#5856d6] border border-[#5856d6]/30">
            <Clock className="w-3.5 h-3.5" /> Candidato 2026 (No Descargado)
          </span>
        )
      case 'pending_context_review':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#ff9500]/15 text-[#b25000] border border-[#ff9500]/30">
            <Clock className="w-3.5 h-3.5" /> En Cuarentena (Pendiente Revisión)
          </span>
        )
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Banner de Soberanía y Gobernanza Dinámica */}
      <div className="bg-[#0066cc]/[0.05] p-5 rounded-2xl border border-[#0066cc]/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <ShieldCheck className="w-6 h-6 text-[#0066cc] shrink-0 mt-0.5" />
          <div className="flex flex-col gap-1">
            <span className="text-sm font-semibold text-[#1d1d1f]">
              Revisión Contextual Humana y Gobernanza Criptográfica (AT-1)
            </span>
            <p className="text-xs text-[#6e6e73] leading-relaxed max-w-3xl">
              <strong>Gobernanza Dinámica:</strong> Mientras un artefacto permanezca en cuarentena preventiva (pendiente de revisión o rechazado),
              los motores están estrictamente bloqueados (<span className="font-mono text-red-600 font-semibold">Gemma: BLOQUEADO</span>, <span className="font-mono text-red-600 font-semibold">OCR: BLOQUEADO</span>).
              Una vez <span className="font-semibold text-[#248a3d]">Aprobado para Contexto</span> por un investigador humano,
              el micro-LLM <strong>gemma4:e4b</strong> y el OCR local se <span className="font-semibold text-[#0066cc]">desbloquean soberanamente</span> para extracción estructurada y curación granular eBDI.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#0066cc] text-white hover:bg-[#0052a3] shadow-xs transition-all cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            Cargar PDF Manualmente
          </button>
          <button
            type="button"
            onClick={() => setShowSeedsPanel(!showSeedsPanel)}
            className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
              showSeedsPanel
                ? 'bg-[#5856d6] text-white border-[#5856d6]'
                : 'bg-white border-black/[0.08] text-[#1d1d1f] hover:bg-gray-50'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            Semillas Autorizadas ({seeds.length})
          </button>
          <button
            type="button"
            onClick={() => {
              fetchArtifacts()
              fetchSeeds()
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-black/[0.08] text-[#1d1d1f] hover:bg-gray-50 shadow-xs cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>
      </div>

      {/* Panel Desplegable de Semillas Autorizadas para Rastreo */}
      {showSeedsPanel && (
        <div className="bg-white p-5 rounded-2xl border border-[#5856d6]/30 shadow-sm flex flex-col gap-4 animate-in fade-in duration-150">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-black/[0.06]">
            <div>
              <h3 className="text-sm font-semibold text-[#1d1d1f] flex items-center gap-2">
                <Globe className="w-4 h-4 text-[#5856d6]" />
                Enlaces y Repositorios Institucionales Autorizados para Rastreo
              </h3>
              <p className="text-xs text-[#6e6e73] mt-0.5">
                Defina los dominios o enlaces oficiales donde el agente está autorizado a buscar documentos. Los documentos descubiertos requerirán validación humana previa antes de su incorporación.
              </p>
            </div>
            <button
              type="button"
              onClick={handleScanSeeds}
              disabled={scanningSeeds}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#5856d6] text-white hover:bg-[#4846c4] shadow-xs transition-all disabled:opacity-50 shrink-0 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${scanningSeeds ? 'animate-spin' : ''}`} />
              {scanningSeeds ? 'Rastreando semillas...' : 'Escanear Semillas Ahora'}
            </button>
          </div>

          {/* Formulario para registrar nueva semilla */}
          <form onSubmit={handleAddSeed} className="grid grid-cols-1 md:grid-cols-6 gap-2.5 bg-[#fafafc] p-3.5 rounded-xl border border-black/[0.06] text-xs">
            <div className="md:col-span-2 flex flex-col gap-1">
              <label className="font-semibold text-[#1d1d1f]">URL Semilla Oficial (.gov.co):</label>
              <input
                type="url"
                value={newSeedUrl}
                onChange={(e) => setNewSeedUrl(e.target.value)}
                placeholder="https://www.renovacionterritorio.gov.co/..."
                required
                className="px-3 py-2 rounded-lg border border-black/[0.1] bg-white focus:outline-none focus:border-[#5856d6]"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="font-semibold text-[#1d1d1f]">Entidad:</label>
              <input
                type="text"
                value={newSeedEntity}
                onChange={(e) => setNewSeedEntity(e.target.value)}
                placeholder="ej. ART, ADR, Alcaldía"
                className="px-3 py-2 rounded-lg border border-black/[0.1] bg-white focus:outline-none focus:border-[#5856d6]"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="font-semibold text-[#1d1d1f]">Instrumento:</label>
              <select
                value={newSeedInstrument}
                onChange={(e) => setNewSeedInstrument(e.target.value)}
                className="px-3 py-2 rounded-lg border border-black/[0.1] bg-white focus:outline-none focus:border-[#5856d6]"
              >
                <option value="PDM">PDM</option>
                <option value="PDT">PDT</option>
                <option value="PATR">PATR</option>
                <option value="PIDARET">PIDARET</option>
                <option value="OTRO">Otro</option>
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="font-semibold text-[#1d1d1f]">Ámbito Territorial:</label>
              <input
                type="text"
                value={newSeedScope}
                onChange={(e) => setNewSeedScope(e.target.value)}
                placeholder="ej. Montes de María"
                className="px-3 py-2 rounded-lg border border-black/[0.1] bg-white focus:outline-none focus:border-[#5856d6]"
              />
            </div>
            <div className="flex flex-col justify-end">
              <button
                type="submit"
                disabled={addingSeed || !newSeedUrl.trim()}
                className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold bg-[#1d1d1f] text-white hover:bg-black shadow-xs transition-all disabled:opacity-50 cursor-pointer h-[34px]"
              >
                <Plus className="w-3.5 h-3.5" />
                {addingSeed ? 'Guardando...' : 'Autorizar'}
              </button>
            </div>
          </form>

          {/* Lista de semillas activas */}
          <div className="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
            {loadingSeeds ? (
              <p className="text-xs text-[#86868b] italic py-2 flex items-center gap-1.5">
                <RefreshCw className="w-3 h-3 animate-spin" /> Cargando semillas autorizadas...
              </p>
            ) : seeds.length === 0 ? (
              <p className="text-xs text-[#86868b] italic py-2">No hay semillas adicionales registradas.</p>
            ) : (
              seeds.map((s) => (
                <div
                  key={s.seed_id}
                  className="flex items-center justify-between gap-3 p-2.5 rounded-lg border border-black/[0.05] bg-white hover:bg-gray-50 text-xs"
                >
                  <div className="flex flex-col gap-0.5 truncate">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-[#1d1d1f]">{s.title || s.seed_id}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-black/[0.05] text-gray-600 font-mono">
                        {s.instrument_type}
                      </span>
                      <span className="text-[11px] text-[#5856d6] font-medium">{s.territory_scope}</span>
                    </div>
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#0066cc] hover:underline font-mono text-[11px] truncate flex items-center gap-1"
                    >
                      <ExternalLink className="w-3 h-3 shrink-0" />
                      <span className="truncate">{s.url}</span>
                    </a>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteSeed(s.seed_id)}
                    className="p-1.5 rounded-md text-red-500 hover:bg-red-50 hover:text-red-700 transition-colors shrink-0 cursor-pointer"
                    title="Eliminar semilla"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center gap-2 border ${
            feedback.type === 'success'
              ? 'bg-[#34c759]/10 text-[#248a3d] border-[#34c759]/30'
              : 'bg-[#ff3b30]/10 text-[#d70015] border-[#ff3b30]/30'
          }`}
        >
          {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
          <span>{feedback.message}</span>
        </div>
      )}

      {error && (
        <div className="bg-[#ff3b30]/10 p-4 rounded-xl border border-[#ff3b30]/20 text-xs text-[#d70015] flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Selector de Sub-Navegación de Cuarentena (Sticky debajo de las pestañas principales) */}
      <div className="sticky top-[162px] z-20 bg-white/95 backdrop-blur-md p-2.5 rounded-2xl border border-black/[0.08] shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all">
        <div className="bg-[#f5f5f7] p-1 rounded-xl border border-black/[0.04] inline-flex items-center gap-1 flex-wrap">
          <button
            type="button"
            onClick={() => setActiveSectionTab('candidates')}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSectionTab === 'candidates'
                ? 'bg-white text-[#1d1d1f] shadow-xs'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <Layers className={`w-3.5 h-3.5 ${activeSectionTab === 'candidates' ? 'text-[#5856d6]' : 'text-gray-400'}`} />
            <span>Candidatos para Validación</span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                pendingCandidatesCount > 0
                  ? 'bg-[#5856d6] text-white'
                  : 'bg-black/[0.06] text-[#6e6e73]'
              }`}
            >
              {candidates.length}
            </span>
            {pendingCandidatesCount > 0 && (
              <span className="text-[10px] text-amber-800 font-semibold bg-amber-100 px-1.5 py-0.5 rounded-md">
                {pendingCandidatesCount} por revisar
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveSectionTab('downloaded')}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSectionTab === 'downloaded'
                ? 'bg-white text-[#1d1d1f] shadow-xs'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <Database className={`w-3.5 h-3.5 ${activeSectionTab === 'downloaded' ? 'text-[#0066cc]' : 'text-gray-400'}`} />
            <span>Artefactos en Cuarentena Descargados</span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                activeSectionTab === 'downloaded'
                  ? 'bg-[#0066cc] text-white'
                  : 'bg-black/[0.06] text-[#6e6e73]'
              }`}
            >
              {documents.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveSectionTab('all')}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSectionTab === 'all'
                ? 'bg-white text-[#1d1d1f] shadow-xs'
                : 'text-[#6e6e73] hover:text-[#1d1d1f]'
            }`}
          >
            <span>Ver Ambos</span>
          </button>
        </div>

        <div className="text-[11px] text-[#6e6e73] flex items-center gap-2 px-2">
          <span>
            {activeSectionTab === 'candidates'
              ? 'Enfoque HITL: Audite justificativos del agente y decida adquisición o descarte.'
              : activeSectionTab === 'downloaded'
              ? 'Inspección de artefactos locales descargados con hash criptográfico SHA-256.'
              : 'Vista consolidada simultánea de candidatos y artefactos adquiridos.'}
          </span>
        </div>
      </div>

      {/* Sección 1: Candidatos Oficiales y Descubiertos para Validación Humana (HITL) */}
      {(activeSectionTab === 'candidates' || activeSectionTab === 'all') && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-1 border-b border-black/[0.06]">
            <div>
              <h3 className="text-sm font-semibold text-[#1d1d1f] flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#5856d6]" />
                Candidatos Oficiales y Descubiertos para Validación Humana ({candidates.length})
              </h3>
              <p className="text-[11px] text-[#6e6e73]">
                Human-in-the-Loop: Ningún documento se adquiere automáticamente. Haga clic en el enlace para verificar el documento oficial y decida si aprueba la adquisición al almacenamiento local soberano o lo descarta.
              </p>
            </div>
            <span className="text-[11px] text-[#5856d6] font-semibold bg-[#5856d6]/10 px-2.5 py-1 rounded-full shrink-0">
              Validación Humana Obligatoria
            </span>
          </div>

          {candidates.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl border border-dashed border-black/[0.1] text-center flex flex-col items-center justify-center gap-3">
              <Layers className="w-8 h-8 text-gray-300" />
              <div className="flex flex-col gap-1 max-w-md">
                <span className="font-semibold text-sm text-[#1d1d1f]">No hay candidatos registrados para validación</span>
                <p className="text-xs text-[#6e6e73]">
                  Actualmente no se han descubierto nuevos candidatos para validación humana. Puede registrar nuevas URLs o repositorios semilla arriba o cargar un documento PDF directamente.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {candidates.map((cand) => (
                <div
                  key={cand.source_id}
                  className="bg-white p-4 rounded-xl border border-[#5856d6]/25 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs"
                >
                  <div className="flex flex-col gap-1 max-w-2xl flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono font-bold text-[#5856d6] bg-[#5856d6]/10 px-2 py-0.5 rounded">
                        {cand.source_id}
                      </span>
                      {getStatusBadge(cand.status)}
                      <span className="text-gray-500 font-medium">({cand.instrument_type})</span>
                      <span className="text-gray-400 text-[11px]">{cand.territory_scope}</span>
                      {cand.retry_count && cand.retry_count > 0 ? (
                        <span className="text-[10px] font-semibold text-[#5856d6] bg-[#5856d6]/10 px-2 py-0.5 rounded border border-[#5856d6]/25">
                          Intento {cand.retry_count}/6
                        </span>
                      ) : null}
                    </div>
                    <span className="font-medium text-[#1d1d1f] text-sm">{cand.title}</span>
                    <span className="text-gray-500 text-[11px]">{cand.entity}</span>

                    {/* Justificación Técnica del Agente de por qué seleccionó este documento */}
                    <div className="bg-[#5856d6]/[0.05] p-2.5 rounded-lg border border-[#5856d6]/20 flex flex-col gap-1 mt-1">
                      <span className="text-[10px] font-bold text-[#5856d6] uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3 h-3" /> Justificación del Agente para Selección:
                      </span>
                      <p className="text-[#1d1d1f] text-[11px] leading-relaxed">
                        {cand.selection_reason || 'Fuente oficial institucional con cobertura territorial compatible.'}
                      </p>
                    </div>

                    {/* Alerta de agotamiento de intentos adaptativos */}
                    {cand.search_status === 'exhausted_no_alternative' && (
                      <div className="bg-amber-50 p-2 rounded-lg border border-amber-200 mt-1 flex items-center gap-1.5 text-amber-900 text-[11px]">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                        <span>El agente agotó los 6 intentos de búsqueda adaptativa sin hallar alternativas no redundantes. Sugerencia: cargue el PDF manualmente o agregue una nueva semilla oficial.</span>
                      </div>
                    )}

                    {/* Motivo de descarte previo si ya fue revisado */}
                    {cand.status === 'rejected' && cand.review_notes && (
                      <div className="bg-red-50 p-2 rounded-lg border border-red-200 mt-1">
                        <span className="text-[10px] font-bold text-red-700 uppercase">Motivo del Descarte Humano:</span>
                        <p className="text-red-900 text-[11px] mt-0.5">{cand.review_notes}</p>
                        {cand.instruction_feedback && (
                          <p className="text-red-700 text-[10px] mt-0.5 italic">
                            Indicación dada al agente: "{cand.instruction_feedback}"
                          </p>
                        )}
                      </div>
                    )}

                    {/* Enlace auditable oficial */}
                    {cand.canonical_url ? (
                      <div className="flex items-center gap-2 mt-1">
                        <a
                          href={cand.canonical_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-[#0066cc] hover:text-[#004499] hover:underline font-mono text-[11px] bg-[#0066cc]/5 px-2.5 py-1 rounded-md border border-[#0066cc]/20 transition-all cursor-pointer"
                          title="Abrir en pestaña nueva para validar contenido"
                        >
                          <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                          <span>Inspeccionar Documento Oficial</span>
                        </a>
                        <span className="text-[#86868b] text-[10px] font-mono truncate max-w-xs">{cand.canonical_url}</span>
                      </div>
                    ) : (
                      <span className="text-gray-400 italic text-[11px]">Sin URL canónica registrada</span>
                    )}
                  </div>

                  <div className="flex flex-row md:flex-col items-center md:items-end gap-2 shrink-0">
                    {cand.is_downloaded ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Adquirido en Cuarentena
                      </span>
                    ) : cand.status === 'rejected' ? (
                      <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-100 text-red-800 border border-red-300">
                        <XCircle className="w-3.5 h-3.5" /> Descartado por Revisor
                      </span>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleApproveAndAcquireCandidate(cand)}
                          disabled={acquiringId === cand.source_id}
                          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[#34c759] text-white hover:bg-[#2fb350] shadow-xs transition-all disabled:opacity-50 cursor-pointer"
                          title="Aprobar para adquisición y descargar al almacenamiento local de cuarentena"
                        >
                          {acquiringId === cand.source_id ? (
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          )}
                          <span>{acquiringId === cand.source_id ? 'Adquiriendo...' : 'Aprobar y Adquirir'}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleOpenRejectModal(cand)}
                          disabled={acquiringId === cand.source_id}
                          className="inline-flex items-center gap-1 px-2.5 py-2 rounded-xl text-xs font-semibold bg-white border border-red-300 text-red-600 hover:bg-red-50 transition-all disabled:opacity-50 cursor-pointer"
                          title="Descartar con retroalimentación para el agente"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Descartar</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sección 2: Lista de Artefactos en Cuarentena Descargados */}
      {(activeSectionTab === 'downloaded' || activeSectionTab === 'all') && (
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between pb-1 border-b border-black/[0.06]">
            <h3 className="text-sm font-semibold text-[#1d1d1f] flex items-center gap-2">
              <Database className="w-4 h-4 text-[#0066cc]" />
              Artefactos en Cuarentena Descargados ({documents.length})
            </h3>
            <span className="text-[11px] text-[#86868b]">
              Direccionados por SHA-256 en almacenamiento aislado fuera de Git
            </span>
          </div>

          {documents.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl border border-dashed border-black/[0.1] text-center flex flex-col items-center justify-center gap-3">
              <Database className="w-8 h-8 text-gray-300" />
              <div className="flex flex-col gap-1 max-w-md">
                <span className="font-semibold text-sm text-[#1d1d1f]">No hay artefactos en cuarentena descargados</span>
                <p className="text-xs text-[#6e6e73]">
                  Aún no se han descargado artefactos al almacenamiento local. Apruebe un candidato oficial o utilice el botón de carga manual de PDF arriba.
                </p>
              </div>
            </div>
          ) : (

        <div className="flex flex-col gap-4">
          {documents.map((doc) => (
            <div
              key={doc.source_id}
              className="bg-white p-5 rounded-2xl border border-black/[0.08] shadow-xs flex flex-col gap-4 hover:border-black/[0.15] transition-all"
            >
              {/* Encabezado del documento */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2.5 pb-3 border-b border-black/[0.05]">
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-mono text-xs font-bold text-[#0066cc] bg-[#0066cc]/[0.08] px-2 py-0.5 rounded-md">
                      {doc.source_id}
                    </span>
                    {getStatusBadge(doc.status)}
                    <span className="text-xs px-2 py-0.5 rounded-md bg-black/[0.04] text-[#1d1d1f] font-medium">
                      Tipo: {doc.instrument_type || 'N/A'}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-[#1d1d1f] mt-1">{doc.title}</h4>
                </div>
                <div className="flex items-center gap-2 shrink-0 flex-wrap">
                  <a
                    href={`${API_BASE}/atlas/artifacts/${doc.source_id}/content`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-[#1d1d1f] border border-black/[0.08] transition-all shadow-xs"
                    title="Inspeccionar el archivo PDF original almacenado en disco local"
                  >
                    <FileText className="w-4 h-4 text-[#0066cc]" />
                    <span>Ver PDF Local (100% Soberano)</span>
                  </a>
                  {doc.status === 'approved_for_context' && (
                    <button
                      type="button"
                      onClick={() => handleOpenBeliefs(doc)}
                      className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-[#248a3d] hover:bg-[#1f7835] text-white transition-all shadow-xs"
                      title="Ver o extraer creencias eBDI asistidas por gemma4:e4b"
                    >
                      <Brain className="w-4 h-4" />
                      <span>Creencias eBDI</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => handleOpenReview(doc)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-[#0066cc] text-white hover:bg-[#0055b3] transition-all shadow-xs"
                  >
                    <UserCheck className="w-4 h-4" />
                    Emitir Revisión Humana
                  </button>
                </div>
              </div>

              {/* Grilla completa con los 16 campos auditables */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">1. Entidad Oficial</span>
                  <span className="font-medium text-[#1d1d1f]">{doc.entity}</span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">2. Alcance Territorial</span>
                  <span className="font-medium text-[#1d1d1f]">{doc.territory_scope}</span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">3. ID Anterior (Relación)</span>
                  <span className="font-mono font-medium text-[#1d1d1f]">
                    {doc.previous_source_id || 'Ninguno (Directo)'}
                  </span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">4. Estado de Aprobación</span>
                  <span className="font-mono font-semibold text-[#1d1d1f]">{doc.approval_status}</span>
                </div>

                <div className="flex flex-col gap-1.5 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03] sm:col-span-2">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">5. Acceso y Verificación Documental</span>
                  <div className="flex flex-col gap-1.5">
                    <a
                      href={`${API_BASE}/atlas/artifacts/${doc.source_id}/content`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[#0066cc] hover:underline flex items-center gap-1.5 font-semibold text-xs"
                    >
                      <FileText className="w-3.5 h-3.5 shrink-0" />
                      <span>Abrir archivo en cuarentena local ({doc.source_id}.pdf)</span>
                    </a>
                    <div className="flex items-center gap-1 text-[11px] text-[#6e6e73] font-mono truncate">
                      <span className="text-[9px] uppercase font-bold text-[#86868b]">Web Externa:</span>
                      <a
                        href={doc.canonical_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-gray-600 hover:text-[#0066cc] hover:underline flex items-center gap-1 truncate"
                        title={doc.canonical_url}
                      >
                        <ExternalLink className="w-3 h-3 shrink-0" />
                        <span className="truncate">{doc.canonical_url}</span>
                      </a>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03] sm:col-span-2">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">6. Hash Criptográfico SHA-256</span>
                  <span className="font-mono text-[11px] text-[#1d1d1f] truncate select-all">{doc.sha256}</span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">7. Tamaño en Disco</span>
                  <span className="font-medium text-[#1d1d1f]">
                    {(doc.byte_size / (1024 * 1024)).toFixed(2)} MB ({doc.byte_size.toLocaleString()} B)
                  </span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">8. Allowed For Training</span>
                  <span className="font-mono font-bold text-[#248a3d]">
                    {String(doc.allowed_for_training)} (Estrictamente False)
                  </span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">9. Usage State</span>
                  <span className="font-mono font-bold text-[#1d1d1f]">{doc.usage_state}</span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03]">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">10. Revisor Asignado</span>
                  <span className="font-medium text-[#1d1d1f]">{doc.reviewer_id || 'Pendiente'}</span>
                  <span className="text-[10px] font-mono text-amber-700 font-semibold bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 self-start">
                    Modo: declarado, sin autenticación
                  </span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03] sm:col-span-2">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">11. Timestamp de Aprobación</span>
                  <span className="font-mono text-[#6e6e73]">{doc.approval_timestamp || 'Sin decisión'}</span>
                </div>

                <div className="flex flex-col gap-1 p-2.5 rounded-xl bg-[#fafafc] border border-black/[0.03] sm:col-span-2 lg:col-span-4">
                  <span className="text-[10px] uppercase font-bold text-[#86868b]">12. Notas y Traza Forense de Revisión</span>
                  <p className="text-[#6e6e73] leading-relaxed font-mono text-[11px] bg-white p-2 rounded-lg border border-black/[0.03] whitespace-pre-wrap">
                    {doc.approval_notes || 'Sin notas registradas.'}
                  </p>
                </div>

                {doc.review_events && doc.review_events.length > 0 && (
                  <div className="flex flex-col gap-1.5 p-3 rounded-xl bg-[#fafafc] border border-black/[0.03] sm:col-span-2 lg:col-span-4">
                    <span className="text-[10px] uppercase font-bold text-[#86868b]">
                      Historial Append-Only de Decisiones ({doc.review_events.length} eventos)
                    </span>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-[11px] border-collapse bg-white rounded-lg border border-black/[0.05]">
                        <thead>
                          <tr className="border-b border-black/[0.06] text-[#86868b] uppercase text-[9px] tracking-wider bg-gray-50">
                            <th className="py-1.5 px-2 font-semibold">Event ID</th>
                            <th className="py-1.5 px-2 font-semibold">Tipo</th>
                            <th className="py-1.5 px-2 font-semibold">Timestamp UTC</th>
                            <th className="py-1.5 px-2 font-semibold">Revisor</th>
                            <th className="py-1.5 px-2 font-semibold">Modo Autenticación</th>
                            <th className="py-1.5 px-2 font-semibold">Transición</th>
                            <th className="py-1.5 px-2 font-semibold">Notas</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-black/[0.04]">
                          {doc.review_events.map((ev) => (
                            <tr key={ev.event_id} className="hover:bg-gray-50/50">
                              <td className="py-1.5 px-2 font-mono text-[#0066cc] font-semibold">{ev.event_id}</td>
                              <td className="py-1.5 px-2">
                                {ev.event_type === 'test' ? (
                                  <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-gray-100 text-gray-600 border border-gray-300">
                                    PRUEBA TÉCNICA (NO APROBACIÓN)
                                  </span>
                                ) : (
                                  <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                    DECISIÓN HUMANA
                                  </span>
                                )}
                              </td>
                              <td className="py-1.5 px-2 font-mono text-[#6e6e73]">{ev.timestamp_utc}</td>
                              <td className="py-1.5 px-2 font-medium text-[#1d1d1f]">{ev.reviewer_id}</td>
                              <td className="py-1.5 px-2 text-amber-700 font-mono text-[10px]">{ev.reviewer_auth_mode}</td>
                              <td className="py-1.5 px-2 font-semibold">
                                <span className="font-mono text-[10px] text-gray-500">{ev.previous_status || 'init'}</span> →{' '}
                                <span className="font-mono text-[10px] text-[#0066cc]">{ev.decision}</span>
                              </td>
                              <td className="py-1.5 px-2 text-[#6e6e73] max-w-xs truncate">{ev.review_notes}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
          )}
        </div>
      )}

      {/* Modal de Carga Manual de Documento PDF */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-lg rounded-2xl border border-black/[0.1] shadow-2xl p-6 flex flex-col gap-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between pb-3 border-b border-black/[0.06]">
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#0066cc]">
                  Almacenamiento Local Soberano
                </span>
                <h3 className="text-base font-semibold text-[#1d1d1f]">Carga Manual de Documento PDF</h3>
                <span className="text-xs text-[#6e6e73]">
                  El archivo será validado (%PDF-), se calculará su SHA-256 e ingresará aprobado directamente a cuarentena.
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setShowUploadModal(false)
                  setUploadFile(null)
                }}
                className="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                aria-label="Cerrar modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUploadFileSubmit} className="flex flex-col gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="font-semibold text-[#1d1d1f]">Archivo PDF (*.pdf):</label>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  required
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      const f = e.target.files[0]
                      setUploadFile(f)
                      if (!uploadTitle) {
                        setUploadTitle(f.name.replace('.pdf', '').replace(/[-_]/g, ' '))
                      }
                    }
                  }}
                  className="px-3 py-2 rounded-xl border border-dashed border-black/[0.2] bg-[#fafafc] hover:bg-gray-50 cursor-pointer"
                />
                {uploadFile && (
                  <span className="text-[11px] text-gray-500 font-mono">
                    Seleccionado: {uploadFile.name} ({(uploadFile.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                )}
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-semibold text-[#1d1d1f]">Título del Instrumento:</label>
                <input
                  type="text"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                  placeholder="ej. Plan de Desarrollo Municipal 2024-2027"
                  required
                  className="px-3.5 py-2.5 rounded-xl border border-black/[0.1] focus:outline-none focus:border-[#0066cc]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="font-semibold text-[#1d1d1f]">Entidad Territorial:</label>
                  <input
                    type="text"
                    value={uploadEntity}
                    onChange={(e) => setUploadEntity(e.target.value)}
                    placeholder="ej. Alcaldía Municipal"
                    className="px-3.5 py-2.5 rounded-xl border border-black/[0.1] focus:outline-none focus:border-[#0066cc]"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="font-semibold text-[#1d1d1f]">Ámbito Territorial:</label>
                  <input
                    type="text"
                    value={uploadScope}
                    onChange={(e) => setUploadScope(e.target.value)}
                    placeholder="ej. Montes de María"
                    required
                    className="px-3.5 py-2.5 rounded-xl border border-black/[0.1] focus:outline-none focus:border-[#0066cc]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1.5">
                  <label className="font-semibold text-[#1d1d1f]">Tipo de Instrumento:</label>
                  <select
                    value={uploadInstrument}
                    onChange={(e) => setUploadInstrument(e.target.value)}
                    className="px-3.5 py-2.5 rounded-xl border border-black/[0.1] bg-white focus:outline-none focus:border-[#0066cc]"
                  >
                    <option value="PDM">PDM (Plan de Desarrollo Municipal)</option>
                    <option value="PDT">PDT (Plan de Desarrollo Territorial)</option>
                    <option value="PATR">PATR (Transformación Regional PDET)</option>
                    <option value="PIDARET">PIDARET (Desarrollo Rural Departamental)</option>
                    <option value="EOT">EOT (Esquema de Ordenamiento)</option>
                    <option value="POT">POT (Plan de Ordenamiento)</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="font-semibold text-[#1d1d1f]">Revisor Responsable:</label>
                  <input
                    type="text"
                    value={uploadReviewer}
                    onChange={(e) => setUploadReviewer(e.target.value)}
                    required
                    className="px-3.5 py-2.5 rounded-xl border border-black/[0.1] focus:outline-none focus:border-[#0066cc]"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-black/[0.06]">
                <button
                  type="button"
                  onClick={() => {
                    setShowUploadModal(false)
                    setUploadFile(null)
                  }}
                  className="px-4 py-2.5 rounded-xl font-semibold text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-gray-100 transition-colors cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="px-5 py-2.5 rounded-xl font-semibold bg-[#0066cc] text-white hover:bg-[#0052a3] shadow-xs transition-all disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                >
                  {uploading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <FileUp className="w-4 h-4" />}
                  <span>{uploading ? 'Cargando y Verificando...' : 'Cargar a Cuarentena'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Descarte y Retroalimentacion Adaptativa de Candidato */}
      {rejectingCandidate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-xl rounded-2xl border border-black/[0.1] shadow-2xl p-6 flex flex-col gap-4 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between pb-3 border-b border-black/[0.06]">
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#d97706]">
                  Retroalimentacion del Investigador
                </span>
                <h3 className="text-base font-semibold text-[#1d1d1f]">
                  Descartar Candidato y Guiar al Agente
                </h3>
                <span className="font-mono text-xs text-[#6e6e73]">{rejectingCandidate.source_id}</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setRejectingCandidate(null);
                  setRejectReason('');
                  setRejectInstruction('');
                  setRejectRequestSearch(true);
                }}
                className="text-[#86868b] hover:text-[#1d1d1f] p-1 rounded-lg hover:bg-black/[0.04] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitRejectFeedback} className="flex flex-col gap-4">
              <div className="bg-[#f5f5f7] rounded-xl p-3 text-xs flex flex-col gap-1.5 border border-black/[0.04]">
                <div className="font-semibold text-[#1d1d1f]">{rejectingCandidate.title}</div>
                <div className="text-[#6e6e73] flex items-center gap-2">
                  <span>Entidad: {rejectingCandidate.entity}</span>
                  <span>•</span>
                  <span>Instrumento: {rejectingCandidate.instrument_type}</span>
                </div>
                {rejectingCandidate.selection_reason && (
                  <div className="mt-1 pt-1.5 border-t border-black/[0.06] text-[#424245]">
                    <span className="font-semibold text-[#1d1d1f]">Justificacion original del agente: </span>
                    {rejectingCandidate.selection_reason}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#1d1d1f] mb-1">
                  Motivo del Descarte y Observaciones (Obligatorio)
                </label>
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Explique al agente por que este documento no es adecuado (ej. resolucion desactualizada, alcance fuera de Montes de Maria, documento incompleto)..."
                  rows={3}
                  required
                  className="w-full text-xs p-3 rounded-xl border border-black/[0.1] bg-[#fafafa] focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]/20 focus:border-[#0066cc] resize-none"
                />
              </div>

              {((rejectingCandidate.retry_count || 0) < (rejectingCandidate.max_retries || 6)) ? (
                <div className="flex flex-col gap-3 p-3 rounded-xl border border-blue-100 bg-blue-50/50">
                  <label className="flex items-start gap-2.5 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rejectRequestSearch}
                      onChange={(e) => setRejectRequestSearch(e.target.checked)}
                      className="mt-0.5 rounded border-black/[0.2] text-[#0066cc] focus:ring-[#0066cc]"
                    />
                    <div className="flex flex-col">
                      <span className="text-xs font-semibold text-[#1d1d1f]">
                        Solicitar al agente re-busqueda adaptativa de una alternativa oficial
                      </span>
                      <span className="text-[11px] text-[#6e6e73]">
                        Intento {(rejectingCandidate.retry_count || 0) + 1} de {rejectingCandidate.max_retries || 6}. El agente usara sus fuentes autorizadas y observara filtros anti-redundancia para no duplicar informacion.
                      </span>
                    </div>
                  </label>

                  {rejectRequestSearch && (
                    <div>
                      <label className="block text-[11px] font-medium text-[#1d1d1f] mb-1">
                        Criterio o directriz tecnica de reorientacion (Opcional)
                      </label>
                      <input
                        type="text"
                        value={rejectInstruction}
                        onChange={(e) => setRejectInstruction(e.target.value)}
                        placeholder="Ej: Buscar version consolidada 2024 o PDF normativo de Renovacion del Territorio"
                        className="w-full text-xs p-2.5 rounded-lg border border-black/[0.1] bg-white focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]/20 focus:border-[#0066cc]"
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-3 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 text-xs">
                  <span className="font-semibold">Limite maximo de 6 intentos alcanzado: </span>
                  No se pueden solicitar mas re-busquedas adaptativas para este instrumento. El descarte sera definitivo.
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-black/[0.06]">
                <button
                  type="button"
                  onClick={() => {
                    setRejectingCandidate(null);
                    setRejectReason('');
                    setRejectInstruction('');
                    setRejectRequestSearch(true);
                  }}
                  className="px-4 py-2 text-xs font-semibold text-[#424245] hover:text-[#1d1d1f] hover:bg-black/[0.04] rounded-xl transition-all cursor-pointer"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submittingReject || rejectReason.trim().length < 5}
                  className="px-4 py-2 text-xs font-semibold bg-[#dc2626] text-white hover:bg-[#b91c1c] rounded-xl shadow-xs transition-all disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
                >
                  {submittingReject && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>
                    {submittingReject ? 'Procesando...' : 'Confirmar Descarte y Retroalimentar'}
                  </span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Revisión Humana */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-xl rounded-2xl border border-black/[0.1] shadow-2xl p-6 flex flex-col gap-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between pb-3 border-b border-black/[0.06]">
              <div className="flex flex-col gap-0.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#0066cc]">
                  Puerta de Control Epistémico
                </span>
                <h3 className="text-base font-semibold text-[#1d1d1f]">Revisión Humana de Documento</h3>
                <span className="font-mono text-xs text-[#6e6e73]">{selectedDoc.source_id}</span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDoc(null)}
                className="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
                aria-label="Cerrar modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitReview} className="flex flex-col gap-4 text-xs">
              <div className="flex flex-col gap-1.5">
                <label className="font-semibold text-[#1d1d1f]">Identificador del Investigador / Revisor:</label>
                <input
                  type="text"
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  placeholder="ej. investigador_ebdi_01"
                  required
                  className="px-3.5 py-2.5 rounded-xl border border-black/[0.1] focus:outline-none focus:border-[#0066cc] font-medium"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="font-semibold text-[#1d1d1f]">Decisión Humana Formal:</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setDecision('approved_for_context')}
                    className={`px-3 py-2.5 rounded-xl font-semibold border flex flex-col items-center justify-center gap-1 transition-all ${
                      decision === 'approved_for_context'
                        ? 'bg-[#34c759] text-white border-[#34c759] shadow-sm'
                        : 'bg-white text-[#248a3d] border-[#34c759]/40 hover:bg-[#34c759]/5'
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Aprobar Contexto</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setDecision('pending_context_review')}
                    className={`px-3 py-2.5 rounded-xl font-semibold border flex flex-col items-center justify-center gap-1 transition-all ${
                      decision === 'pending_context_review'
                        ? 'bg-[#ff9500] text-white border-[#ff9500] shadow-sm'
                        : 'bg-white text-[#b25000] border-[#ff9500]/40 hover:bg-[#ff9500]/5'
                    }`}
                  >
                    <Clock className="w-4 h-4" />
                    <span>Cuarentena</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setDecision('rejected')}
                    className={`px-3 py-2.5 rounded-xl font-semibold border flex flex-col items-center justify-center gap-1 transition-all ${
                      decision === 'rejected'
                        ? 'bg-[#ff3b30] text-white border-[#ff3b30] shadow-sm'
                        : 'bg-white text-[#d70015] border-[#ff3b30]/40 hover:bg-[#ff3b30]/5'
                    }`}
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Rechazar</span>
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-semibold text-[#1d1d1f]">Notas de Justificación y Auditoría:</label>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Justifique la decisión con base en aplicabilidad territorial, vigencia o calidad de la fuente..."
                  rows={3}
                  required
                  className="px-3.5 py-2.5 rounded-xl border border-black/[0.1] focus:outline-none focus:border-[#0066cc]"
                />
              </div>

              <div className="bg-[#0066cc]/[0.03] p-3 rounded-xl border border-[#0066cc]/10 text-[11px] text-[#6e6e73]">
                <strong>Garantía Inmutable:</strong> La decisión no altera el SHA-256, la ruta de almacenamiento, la URL canónica, la fecha de descarga ni la clase de procedencia gubernamental.
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-black/[0.06]">
                <button
                  type="button"
                  onClick={() => setSelectedDoc(null)}
                  className="px-4 py-2 rounded-xl border border-black/[0.1] font-semibold text-[#1d1d1f] hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl bg-[#0066cc] text-white font-semibold hover:bg-[#0055b3] disabled:opacity-50 flex items-center gap-1.5 shadow-xs"
                >
                  <Send className="w-3.5 h-3.5" />
                  {submitting ? 'Registrando...' : 'Confirmar Decisión'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal de Inspección y Extracción de Creencias eBDI */}
      {beliefsDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] shadow-2xl border border-black/[0.08] flex flex-col overflow-hidden">
            {/* Cabecera del Modal */}
            <div className="p-6 border-b border-black/[0.06] flex items-center justify-between gap-4 bg-[#fafafc]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-[#248a3d]/10 flex items-center justify-center text-[#248a3d]">
                  <Brain className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#0066cc] bg-[#0066cc]/[0.08] px-2 py-0.5 rounded-md">
                      {beliefsDoc.source_id}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-md bg-[#248a3d]/15 text-[#248a3d] font-semibold">
                      Aprobado para Contexto
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-[#1d1d1f] mt-1">{beliefsDoc.title}</h3>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setBeliefsDoc(null)}
                className="text-gray-400 hover:text-gray-700 p-2 rounded-xl hover:bg-gray-100 transition-colors"
                aria-label="Cerrar modal de creencias"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Contenido del Modal */}
            <div className="p-6 overflow-y-auto flex-1 flex flex-col gap-6">
              {/* Barra de Telemetría del Modelo y Acciones Soberanas */}
              <div className="bg-[#f5f5f7] p-4 rounded-2xl border border-black/[0.04] flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3 text-xs flex-wrap">
                  <span className="font-semibold text-[#1d1d1f]">Motor de Inferencia:</span>
                  <span className="font-mono bg-white px-2.5 py-1 rounded-lg border border-black/[0.06] text-[#0066cc] font-bold">
                    ai/gemma4:E4B (Local Soberano)
                  </span>
                  <span className="text-[#86868b]">·</span>
                  <span className="text-[#6e6e73]">
                    Pipeline: Poppler <code>pdftotext</code> / Tesseract OCR + Zero-Trust Delimiters
                  </span>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    type="button"
                    disabled={ocrRunning || extractingBeliefs}
                    onClick={() => handleRunOcr(beliefsDoc.source_id)}
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-black/[0.08] hover:bg-gray-50 text-[#1d1d1f] flex items-center gap-1.5 shadow-xs disabled:opacity-50"
                    title="Ejecuta Poppler pdftoppm + Tesseract OCR localmente para documentos escaneados"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${ocrRunning ? 'animate-spin' : ''}`} />
                    <span>{ocrRunning ? 'Procesando OCR...' : 'Ejecutar OCR Local'}</span>
                  </button>
                  <button
                    type="button"
                    disabled={extractingBeliefs || ocrRunning}
                    onClick={() => handleRunExtraction(beliefsDoc.source_id)}
                    className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#0066cc] hover:bg-[#0055b3] text-white flex items-center gap-1.5 shadow-xs disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{extractingBeliefs ? 'Extrayendo con gemma4:e4b...' : beliefsData ? 'Re-extraer Creencias' : 'Ejecutar Extracción'}</span>
                  </button>
                  {beliefsData && (
                    <button
                      type="button"
                      onClick={() => setViewJsonBeliefId(viewJsonBeliefId === '__full__' ? null : '__full__')}
                      className={`px-3 py-2 rounded-xl text-xs font-semibold border flex items-center gap-1.5 transition-all ${
                        viewJsonBeliefId === '__full__'
                          ? 'bg-[#1d1d1f] text-white border-[#1d1d1f]'
                          : 'bg-white text-[#1d1d1f] border-black/[0.08] hover:bg-gray-50'
                      }`}
                    >
                      <Code className="w-3.5 h-3.5" />
                      <span>{viewJsonBeliefId === '__full__' ? 'Ocultar JSON Manifiesto' : 'Ver JSON Manifiesto'}</span>
                    </button>
                  )}
                  {beliefsData && beliefsData.beliefs.some((b) => b.curation_status === 'admitted_ebdi') && (
                    <button
                      type="button"
                      disabled={compilingYaml}
                      onClick={() => handleCompileYamls(beliefsDoc.source_id)}
                      className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#248a3d] hover:bg-[#1e7433] text-white flex items-center gap-1.5 shadow-xs disabled:opacity-50"
                      title="Compilar las creencias admitidas a especificaciones declarativas GoalSpec y PlanSpec YAML para el simulador EthosTerra"
                    >
                      <FileCode className="w-3.5 h-3.5" />
                      <span>{compilingYaml ? 'Compilando YAMLs...' : 'Compilar a YAML de Simulación'}</span>
                    </button>
                  )}
                </div>
              </div>

              {ocrMessage && (
                <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200/80 text-emerald-800 text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  <span>{ocrMessage}</span>
                </div>
              )}

              {beliefsError && (
                <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-xs">
                  {beliefsError}
                </div>
              )}

              {/* Visor de JSON Completo del Manifiesto si está activado */}
              {viewJsonBeliefId === '__full__' && beliefsData && (
                <div className="bg-[#1e1e1e] text-[#d4d4d4] p-4 rounded-2xl border border-black/10 flex flex-col gap-2 font-mono text-xs shadow-lg">
                  <div className="flex items-center justify-between pb-2 border-b border-white/10 text-xs">
                    <span className="font-semibold text-white">JSON de Extracción Territorial ({beliefsDoc.source_id})</span>
                    <button
                      type="button"
                      onClick={() => handleCopyJson(JSON.stringify(beliefsData, null, 2), '__full__')}
                      className="px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white font-sans text-xs flex items-center gap-1.5 transition-all"
                    >
                      {copiedBeliefId === '__full__' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedBeliefId === '__full__' ? 'Copiado' : 'Copiar JSON'}</span>
                    </button>
                  </div>
                  <pre className="max-h-96 overflow-y-auto overflow-x-auto whitespace-pre leading-relaxed select-all">
                    {JSON.stringify(beliefsData, null, 2)}
                  </pre>
                </div>
              )}

              {ocrRunning && (
                <div className="p-6 md:p-8 rounded-3xl bg-[#fafafc] border border-black/[0.08] shadow-sm flex flex-col gap-5 animate-in fade-in duration-300">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-[#5856d6]/10 border border-[#5856d6]/20 flex items-center justify-center text-[#5856d6] shrink-0">
                      <RefreshCw className="w-5 h-5 animate-spin" />
                    </div>
                    <div className="flex flex-col">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-[#5856d6] bg-[#5856d6]/[0.08] px-2 py-0.5 rounded-md">
                          LOCAL OCR PIPELINE
                        </span>
                        <span className="text-xs text-[#86868b]">Poppler pdftoppm + Tesseract OCR (spa)</span>
                      </div>
                      <h4 className="text-sm font-semibold text-[#1d1d1f] mt-1">
                        Reconocimiento Óptico de Caracteres en Ejecución Soberana
                      </h4>
                    </div>
                  </div>
                  <div className="w-full h-3.5 rounded-full bg-black/[0.05] p-0.5 overflow-hidden border border-black/[0.06]">
                    <div className="h-full rounded-full bg-gradient-to-r from-[#5856d6] via-[#0066cc] to-[#5856d6] animate-progress-shimmer w-3/4 transition-all duration-500" />
                  </div>
                  <p className="text-xs text-[#6e6e73]">
                    Convirtiendo páginas escaneadas del documento a capas de texto indexables sin dependencias externas ni telemetría en la nube.
                  </p>
                </div>
              )}

              {loadingBeliefs && (
                <div className="py-12 flex flex-col items-center justify-center gap-3 text-gray-500 text-sm">
                  <RefreshCw className="w-6 h-6 animate-spin text-[#0066cc]" />
                  <span>Consultando creencias territoriales...</span>
                </div>
              )}

              {extractingBeliefs && (
                <div className="p-6 md:p-8 rounded-3xl bg-[#fafafc] border border-black/[0.08] shadow-sm flex flex-col gap-6 animate-in fade-in duration-300">
                  {/* Encabezado con estado activo y tiempos */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-black/[0.06]">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-2xl bg-[#0066cc]/10 border border-[#0066cc]/20 flex items-center justify-center text-[#0066cc] shrink-0">
                        <Activity className="w-5 h-5 animate-pulse" />
                      </div>
                      <div className="flex flex-col">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-[#0066cc] bg-[#0066cc]/[0.08] px-2 py-0.5 rounded-md">
                            DMR INFERENCE
                          </span>
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-[#34c759]/15 text-[#248a3d] border border-[#34c759]/30">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#34c759] animate-ping" />
                            Offline-First Activo
                          </span>
                        </div>
                        <h4 className="text-sm font-semibold text-[#1d1d1f] mt-1">
                          Extracción Exhaustiva de Creencias Territoriales eBDI
                        </h4>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 bg-white px-4 py-2.5 rounded-2xl border border-black/[0.06] shadow-xs self-start md:self-auto">
                      <div className="flex flex-col items-end">
                        <span className="text-[10px] uppercase font-bold text-[#86868b]">Progreso</span>
                        <span className="font-mono text-base font-bold text-[#1d1d1f]">
                          {Math.round(extractionProgress)}%
                        </span>
                      </div>
                      <div className="h-6 w-px bg-black/[0.08]" />
                      <div className="flex flex-col items-end">
                        <span className="text-[10px] uppercase font-bold text-[#86868b] flex items-center gap-1">
                          <Clock className="w-3 h-3" /> Transcurrido
                        </span>
                        <span className="font-mono text-xs font-semibold text-[#6e6e73]">
                          {Math.floor(extractionElapsed / 60)
                            .toString()
                            .padStart(2, '0')}
                          :
                          {(extractionElapsed % 60).toString().padStart(2, '0')}s
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Barra de progreso visual interactiva */}
                  <div className="flex flex-col gap-2">
                    <div className="w-full h-3.5 rounded-full bg-black/[0.05] p-0.5 overflow-hidden border border-black/[0.06]">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-[#0066cc] via-[#248a3d] to-[#0066cc] animate-progress-shimmer transition-all duration-300 ease-out"
                        style={{ width: `${Math.max(6, extractionProgress)}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between text-xs text-[#6e6e73]">
                      <span className="font-medium text-[#1d1d1f] flex items-center gap-1.5">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#0066cc]" />
                        {extractionStageText}
                      </span>
                      <span className="font-mono text-[11px] text-[#86868b]">
                        {extractionProgress >= 100
                          ? '100% Completado'
                          : extractionProgress > 74
                          ? 'Fase 3 de 3'
                          : extractionProgress > 24
                          ? 'Fase 2 de 3'
                          : 'Fase 1 de 3'}
                      </span>
                    </div>
                  </div>

                  {/* Stepper horizontal con las 3 fases normativas */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                    {/* Fase 1 */}
                    <div
                      className={`p-3.5 rounded-2xl border transition-all flex flex-col gap-1.5 ${
                        extractionPhase > 1
                          ? 'bg-emerald-50/60 border-emerald-200/80 text-emerald-950'
                          : extractionPhase === 1
                          ? 'bg-blue-50/60 border-blue-200 text-blue-950 shadow-xs'
                          : 'bg-white/60 border-black/[0.05] text-[#86868b]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold tracking-wider">
                          Fase 1 · Delimitación
                        </span>
                        {extractionPhase > 1 ? (
                          <CheckCircle2 className="w-4 h-4 text-[#248a3d]" />
                        ) : extractionPhase === 1 ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#0066cc]" />
                        ) : (
                          <div className="w-3.5 h-3.5 rounded-full border border-black/20" />
                        )}
                      </div>
                      <span className="text-xs font-semibold">Segmentación Zero-Trust</span>
                      <p className="text-[11px] leading-relaxed opacity-80">
                        Extracción del texto del PDF y aislamiento de fragmentos agrarios y territoriales.
                      </p>
                    </div>

                    {/* Fase 2 */}
                    <div
                      className={`p-3.5 rounded-2xl border transition-all flex flex-col gap-1.5 ${
                        extractionPhase > 2
                          ? 'bg-emerald-50/60 border-emerald-200/80 text-emerald-950'
                          : extractionPhase === 2
                          ? 'bg-blue-50/60 border-blue-200 text-blue-950 shadow-xs'
                          : 'bg-white/60 border-black/[0.05] text-[#86868b]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold tracking-wider">
                          Fase 2 · Razonamiento
                        </span>
                        {extractionPhase > 2 ? (
                          <CheckCircle2 className="w-4 h-4 text-[#248a3d]" />
                        ) : extractionPhase === 2 ? (
                          <Brain className="w-3.5 h-3.5 animate-pulse text-[#0066cc]" />
                        ) : (
                          <div className="w-3.5 h-3.5 rounded-full border border-black/20" />
                        )}
                      </div>
                      <span className="text-xs font-semibold">Inferencia ai/gemma4:E4B</span>
                      <p className="text-[11px] leading-relaxed opacity-80">
                        Deducción de condiciones campesinas y acciones bajo JSON Schema estricto.
                      </p>
                    </div>

                    {/* Fase 3 */}
                    <div
                      className={`p-3.5 rounded-2xl border transition-all flex flex-col gap-1.5 ${
                        extractionPhase > 3
                          ? 'bg-emerald-50/60 border-emerald-200/80 text-emerald-950'
                          : extractionPhase === 3
                          ? 'bg-blue-50/60 border-blue-200 text-blue-950 shadow-xs'
                          : 'bg-white/60 border-black/[0.05] text-[#86868b]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase font-bold tracking-wider">
                          Fase 3 · Verificación
                        </span>
                        {extractionPhase > 3 ? (
                          <CheckCircle2 className="w-4 h-4 text-[#248a3d]" />
                        ) : extractionPhase === 3 ? (
                          <ShieldCheck className="w-3.5 h-3.5 animate-pulse text-[#0066cc]" />
                        ) : (
                          <div className="w-3.5 h-3.5 rounded-full border border-black/20" />
                        )}
                      </div>
                      <span className="text-xs font-semibold">Verbatim Gate & Colisiones</span>
                      <p className="text-[11px] leading-relaxed opacity-80">
                        Validación literal de citas y cruce con el acervo territorial histórico.
                      </p>
                    </div>
                  </div>

                  {/* Fila de Telemetría Técnica y Soberanía */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t border-black/[0.05] text-xs">
                    <div className="flex items-center gap-2 text-[#515154]">
                      <Cpu className="w-4 h-4 text-[#0066cc] shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase font-bold text-[#86868b]">Runtime</span>
                        <span className="font-mono text-[11px] font-semibold text-[#1d1d1f]">Docker Model Runner</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-[#515154]">
                      <ShieldCheck className="w-4 h-4 text-[#248a3d] shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase font-bold text-[#86868b]">Soberanía</span>
                        <span className="font-mono text-[11px] font-semibold text-[#1d1d1f]">100% Offline (Local)</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-[#515154]">
                      <Layers className="w-4 h-4 text-[#5856d6] shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase font-bold text-[#86868b]">Parámetros</span>
                        <span className="font-mono text-[11px] font-semibold text-[#1d1d1f]">Temp 0.0 · top_p 0.9</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-[#515154]">
                      <Sparkles className="w-4 h-4 text-[#ff9500] shrink-0" />
                      <div className="flex flex-col">
                        <span className="text-[10px] uppercase font-bold text-[#86868b]">Validación</span>
                        <span className="font-mono text-[11px] font-semibold text-[#1d1d1f]">Pydantic V2 Strict</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {!loadingBeliefs && !extractingBeliefs && !beliefsData && (
                <div className="py-12 flex flex-col items-center justify-center gap-3 text-gray-500 text-sm border-2 border-dashed border-gray-200 rounded-3xl">
                  <FileText className="w-8 h-8 text-gray-400" />
                  <span className="font-semibold text-gray-700">Aún no se han extraído creencias eBDI de este documento</span>
                  <p className="text-xs text-gray-500 text-center max-w-md">
                    Haz clic en "Ejecutar Extracción" para procesar el PDF soberanamente con gemma4:e4b y extraer proposiciones territoriales verificadas.
                  </p>
                </div>
              )}

              {!loadingBeliefs && !extractingBeliefs && beliefsData && (
                <div className="flex flex-col gap-4">
                  {/* Resumen Cuantitativo y Métricas */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-2xl bg-[#fafafc] border border-black/[0.04] flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-[#86868b]">Total Creencias</span>
                      <span className="text-lg font-bold text-[#1d1d1f]">{beliefsData.total_beliefs_extracted}</span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-200/60 flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-emerald-800">Verificadas (Verbatim)</span>
                      <span className="text-lg font-bold text-emerald-700">{beliefsData.verified_beliefs_count}</span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200/60 flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-amber-800">Alucinaciones Rechazadas</span>
                      <span className="text-lg font-bold text-amber-700">{beliefsData.rejected_hallucinations_count}</span>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-blue-50 border border-blue-200/60 flex flex-col gap-1">
                      <span className="text-[10px] uppercase font-bold text-blue-800">Admitidas eBDI</span>
                      <span className="text-lg font-bold text-blue-700">
                        {beliefsData.beliefs.filter((b) => b.curation_status === 'admitted_ebdi').length} / {beliefsData.beliefs.length}
                      </span>
                    </div>
                  </div>

                  {/* Listado de Creencias Extraídas con Curación Granular */}
                  <div className="flex flex-col gap-3.5">
                    {beliefsData.beliefs.map((b, idx) => {
                      const isVerbatim = b.verification_status === 'verified_verbatim'
                      const isAdmitted = b.curation_status === 'admitted_ebdi'
                      const isDismissed = b.curation_status === 'dismissed_noise'
                      const isCuratingThis = curatingBeliefId === b.belief_id
                      const isJsonOpen = viewJsonBeliefId === b.belief_id

                      return (
                        <div
                          key={b.belief_id}
                          className={`p-4 rounded-2xl border transition-all flex flex-col gap-3 ${
                            isDismissed
                              ? 'bg-gray-50/70 border-gray-200 opacity-60'
                              : isVerbatim
                              ? 'bg-white border-black/[0.08] shadow-xs'
                              : 'bg-amber-50/50 border-amber-200/80'
                          }`}
                        >
                          {/* Alerta de Inconsistencia o Colisión Normativa si fue detectada */}
                          {b.collision_detected && (
                            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-900 text-xs flex items-start gap-2.5">
                              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                              <div className="flex flex-col gap-0.5">
                                <span className="font-bold text-amber-800">Alerta de Inconsistencia / Conflicto Normativo Detectado</span>
                                <span className="text-amber-950 font-normal leading-relaxed">
                                  {b.collision_reason || 'Se detectó incompatibilidad potencial con otra regla territorial en el mismo territorio.'}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Cabecera de la Creencia */}
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-mono text-[11px] font-bold text-gray-500">#{idx + 1}</span>
                              {b.belief_key && (
                                <span className="font-mono text-[10px] px-2 py-0.5 rounded-md bg-[#0066cc]/10 text-[#0066cc] font-bold border border-[#0066cc]/20">
                                  {b.belief_key}
                                </span>
                              )}
                              <span className="text-xs px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-700 font-semibold">
                                {b.pillar}
                              </span>
                              <span className="text-xs font-semibold text-[#1d1d1f]">{b.topic}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {/* Badge de Verificación Anti-Alucinación */}
                              <span
                                className={`text-[11px] px-2.5 py-0.5 rounded-full font-semibold inline-flex items-center gap-1 ${
                                  isVerbatim
                                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300/60'
                                    : 'bg-amber-100 text-amber-800 border border-amber-300/60'
                                }`}
                              >
                                {isVerbatim ? <CheckCircle2 className="w-3 h-3" /> : <AlertOctagon className="w-3 h-3" />}
                                {isVerbatim ? 'Cita Verificada al 100%' : 'Alucinación Detectada'}
                              </span>

                              {/* Badge de Curación Humana */}
                              {isAdmitted && (
                                <span className="text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-[#34c759]/15 text-[#248a3d] border border-[#34c759]/40 inline-flex items-center gap-1">
                                  <ThumbsUp className="w-3 h-3" /> Admitida eBDI
                                </span>
                              )}
                              {isDismissed && (
                                <span className="text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-gray-200 text-gray-700 border border-gray-300 inline-flex items-center gap-1">
                                  <ThumbsDown className="w-3 h-3" /> Descartada (Ruido)
                                </span>
                              )}
                              {(!b.curation_status || b.curation_status === 'pending') && (
                                <span className="text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                                  Pendiente Curación
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Dupla Operativa eBDI: [Condición Fáctica -> Acción Ejecutable del Catálogo] */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 bg-slate-50/80 p-4 rounded-xl border border-slate-200/80">
                            <div className="flex flex-col gap-1.5">
                              <span className="text-[10px] uppercase font-bold text-amber-700 flex items-center gap-1.5">
                                <Zap className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
                                <span>Condición Fáctica del Campesino (Trigger):</span>
                              </span>
                              <p className="text-xs text-slate-800 font-medium leading-relaxed bg-white p-3 rounded-lg border border-slate-200/60 shadow-2xs">
                                {b.trigger_condition || 'Condición general del territorio aplicable a pequeños productores.'}
                              </p>
                            </div>
                            <div className="flex flex-col gap-1.5">
                              <span className="text-[10px] uppercase font-bold text-blue-700 flex items-center gap-1.5">
                                <Target className="w-3.5 h-3.5 text-blue-600" aria-hidden="true" />
                                <span>Acción del Catálogo EthosTerra:</span>
                              </span>
                              <div className="bg-white p-3 rounded-lg border border-slate-200/60 shadow-2xs flex flex-col gap-2">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className="font-mono text-xs font-bold bg-emerald-100 text-emerald-900 px-2 py-0.5 rounded border border-emerald-300">
                                    {b.executable_action || 'agro_ecosystem_operation'}
                                  </span>
                                  {b.action_operation_type && (
                                    <span className="font-mono text-xs font-semibold bg-blue-100 text-blue-900 px-2 py-0.5 rounded border border-blue-300">
                                      operation: {b.action_operation_type}
                                    </span>
                                  )}
                                  {b.activation_rule_template && (
                                    <span className="font-mono text-[10px] text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                                      MVEL: {b.activation_rule_template}
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-[#333336] leading-relaxed">
                                  <strong>Efecto:</strong> {b.behavioral_effect || b.ebdi_belief_assertion}
                                </p>
                              </div>
                            </div>
                          </div>

                          {/* Cita Textual Fuente Literal */}
                          <div className="flex flex-col gap-1">
                            <span className="text-[10px] uppercase font-bold text-[#86868b]">Cita Textual Literal Fuente (raw_excerpt):</span>
                            <blockquote className="border-l-2 border-[#0066cc] bg-[#f5f5f7] pl-3 py-1.5 pr-2 rounded-r-xl text-xs text-[#333336] italic leading-relaxed">
                              "{b.raw_excerpt}"
                            </blockquote>
                          </div>

                          {/* Barra de Acciones y Metadatos */}
                          <div className="flex items-center justify-between pt-2 border-t border-black/[0.04] text-[11px] text-[#6e6e73] flex-wrap gap-2">
                            <div className="flex items-center gap-3 flex-wrap">
                              <div className="flex items-center gap-1">
                                <span className="font-medium text-[#1d1d1f]">Municipios:</span>
                                <span>{b.target_municipalities.length > 0 ? b.target_municipalities.join(', ') : 'Ámbito General Subregional'}</span>
                              </div>
                              {b.applicable_divipolas.length > 0 && (
                                <span className="font-mono text-[#0066cc] font-semibold">
                                  DIVIPOLA: [{b.applicable_divipolas.join(', ')}]
                                </span>
                              )}
                              <span className="font-mono text-gray-500">
                                Confianza: {(b.confidence * 100).toFixed(0)}%
                              </span>
                            </div>

                            {/* Controles de Curación Humana Granular y Visor JSON */}
                            <div className="flex items-center gap-1.5">
                              <button
                                type="button"
                                disabled={isCuratingThis}
                                onClick={() => handleCurateBelief(beliefsDoc.source_id, b.belief_id, 'admitted_ebdi')}
                                className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all ${
                                  isAdmitted
                                    ? 'bg-[#34c759] text-white shadow-xs'
                                    : 'bg-white border border-black/[0.08] hover:bg-emerald-50 hover:text-emerald-700 text-[#1d1d1f]'
                                }`}
                                title="Admitir esta creencia para la toma de decisiones eBDI de los agentes"
                              >
                                <ThumbsUp className="w-3 h-3" />
                                <span>Admitir eBDI</span>
                              </button>

                              <button
                                type="button"
                                disabled={isCuratingThis}
                                onClick={() => handleCurateBelief(beliefsDoc.source_id, b.belief_id, 'dismissed_noise')}
                                className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition-all ${
                                  isDismissed
                                    ? 'bg-gray-700 text-white shadow-xs'
                                    : 'bg-white border border-black/[0.08] hover:bg-gray-100 text-[#6e6e73]'
                                }`}
                                title="Descartar esta creencia si es ruido de índice, tabla de siglas o no aporta valor eBDI"
                              >
                                <ThumbsDown className="w-3 h-3" />
                                <span>Descartar Ruido</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => setViewJsonBeliefId(isJsonOpen ? null : b.belief_id)}
                                className={`px-2.5 py-1 rounded-lg text-xs font-semibold border flex items-center gap-1 transition-all ${
                                  isJsonOpen
                                    ? 'bg-[#1d1d1f] text-white border-[#1d1d1f]'
                                    : 'bg-white border-black/[0.08] hover:bg-gray-50 text-[#1d1d1f]'
                                }`}
                                title="Ver el objeto JSON raw exacto de esta creencia"
                              >
                                <Code className="w-3 h-3" />
                                <span>{isJsonOpen ? 'Ocultar JSON' : 'Ver JSON'}</span>
                              </button>

                              <button
                                type="button"
                                onClick={() => handleStartEdit(b)}
                                className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-white border border-black/[0.08] hover:bg-blue-50 hover:text-blue-700 text-[#1d1d1f] flex items-center gap-1 transition-all"
                                title="Editar campos de la creencia (formulario amigable para no programadores o editor JSON para investigadores)"
                              >
                                <Edit3 className="w-3 h-3" />
                                <span>Editar</span>
                              </button>
                            </div>
                          </div>

                          {/* Visor de JSON Desplegable para esta Creencia */}
                          {isJsonOpen && (
                            <div className="bg-[#1e1e1e] text-[#d4d4d4] p-3 rounded-xl border border-black/10 flex flex-col gap-2 font-mono text-[11px] mt-1 shadow-inner">
                              <div className="flex items-center justify-between pb-1.5 border-b border-white/10">
                                <span className="font-semibold text-white">JSON de la Creencia #{idx + 1} ({b.belief_id})</span>
                                <button
                                  type="button"
                                  onClick={() => handleCopyJson(JSON.stringify(b, null, 2), b.belief_id)}
                                  className="px-2 py-0.5 rounded bg-white/10 hover:bg-white/20 text-white font-sans text-[11px] flex items-center gap-1 transition-all"
                                >
                                  {copiedBeliefId === b.belief_id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                                  <span>{copiedBeliefId === b.belief_id ? 'Copiado!' : 'Copiar'}</span>
                                </button>
                              </div>
                              <pre className="max-h-60 overflow-y-auto overflow-x-auto whitespace-pre leading-relaxed select-all">
                                {JSON.stringify(b, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* Pie del Modal */}
            <div className="p-4 border-t border-black/[0.06] bg-[#fafafc] flex items-center justify-between text-xs text-[#86868b]">
              <span className="font-mono">
                Persistido soberanamente en <code>outputs/atlas/context/{beliefsDoc.source_id}_beliefs.json</code>
              </span>
              <button
                type="button"
                onClick={() => setBeliefsDoc(null)}
                className="px-4 py-2 rounded-xl bg-gray-200 hover:bg-gray-300 text-[#1d1d1f] font-semibold transition-all"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Edición Granular de Creencia (Modo Amigable / JSON) */}
      {editingBelief && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-black/10">
            <div className="p-5 border-b border-black/[0.06] bg-[#fafafc] flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#0066cc]/10 flex items-center justify-center text-[#0066cc]">
                  <Edit3 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1d1d1f]">Edición de Creencia Territorial eBDI</h3>
                  <span className="font-mono text-xs text-[#6e6e73]">{editingBelief.belief_id}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {/* Selector de Modo */}
                <div className="flex items-center p-1 bg-black/[0.04] rounded-xl text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => {
                      setEditTab('friendly')
                      try {
                        const parsed = JSON.parse(editJsonStr)
                        setEditingBelief(parsed)
                      } catch (_) {}
                    }}
                    className={`px-3 py-1 rounded-lg transition-all ${
                      editTab === 'friendly' ? 'bg-white text-[#1d1d1f] shadow-xs' : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                    }`}
                  >
                    Formulario Guiado
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditJsonStr(JSON.stringify(editingBelief, null, 2))
                      setEditTab('json')
                    }}
                    className={`px-3 py-1 rounded-lg transition-all ${
                      editTab === 'json' ? 'bg-[#1d1d1f] text-white shadow-xs' : 'text-[#6e6e73] hover:text-[#1d1d1f]'
                    }`}
                  >
                    Editor JSON
                  </button>
                </div>
                <button
                  type="button"
                  onClick={() => setEditingBelief(null)}
                  className="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto flex-1 flex flex-col gap-4">
              {editError && (
                <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
                  {editError}
                </div>
              )}

              {editTab === 'friendly' ? (
                <div className="flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#1d1d1f]">Tema / Título Descriptivo:</label>
                    <input
                      type="text"
                      value={editingBelief.topic || ''}
                      onChange={(e) => setEditingBelief({ ...editingBelief, topic: e.target.value })}
                      className="p-2.5 rounded-xl border border-black/[0.1] text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-amber-800">
                        Condición Fáctica en el Campo (¿Cuándo ocurre?):
                      </label>
                      <textarea
                        rows={3}
                        value={editingBelief.trigger_condition || ''}
                        onChange={(e) => setEditingBelief({ ...editingBelief, trigger_condition: e.target.value })}
                        className="p-2.5 rounded-xl border border-amber-200 bg-amber-50/20 text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-amber-500"
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-blue-800">
                        Efecto Conductual (¿Qué hace el campesino?):
                      </label>
                      <textarea
                        rows={3}
                        value={editingBelief.behavioral_effect || ''}
                        onChange={(e) => setEditingBelief({ ...editingBelief, behavioral_effect: e.target.value })}
                        className="p-2.5 rounded-xl border border-blue-200 bg-blue-50/20 text-xs font-medium focus:outline-hidden focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-[#1d1d1f]">Acción del Catálogo EthosTerra:</label>
                      <select
                        value={editingBelief.executable_action || 'agro_ecosystem_operation'}
                        onChange={(e) => setEditingBelief({ ...editingBelief, executable_action: e.target.value })}
                        className="p-2.5 rounded-xl border border-black/[0.1] text-xs font-mono bg-white focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]"
                      >
                        <option value="agro_ecosystem_operation">agro_ecosystem_operation</option>
                        <option value="send_marketplace_event">send_marketplace_event</option>
                        <option value="send_society_collaboration">send_society_collaboration</option>
                        <option value="consume_resource">consume_resource</option>
                        <option value="update_belief">update_belief</option>
                        <option value="increment_belief">increment_belief</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-[#1d1d1f]">Operación Agronómica (si aplica):</label>
                      <input
                        type="text"
                        placeholder="PREPARE, PLANT, IRRIGATE, BUY_SEEDS..."
                        value={editingBelief.action_operation_type || ''}
                        onChange={(e) => setEditingBelief({ ...editingBelief, action_operation_type: e.target.value || null })}
                        className="p-2.5 rounded-xl border border-black/[0.1] text-xs font-mono focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]"
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#1d1d1f]">Proposición eBDI Formalizada:</label>
                    <textarea
                      rows={2}
                      value={editingBelief.ebdi_belief_assertion || ''}
                      onChange={(e) => setEditingBelief({ ...editingBelief, ebdi_belief_assertion: e.target.value })}
                      className="p-2.5 rounded-xl border border-black/[0.1] text-xs focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#1d1d1f]">Cita Textual Literal Fuente (raw_excerpt):</label>
                    <textarea
                      rows={2}
                      value={editingBelief.raw_excerpt || ''}
                      onChange={(e) => setEditingBelief({ ...editingBelief, raw_excerpt: e.target.value })}
                      className="p-2.5 rounded-xl border border-black/[0.1] bg-gray-50 text-xs italic focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-[#1d1d1f]">Municipios Afectados (separados por coma):</label>
                      <input
                        type="text"
                        value={editingBelief.target_municipalities.join(', ')}
                        onChange={(e) =>
                          setEditingBelief({
                            ...editingBelief,
                            target_municipalities: e.target.value.split(',').map((m) => m.trim()).filter(Boolean),
                          })
                        }
                        className="p-2.5 rounded-xl border border-black/[0.1] text-xs focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]"
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-bold text-[#1d1d1f]">Plantilla MVEL (activation_when):</label>
                      <input
                        type="text"
                        value={editingBelief.activation_rule_template || ''}
                        onChange={(e) => setEditingBelief({ ...editingBelief, activation_rule_template: e.target.value })}
                        className="p-2.5 rounded-xl border border-black/[0.1] font-mono text-xs focus:outline-hidden focus:ring-2 focus:ring-[#0066cc]"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  <span className="text-xs text-[#6e6e73]">
                    Edición directa del objeto JSON para programadores e investigadores:
                  </span>
                  <textarea
                    rows={16}
                    value={editJsonStr}
                    onChange={(e) => setEditJsonStr(e.target.value)}
                    className="p-3.5 rounded-xl bg-[#1e1e1e] text-[#d4d4d4] font-mono text-xs focus:outline-hidden focus:ring-2 focus:ring-[#0066cc] leading-relaxed"
                  />
                </div>
              )}
            </div>

            <div className="p-4 border-t border-black/[0.06] bg-[#fafafc] flex items-center justify-between">
              <button
                type="button"
                onClick={() => setEditingBelief(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-gray-100"
              >
                Cancelar
              </button>
              <button
                type="button"
                disabled={savingEdit}
                onClick={handleSaveEdit}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#0066cc] hover:bg-[#0055b3] text-white flex items-center gap-1.5 shadow-xs disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{savingEdit ? 'Guardando...' : 'Guardar y Re-validar'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Previsualización de YAMLs Compilados (GoalSpec & PlanSpec) */}
      {showYamlViewer && compiledYamlResult && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-black/10">
            <div className="p-5 border-b border-black/[0.06] bg-[#fafafc] flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#248a3d]/10 flex items-center justify-center text-[#248a3d]">
                  <FileCode className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1d1d1f]">Especificaciones Declarativas YAML Compiladas</h3>
                  <span className="text-xs text-[#6e6e73]">
                    {compiledYamlResult.compiled_goals_count} Metas (GoalSpec) y {compiledYamlResult.compiled_plans_count} Planes (PlanSpec) generados
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowYamlViewer(false)}
                className="text-gray-400 hover:text-gray-700 p-1.5 rounded-lg hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1 flex flex-col gap-4">
              <div className="flex items-center gap-2 border-b border-black/[0.06] pb-3">
                <button
                  type="button"
                  onClick={() => setActiveYamlTab('goals')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    activeYamlTab === 'goals'
                      ? 'bg-[#0066cc] text-white shadow-xs'
                      : 'bg-gray-100 text-[#1d1d1f] hover:bg-gray-200'
                  }`}
                >
                  Metas (GoalSpec) ({compiledYamlResult.goals?.length || 0})
                </button>
                <button
                  type="button"
                  onClick={() => setActiveYamlTab('plans')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    activeYamlTab === 'plans'
                      ? 'bg-[#0066cc] text-white shadow-xs'
                      : 'bg-gray-100 text-[#1d1d1f] hover:bg-gray-200'
                  }`}
                >
                  Planes (PlanSpec) ({compiledYamlResult.plans?.length || 0})
                </button>
              </div>

              {activeYamlTab === 'goals' && (
                <div className="flex flex-col gap-4">
                  {compiledYamlResult.goals?.map((g: any) => (
                    <div key={g.goal_id} className="p-4 rounded-2xl bg-gray-50 border border-black/[0.06] flex flex-col gap-2">
                      <div className="flex items-center justify-between text-xs font-bold text-[#1d1d1f]">
                        <span className="font-mono text-[#0066cc]">{g.goal_id}.yaml</span>
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard.writeText(g.yaml_content)
                            setCopiedYamlId(g.goal_id)
                            setTimeout(() => setCopiedYamlId(null), 2000)
                          }}
                          className="px-2.5 py-1 rounded-lg bg-white border border-black/[0.08] hover:bg-gray-100 text-xs flex items-center gap-1"
                        >
                          {copiedYamlId === g.goal_id ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedYamlId === g.goal_id ? 'Copiado' : 'Copiar YAML'}</span>
                        </button>
                      </div>
                      <pre className="p-3 bg-[#1e1e1e] text-[#d4d4d4] rounded-xl font-mono text-[11px] max-h-48 overflow-auto leading-relaxed select-all">
                        {g.yaml_content}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {activeYamlTab === 'plans' && (
                <div className="flex flex-col gap-4">
                  {compiledYamlResult.plans?.map((p: any) => (
                    <div key={p.plan_id} className="p-4 rounded-2xl bg-gray-50 border border-black/[0.06] flex flex-col gap-2">
                      <div className="flex items-center justify-between text-xs font-bold text-[#1d1d1f]">
                        <span className="font-mono text-[#248a3d]">{p.plan_id}.yaml</span>
                        <button
                          type="button"
                          onClick={() => {
                            navigator.clipboard.writeText(p.yaml_content)
                            setCopiedYamlId(p.plan_id)
                            setTimeout(() => setCopiedYamlId(null), 2000)
                          }}
                          className="px-2.5 py-1 rounded-lg bg-white border border-black/[0.08] hover:bg-gray-100 text-xs flex items-center gap-1"
                        >
                          {copiedYamlId === p.plan_id ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedYamlId === p.plan_id ? 'Copiado' : 'Copiar YAML'}</span>
                        </button>
                      </div>
                      <pre className="p-3 bg-[#1e1e1e] text-[#d4d4d4] rounded-xl font-mono text-[11px] max-h-48 overflow-auto leading-relaxed select-all">
                        {p.yaml_content}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="p-4 border-t border-black/[0.06] bg-[#fafafc] flex items-center justify-between text-xs text-[#86868b]">
              <span>Archivos persistidos en <code>outputs/atlas/yaml/</code></span>
              <button
                type="button"
                onClick={() => setShowYamlViewer(false)}
                className="px-4 py-2 rounded-xl bg-gray-200 hover:bg-gray-300 text-[#1d1d1f] font-semibold transition-all"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
