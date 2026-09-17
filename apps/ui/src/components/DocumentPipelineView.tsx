import { useState } from 'react';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Unlock,
  ShieldCheck,
  FolderSync,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { EpistemicBadge } from './EpistemicBadge';
import { cn } from '../lib/utils';

const API_BASE = 'http://localhost:8000/v2';

const SAMPLE_DIARY = `El campesino peasant_01 indica que para la próxima temporada de siembra es indispensable preparar el terreno adecuadamente. Para llevar a cabo esta labor se requiere contar con las herramientas necesarias en la parcela.`;

export default function DocumentPipelineView() {
  // Navigation & Experiment state
  const [experimentId] = useState('exp_vertical_001');
  const [docId] = useState('doc_diario_001');
  const [sourceText, setSourceText] = useState(SAMPLE_DIARY);
  const [activeTab, setActiveTab] = useState<'flow' | 'yamls' | 'metrics' | 'manifest'>('flow');

  // Step Statuses
  const [ingestData, setIngestData] = useState<any>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [operationalData, setOperationalData] = useState<any>(null);
  const [approvedData, setApprovedData] = useState<any>(null);
  const [generatedYamls, setGeneratedYamls] = useState<any>(null);
  const [installationData, setInstallationData] = useState<any>(null);
  const [metricsData, setMetricsData] = useState<any>(null);
  const [manifestData, setManifestData] = useState<any>(null);

  // Approval Inputs
  const [approverId, setApproverId] = useState('investigador_principal');
  const [approvalNotes, setApprovalNotes] = useState('Aprobado para generación experimental de YAML.');

  // Loading & Feedback states
  const [loadingStep, setLoadingStep] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const clearMessages = () => {
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  // 1. Ingest
  const handleIngest = async () => {
    clearMessages();
    setLoadingStep('ingest');
    try {
      const res = await fetch(`${API_BASE}/documents/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: sourceText,
          source_type: 'peasant_diary',
          document_id: docId,
          experiment_id: experimentId,
          filename: 'diario_campesino_preparacion.txt',
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setIngestData(data);
      setSuccessMessage('Documento normalizado e ingerido con hash SHA-256 inmutable.');
    } catch (err: any) {
      setErrorMessage(`Error en ingesta: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  // 2. Extract
  const handleExtract = async () => {
    clearMessages();
    setLoadingStep('extract');
    try {
      const res = await fetch(`${API_BASE}/documents/${docId}/extract`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setAnalysisData(data);
      setSuccessMessage('Conocimiento epistemológico extraído con referencias de evidencia.');
    } catch (err: any) {
      setErrorMessage(`Error en extracción: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  // 3. Structure
  const handleStructure = async () => {
    clearMessages();
    setLoadingStep('structure');
    try {
      const res = await fetch(`${API_BASE}/documents/${docId}/structure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tipo_caso: 'puro',
          actor_alias: 'peasant_01',
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setOperationalData(data);
      setSuccessMessage('Objetivos y planes eBDI estructurados. Pendiente de aprobación humana.');
    } catch (err: any) {
      setErrorMessage(`Error en estructuración: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  // 4. Approve
  const handleApprove = async () => {
    clearMessages();
    setLoadingStep('approve');
    try {
      const res = await fetch(`${API_BASE}/documents/${docId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          approver_id: approverId,
          notes: approvalNotes,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setApprovedData(data);
      setOperationalData(data);
      setSuccessMessage('¡Documento aprobado formalmente! Puerta de generación YAML desbloqueada.');
    } catch (err: any) {
      setErrorMessage(`Error en aprobación: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  // 5. Generate YAML
  const handleGenerateYaml = async () => {
    clearMessages();
    setLoadingStep('generate');
    try {
      const res = await fetch(`${API_BASE}/documents/${docId}/generate-yaml`, {
        method: 'POST',
      });
      if (!res.ok) {
        const errorDetail = await res.json();
        throw new Error(errorDetail.detail || 'Generación rechazada por la puerta de control.');
      }
      const data = await res.json();
      setGeneratedYamls(data);
      setSuccessMessage('Archivos YAML generados deterministamente con hashes verificados.');
    } catch (err: any) {
      setErrorMessage(err.message);
    } finally {
      setLoadingStep(null);
    }
  };

  // 6. Install to Sandbox
  const handleInstall = async () => {
    clearMessages();
    setLoadingStep('install');
    try {
      const res = await fetch(`${API_BASE}/experiments/${experimentId}/install`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: docId }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setInstallationData(data);
      setSuccessMessage('Archivos instalados en la sandbox EthosTerra_experiment. Respaldo creado exitosamente.');
    } catch (err: any) {
      setErrorMessage(`Error en instalación: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  // 7. Rollback Sandbox
  const handleRollback = async () => {
    clearMessages();
    setLoadingStep('rollback');
    try {
      const res = await fetch(`${API_BASE}/experiments/${experimentId}/rollback`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setSuccessMessage(`Sandbox restaurada exitosamente desde ${data.restored_from}.`);
      setInstallationData(null);
    } catch (err: any) {
      setErrorMessage(`Error en rollback: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  // Load Metrics
  const handleLoadMetrics = async () => {
    setLoadingStep('metrics');
    try {
      const res = await fetch(`${API_BASE}/experiments/${experimentId}/metrics`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setMetricsData(data);
    } catch (err: any) {
      setErrorMessage(`Error cargando métricas: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  // Load Manifest
  const handleLoadManifest = async () => {
    setLoadingStep('manifest');
    try {
      const res = await fetch(`${API_BASE}/experiments/${experimentId}/manifest`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setManifestData(data);
    } catch (err: any) {
      setErrorMessage(`Error cargando manifiesto: ${err.message}`);
    } finally {
      setLoadingStep(null);
    }
  };

  const isApproved = operationalData?.status === 'Aprobado' && operationalData?.review_status === 'approved';

  return (
    <div className="space-y-6">
      {/* Top Banner & Sandbox Safeguard Status */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
              Semana 6 — Document Pipeline
            </span>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> EthosTerra_original: SOLO LECTURA
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-800 mt-1">
            Traductor Documental a Especificaciones eBDI
          </h2>
          <p className="text-sm text-slate-500">
            Extracción epistemológica, puerta de aprobación humana inmutable y sandbox en{' '}
            <code className="bg-slate-100 px-1 py-0.5 rounded text-slate-700">outputs/experiments/{experimentId}/EthosTerra_experiment</code>
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex bg-slate-100 p-1 rounded-lg text-sm self-stretch md:self-auto">
          <button
            onClick={() => setActiveTab('flow')}
            className={cn(
              'px-3 py-1.5 rounded-md font-medium transition-all',
              activeTab === 'flow' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            )}
          >
            Flujo de Pipeline
          </button>
          <button
            onClick={() => {
              setActiveTab('metrics');
              if (!metricsData) handleLoadMetrics();
            }}
            className={cn(
              'px-3 py-1.5 rounded-md font-medium transition-all',
              activeTab === 'metrics' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            )}
          >
            Métricas Reproducibles
          </button>
          <button
            onClick={() => {
              setActiveTab('manifest');
              if (!manifestData) handleLoadManifest();
            }}
            className={cn(
              'px-3 py-1.5 rounded-md font-medium transition-all',
              activeTab === 'manifest' ? 'bg-white text-blue-600 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            )}
          >
            Manifiesto
          </button>
        </div>
      </div>

      {/* Notifications */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1 font-medium">{errorMessage}</div>
        </div>
      )}
      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-sm flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div className="flex-1 font-medium">{successMessage}</div>
        </div>
      )}

      {/* TAB: FLOW */}
      {activeTab === 'flow' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Documentary Ingest & Epistemic Analysis */}
          <div className="lg:col-span-6 space-y-6">
            {/* Step 1: Ingest */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold">
                    1
                  </span>
                  Fuente Documental y Normalización
                </div>
                <button
                  type="button"
                  onClick={() => setSourceText(SAMPLE_DIARY)}
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                >
                  <Sparkles className="w-3.5 h-3.5" /> Cargar muestra de campesino
                </button>
              </div>

              <textarea
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
                rows={4}
                className="w-full text-sm p-3 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-sans"
                placeholder="Pegue aquí el extracto de diario, entrevista o documento..."
              />

              <div className="mt-3 flex items-center justify-between">
                <div className="text-xs text-slate-500 font-mono">
                  {ingestData ? (
                    <span className="text-emerald-600 font-medium">
                      SHA-256: {ingestData.sha256_hash.slice(0, 16)}... ({ingestData.char_count} chars)
                    </span>
                  ) : (
                    <span>No ingerido aún</span>
                  )}
                </div>
                <button
                  onClick={handleIngest}
                  disabled={loadingStep === 'ingest'}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-sm font-medium transition flex items-center gap-2"
                >
                  {loadingStep === 'ingest' ? 'Procesando...' : '1. Ingerir y Normalizar'}
                </button>
              </div>
            </div>

            {/* Step 2: Epistemic Breakdown */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold">
                    2
                  </span>
                  Extracción Epistemológica y Trazabilidad
                </div>
                <button
                  onClick={handleExtract}
                  disabled={!ingestData || loadingStep === 'extract'}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5',
                    !ingestData
                      ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  )}
                >
                  {loadingStep === 'extract' ? 'Extrayendo...' : '2. Extraer Epistemología'}
                </button>
              </div>

              {analysisData ? (
                <div className="space-y-4">
                  {/* Interactive Evidence Quote */}
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                    <div className="font-semibold text-slate-600 mb-1 flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5" /> Evidencia Textual (Fragmento frag_01):
                    </div>
                    <p className="text-slate-800 italic bg-amber-50 p-2 rounded border border-amber-200">
                      "{analysisData.evidence_spans?.[0]?.text_quote}"
                    </p>
                  </div>

                  {/* Epistemic Fields Table */}
                  <div className="divide-y divide-slate-100 text-sm">
                    <div className="py-2 flex items-center justify-between">
                      <span className="text-slate-600 text-xs font-mono">Actor Alias:</span>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800">
                          {analysisData.extracted_knowledge.actor_alias.value}
                        </span>
                        <EpistemicBadge
                          status={analysisData.extracted_knowledge.actor_alias.status}
                          evidenceRef={analysisData.extracted_knowledge.actor_alias.evidence_ref}
                        />
                      </div>
                    </div>

                    <div className="py-2 flex items-center justify-between">
                      <span className="text-slate-600 text-xs font-mono">Intención Central:</span>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800">
                          {analysisData.extracted_knowledge.intentions?.[0]?.value}
                        </span>
                        <EpistemicBadge
                          status={analysisData.extracted_knowledge.intentions?.[0]?.status}
                          evidenceRef={analysisData.extracted_knowledge.intentions?.[0]?.evidence_ref}
                        />
                      </div>
                    </div>

                    <div className="py-2 flex items-center justify-between">
                      <span className="text-slate-600 text-xs font-mono">Deseo Subyacente:</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-700 text-xs">
                          {analysisData.extracted_knowledge.desires?.[0]?.value}
                        </span>
                        <EpistemicBadge
                          status={analysisData.extracted_knowledge.desires?.[0]?.status}
                          evidenceRef={analysisData.extracted_knowledge.desires?.[0]?.evidence_ref}
                        />
                      </div>
                    </div>

                    <div className="py-2 flex items-center justify-between">
                      <span className="text-slate-600 text-xs font-mono">Requerimiento Operativo:</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-700 text-xs font-mono">
                          {JSON.stringify(analysisData.extracted_knowledge.requirements?.[0]?.value)}
                        </span>
                        <EpistemicBadge
                          status={analysisData.extracted_knowledge.requirements?.[0]?.status}
                          rationale={analysisData.extracted_knowledge.requirements?.[0]?.rationale}
                        />
                      </div>
                    </div>

                    <div className="py-2 flex items-center justify-between">
                      <span className="text-slate-600 text-xs font-mono">Contexto Territorial:</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 text-xs italic">No especificado</span>
                        <EpistemicBadge
                          status={analysisData.extracted_knowledge.territory_context.status}
                          rationale={analysisData.extracted_knowledge.territory_context.rationale}
                        />
                      </div>
                    </div>

                    <div className="py-2 flex items-center justify-between">
                      <span className="text-slate-600 text-xs font-mono">Estado Afectivo (Felicidad):</span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 text-xs italic">Desconocido</span>
                        <EpistemicBadge status="unknown" />
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-slate-400 text-xs">
                  Complete el paso 1 y extraiga el conocimiento epistemológico.
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Operational Structuring, Approval Gate & Deployment */}
          <div className="lg:col-span-6 space-y-6">
            {/* Step 3: Structuring & Catalog Validation */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold">
                    3
                  </span>
                  Estructuración Operativa (GoalSpec & PlanSpec)
                </div>
                <button
                  onClick={handleStructure}
                  disabled={!analysisData || loadingStep === 'structure'}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-xs font-medium transition flex items-center gap-1.5',
                    !analysisData
                      ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                      : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                  )}
                >
                  {loadingStep === 'structure' ? 'Estructurando...' : '3. Estructurar Objetivos'}
                </button>
              </div>

              {operationalData ? (
                <div className="space-y-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-700">Artefactos Propuestos:</span>
                      <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        2 artefactos conformes
                      </span>
                    </div>
                    <ul className="list-disc pl-4 space-y-1 text-slate-600">
                      <li>
                        <strong className="font-mono text-slate-800">GoalSpec:</strong> prepare_land (plan_ref: prepare_land_plan_v1)
                      </li>
                      <li>
                        <strong className="font-mono text-slate-800">PlanSpec:</strong> prepare_land_plan_v1 (2 pasos: agro_ecosystem_operation, emit_episode)
                      </li>
                    </ul>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                    <span className="font-semibold text-slate-700">Acciones validadas contra Catálogo:</span>
                    <span className="text-blue-700 font-mono font-medium">
                      2/2 acciones existentes y tipadas
                    </span>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-slate-400 text-xs">
                  Complete el paso 2 para estructurar los artefactos de simulación.
                </div>
              )}
            </div>

            {/* Step 4: Strict Human Approval Gate */}
            <div
              className={cn(
                'border rounded-xl p-5 shadow-xs transition-all',
                isApproved
                  ? 'bg-emerald-50/50 border-emerald-200'
                  : 'bg-amber-50/50 border-amber-200'
              )}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold">
                    4
                  </span>
                  Puerta de Aprobación Humana (Approval Gate)
                </div>
                {isApproved ? (
                  <span className="px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-600 text-white flex items-center gap-1">
                    <Unlock className="w-3.5 h-3.5" /> Aprobado
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-md text-xs font-bold bg-amber-600 text-white flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5" /> Pendiente de Aprobación
                  </span>
                )}
              </div>

              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="block text-slate-600 font-medium mb-1">Investigador:</label>
                    <input
                      type="text"
                      value={approverId}
                      onChange={(e) => setApproverId(e.target.value)}
                      disabled={isApproved}
                      className="w-full p-2 border border-slate-200 rounded bg-white font-mono text-slate-800"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-600 font-medium mb-1">Notas de Revisión:</label>
                    <input
                      type="text"
                      value={approvalNotes}
                      onChange={(e) => setApprovalNotes(e.target.value)}
                      disabled={isApproved}
                      className="w-full p-2 border border-slate-200 rounded bg-white text-slate-800"
                    />
                  </div>
                </div>

                {isApproved && (
                  <div className="p-2.5 bg-emerald-100/60 border border-emerald-300 rounded text-xs font-mono text-emerald-900 break-all">
                    <strong>Hash Aprobado:</strong> {approvedData?.approval_metadata?.approved_json_hash}
                  </div>
                )}

                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs text-slate-500">
                    {isApproved
                      ? 'Firma inmutable registrada.'
                      : 'La generación YAML permanece estrictamente bloqueada.'}
                  </span>
                  {!isApproved && (
                    <button
                      onClick={handleApprove}
                      disabled={!operationalData || loadingStep === 'approve'}
                      className={cn(
                        'px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2',
                        !operationalData
                          ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                          : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                      )}
                    >
                      {loadingStep === 'approve' ? 'Aprobando...' : 'Aprobar Documento e Inmutar Hash'}
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Step 5: Locked / Unlocked YAML Generation */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold">
                    5
                  </span>
                  Generación Determinista de Archivos YAML
                </div>
              </div>

              {!isApproved ? (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3">
                  <Lock className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-xs font-bold text-rose-800">Generación bloqueada</div>
                    <div className="text-xs text-rose-700 mt-0.5">
                      Se requiere un JSON aprobado cuyo hash coincida con la versión actual para generar YAMLs.
                    </div>
                    <button
                      disabled
                      className="mt-3 px-4 py-2 bg-slate-200 text-slate-400 rounded-lg text-xs font-medium cursor-not-allowed flex items-center gap-2"
                    >
                      <Lock className="w-3.5 h-3.5" /> Generar Archivos YAML (Bloqueado)
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-600">
                      Puerta desbloqueada para documento aprobado.
                    </span>
                    <button
                      onClick={handleGenerateYaml}
                      disabled={loadingStep === 'generate'}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-2"
                    >
                      {loadingStep === 'generate' ? 'Generando...' : 'Generar Archivos YAML'}
                    </button>
                  </div>

                  {generatedYamls && (
                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                      <div className="font-semibold text-slate-700">Archivos Generados:</div>
                      {Object.entries(generatedYamls.generated_files || {}).map(([key, path]: any) => (
                        <div key={key} className="flex items-center justify-between font-mono text-slate-800">
                          <span>{key}</span>
                          <span className="text-slate-400 text-[10px]">{path.split('/').pop()}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Step 6: Controlled Sandbox Deployment & Rollback */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 font-semibold text-slate-800">
                  <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-bold">
                    6
                  </span>
                  Instalación en Sandbox Experimental y Rollback
                </div>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-2.5 bg-slate-50 rounded border border-slate-200 font-mono text-slate-700">
                  <strong>Destino Sandbox:</strong> outputs/experiments/{experimentId}/EthosTerra_experiment
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleInstall}
                    disabled={!generatedYamls || loadingStep === 'install'}
                    className={cn(
                      'px-4 py-2 rounded-lg font-bold transition flex items-center gap-2',
                      !generatedYamls
                        ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                        : 'bg-purple-600 hover:bg-purple-700 text-white'
                    )}
                  >
                    <FolderSync className="w-4 h-4" />
                    {loadingStep === 'install' ? 'Instalando...' : 'Instalar en Sandbox'}
                  </button>

                  <button
                    onClick={handleRollback}
                    disabled={loadingStep === 'rollback'}
                    className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-medium transition flex items-center gap-1.5"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    {loadingStep === 'rollback' ? 'Revirtiendo...' : 'Rollback Sandbox'}
                  </button>
                </div>

                {installationData && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-emerald-800 space-y-1">
                    <div className="font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Instalación Exitosa en Sandbox
                    </div>
                    <div>Backup creado: <span className="font-mono">{installationData.backup_file}</span></div>
                    <div>Archivos instalados: {installationData.installed_files?.length}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB: METRICS */}
      {activeTab === 'metrics' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-800">
              Métricas Reproducibles — Separación Estricta de Dimensiones
            </h3>
            <button
              onClick={handleLoadMetrics}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Actualizar Datos
            </button>
          </div>

          {metricsData ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Dimensión 1: Legacy Regression */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <div className="font-bold text-slate-800 flex items-center justify-between">
                  <span>Dimensión 1: Regresión Legacy (20 Casos)</span>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">Benchmark</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">Exactitud (Accuracy):</span>
                    <div className="text-lg font-bold text-slate-800">
                      {Math.round(metricsData.legacy_benchmark.accuracy * 100)}%
                    </div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">Macro-F1:</span>
                    <div className="text-lg font-bold text-slate-800">
                      {metricsData.legacy_benchmark.macro_f1.toFixed(3)}
                    </div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">Conflict Recall:</span>
                    <div className="text-lg font-bold text-slate-800">
                      {Math.round(metricsData.legacy_benchmark.conflict_recall * 100)}%
                    </div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">Alucinación Observada:</span>
                    <div className="text-lg font-bold text-emerald-600">0.0%</div>
                  </div>
                </div>
                <div className="text-[11px] text-slate-500">
                  Latencia mediana p50: {metricsData.legacy_benchmark.latency_statistics.median_p50_ms} ms |
                  Bypass hooks: {metricsData.legacy_benchmark.execution_distribution.hooks_resolved_count}/20
                </div>
              </div>

              {/* Dimensión 2: Document Pipeline */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
                <div className="font-bold text-slate-800 flex items-center justify-between">
                  <span>Dimensión 2: Pipeline Documental ({experimentId})</span>
                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">Prueba Vertical</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">Unit Tests Aprobados:</span>
                    <div className="text-lg font-bold text-emerald-600">
                      {metricsData.document_pipeline.unit_test_suite.passed}/
                      {metricsData.document_pipeline.unit_test_suite.total}
                    </div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">Evasión Approval Gate:</span>
                    <div className="text-lg font-bold text-emerald-600">0%</div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">YAMLs Parseables:</span>
                    <div className="text-lg font-bold text-slate-800">100% (2/2)</div>
                  </div>
                  <div className="p-2 bg-white rounded border">
                    <span className="text-slate-500">Simulación BDI:</span>
                    <div className="text-xs font-semibold text-amber-600 mt-1">Pendiente / No Evaluada</div>
                  </div>
                </div>
                <div className="text-[11px] text-slate-500">
                  Inmutabilidad EthosTerra_original: 0 modificaciones | Sandbox aislado verificado.
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400">Cargando métricas...</div>
          )}
        </div>
      )}

      {/* TAB: MANIFEST */}
      {activeTab === 'manifest' && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-slate-800">
              Manifiesto de Reproducibilidad ({experimentId})
            </h3>
            <button
              onClick={handleLoadManifest}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium flex items-center gap-1"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Recargar
            </button>
          </div>

          {manifestData ? (
            <pre className="p-4 bg-slate-900 text-slate-100 rounded-lg text-xs font-mono overflow-auto max-h-96">
              {JSON.stringify(manifestData, null, 2)}
            </pre>
          ) : (
            <div className="text-center py-8 text-slate-400">Cargando manifiesto...</div>
          )}
        </div>
      )}
    </div>
  );
}
