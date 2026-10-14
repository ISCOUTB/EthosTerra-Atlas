import { useState, type ReactNode } from 'react';
import {
  Check,
  Lock,
  ShieldCheck,
  FolderSync,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { EpistemicBadge } from './EpistemicBadge';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Field, Input, Textarea } from './ui/Field';
import { Mono } from './ui/Mono';
import { StatePanel } from './ui/StatePanel';
import { cn } from '../lib/utils';

const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/v2';

const SAMPLE_DIARY = `El campesino peasant_01 indica que para la próxima temporada de siembra es indispensable preparar el terreno adecuadamente. Para llevar a cabo esta labor se requiere contar con las herramientas necesarias en la parcela.`;

export default function DocumentPipelineView() {
  // Navigation & Experiment state
  const [experimentId] = useState('exp_vertical_001');
  const [docId] = useState('doc_diario_001');
  const [sourceText, setSourceText] = useState(SAMPLE_DIARY);

  // Step Statuses
  const [ingestData, setIngestData] = useState<any>(null);
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [operationalData, setOperationalData] = useState<any>(null);
  const [approvedData, setApprovedData] = useState<any>(null);
  const [generatedYamls, setGeneratedYamls] = useState<any>(null);
  const [installationData, setInstallationData] = useState<any>(null);

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
      const extractedActor = analysisData?.extracted_knowledge?.actor_alias?.value;
      const hasConflicts = (analysisData?.extracted_knowledge?.detected_conflicts?.length ?? 0) > 0;
      const isUnknownIntention = analysisData?.extracted_knowledge?.intentions?.[0]?.status === 'unknown';
      const derivedTipoCaso: 'puro' | 'conflicto' = (hasConflicts || isUnknownIntention) ? 'conflicto' : 'puro';

      const payload: { tipo_caso: 'puro' | 'conflicto'; actor_alias?: string } = {
        tipo_caso: derivedTipoCaso,
      };
      if (extractedActor) {
        payload.actor_alias = extractedActor;
      }

      const res = await fetch(`${API_BASE}/documents/${docId}/structure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
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

  const isApproved = operationalData?.status === 'Aprobado' && operationalData?.review_status === 'approved';

  // Presentación del stepper: el estado de cada paso se deriva de los datos existentes.
  const stepDone = [
    Boolean(ingestData),
    Boolean(analysisData),
    Boolean(operationalData),
    isApproved,
    Boolean(generatedYamls),
    Boolean(installationData),
  ];
  const firstOpen = stepDone.indexOf(false);
  const statusOf = (i: number): StepStatus => {
    if (stepDone[i]) return 'completed';
    if (i === firstOpen) return 'active';
    if (i === 4 && !isApproved) return 'blocked';
    return 'pending';
  };
  const primaryFor = (i: number) => (statusOf(i) === 'active' ? 'primary' : 'secondary') as 'primary' | 'secondary';

  const approval = approvedData?.approval_metadata ?? operationalData?.approval_metadata;
  const yamlCount = Object.keys(generatedYamls?.generated_files || {}).length;
  const analysis = analysisData?.extracted_knowledge;
  const goalArtifact = operationalData?.artifacts?.find((a: any) => a.artifact_type === 'goal');
  const planArtifact = operationalData?.artifacts?.find((a: any) => a.artifact_type === 'plan');
  const goalSpec = goalArtifact?.content;
  const planSpec = planArtifact?.content;
  const planSteps = planSpec?.steps || [];

  return (
    <div className="mx-auto w-full max-w-[1100px] space-y-8">
      <div className="border-b border-hairline pb-6">
        <div className="space-y-2">
          <Badge tone="puro" className="gap-1.5">
            <ShieldCheck className="size-3.5" aria-hidden="true" />
            EthosTerra_original: solo lectura
          </Badge>
          <h2 className="text-[21px] leading-tight font-semibold tracking-tight">
            Traductor documental a especificaciones eBDI
          </h2>
          <p className="max-w-2xl text-ink-subtle">
            Extracción epistemológica, aprobación humana inmutable y sandbox en{' '}
            <Mono className="text-ink-subtle">outputs/experiments/{experimentId}/EthosTerra_experiment</Mono>
          </p>
        </div>
      </div>

      {errorMessage && <StatePanel state="error" title={errorMessage} className="p-4" />}
      {successMessage && <StatePanel state="success" title={successMessage} className="p-4" />}

      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_280px] lg:items-start">
        <ol>
          {/* 1. Ingesta */}
          <StepItem
            n={1}
            title="Fuente documental y normalización"
            description="Normaliza el texto fuente y registra un hash SHA-256 inmutable del documento."
            status={statusOf(0)}
            summary={
              ingestData && (
                <>
                  SHA-256 <Mono>{ingestData.sha256_hash.slice(0, 16)}…</Mono> · {ingestData.char_count} caracteres
                </>
              )
            }
          >
            <div className="space-y-4">
              <Field id="source-text" label="Texto fuente">
                {(control) => (
                  <Textarea
                    {...control}
                    value={sourceText}
                    onChange={(e) => setSourceText(e.target.value)}
                    rows={4}
                    placeholder="Pegue aquí el extracto de diario, entrevista o documento..."
                  />
                )}
              </Field>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setSourceText(SAMPLE_DIARY)}
                  className="flex min-h-8 items-center gap-1.5 text-primary hover:underline"
                >
                  <Sparkles className="size-4" aria-hidden="true" /> Cargar muestra de campesino
                </button>
                <Button
                  variant={primaryFor(0)}
                  size={statusOf(0) === 'active' ? 'md' : 'sm'}
                  onClick={handleIngest}
                  loading={loadingStep === 'ingest'}
                >
                  {loadingStep === 'ingest' ? 'Procesando...' : 'Ingerir y normalizar'}
                </Button>
              </div>
            </div>
          </StepItem>

          {/* 2. Extracción epistemológica */}
          <StepItem
            n={2}
            title="Extracción epistemológica y trazabilidad"
            description="Extrae intención, deseos y requerimientos, cada uno con su evidencia textual."
            status={statusOf(1)}
            summary={
              analysis &&
              `${analysisData.evidence_spans?.length ?? 0} evidencias · ${analysis.intentions?.length ?? 0} intenciones · ${analysis.desires?.length ?? 0} deseos · ${analysis.requirements?.length ?? 0} requerimientos`
            }
          >
            <div className="space-y-4">
              {analysisData && (
                <>
                  <figure className="border-l-2 border-hairline pl-4">
                    <figcaption className="text-xs text-ink-subtle">
                      Evidencia textual (fragmento <Mono>frag_01</Mono>)
                    </figcaption>
                    <blockquote className="mt-1 italic">
                      "{analysisData.evidence_spans?.[0]?.text_quote}"
                    </blockquote>
                  </figure>

                  <dl className="divide-y divide-hairline">
                    <EpistemicRow label="Actor alias">
                      {analysis.actor_alias?.value ? (
                        <Mono>{analysis.actor_alias.value}</Mono>
                      ) : (
                        <span className="text-ink-subtle italic">No declarado</span>
                      )}
                      <EpistemicBadge
                        status={analysis.actor_alias?.status}
                        evidenceRef={analysis.actor_alias?.evidence_ref}
                      />
                    </EpistemicRow>
                    <EpistemicRow label="Intención central">
                      <span className="font-semibold">{analysis.intentions?.[0]?.value || 'No identificada'}</span>
                      <EpistemicBadge
                        status={analysis.intentions?.[0]?.status}
                        evidenceRef={analysis.intentions?.[0]?.evidence_ref}
                      />
                    </EpistemicRow>
                    <EpistemicRow label="Deseo subyacente">
                      <span>{analysis.desires?.[0]?.value || 'No inferido'}</span>
                      <EpistemicBadge
                        status={analysis.desires?.[0]?.status}
                        evidenceRef={analysis.desires?.[0]?.evidence_ref}
                      />
                    </EpistemicRow>
                    <EpistemicRow label="Requerimientos operativos">
                      <div className="flex flex-col items-end gap-1.5">
                        {analysis.requirements?.length > 0 ? (
                          analysis.requirements.map((req: any, idx: number) => (
                            <div key={idx} className="flex flex-wrap items-center justify-end gap-2">
                              <Mono>{typeof req.value === 'object' ? JSON.stringify(req.value) : req.value}</Mono>
                              <EpistemicBadge status={req.status} rationale={req.rationale} />
                            </div>
                          ))
                        ) : (
                          <span className="text-ink-subtle italic">Ninguno declarado</span>
                        )}
                      </div>
                    </EpistemicRow>
                    {analysis.detected_conflicts?.length > 0 && (
                      <EpistemicRow label="Conflictos / Inyecciones">
                        <div className="flex flex-col items-end gap-1 text-xs text-status-conflictivo-fg">
                          {analysis.detected_conflicts.map((c: any, idx: number) => (
                            <span key={idx}>
                              {c.value}: {c.rationale}
                            </span>
                          ))}
                        </div>
                      </EpistemicRow>
                    )}
                    <EpistemicRow label="Contexto territorial">
                      <span className="text-ink-subtle italic">No especificado</span>
                      <EpistemicBadge
                        status={analysis.territory_context?.status}
                        rationale={analysis.territory_context?.rationale}
                      />
                    </EpistemicRow>
                    <EpistemicRow label="Estado afectivo (felicidad)">
                      <span className="text-ink-subtle italic">Desconocido</span>
                      <EpistemicBadge status="unknown" />
                    </EpistemicRow>
                  </dl>
                </>
              )}
              <Button
                variant={primaryFor(1)}
                size={statusOf(1) === 'active' ? 'md' : 'sm'}
                onClick={handleExtract}
                disabled={!ingestData}
                loading={loadingStep === 'extract'}
              >
                {loadingStep === 'extract' ? 'Extrayendo...' : 'Extraer epistemología'}
              </Button>
            </div>
          </StepItem>

          {/* 3. Estructuración */}
          <StepItem
            n={3}
            title="Estructuración operativa (GoalSpec y PlanSpec)"
            description="Produce el GoalSpec y el PlanSpec validados contra el catálogo de acciones."
            status={statusOf(2)}
            summary={
              operationalData && (
                <>
                  {operationalData.artifacts?.length ?? 0} artefactos
                  {goalSpec?.id && (
                    <>
                      {' '}· <Mono>{goalSpec.id}</Mono>
                    </>
                  )}
                  {planSpec?.id && (
                    <>
                      {' '}· <Mono>{planSpec.id}</Mono>
                    </>
                  )}
                  {planSteps.length > 0 && ` · ${planSteps.length} acciones válidas`}
                </>
              )
            }
          >
            <div className="space-y-4">
              {operationalData && (
                <div className="space-y-2">
                  {operationalData.requires_human_review && (
                    <p className="text-xs text-status-conflictivo-fg">
                      Este documento requiere revisión humana (
                      {operationalData.validation_status?.blocking_errors?.join(', ') || 'conflicto o ambigüedad'}).
                    </p>
                  )}
                  {(operationalData.artifacts?.length ?? 0) > 0 ? (
                    <ul className="list-disc space-y-1 pl-5 text-ink-muted">
                      {goalSpec && (
                        <li>
                          <Mono>GoalSpec</Mono>: <Mono>{goalSpec.id}</Mono> ({goalSpec.display_name}) · plan_ref:{' '}
                          <Mono>{goalSpec.plan_ref}</Mono>
                        </li>
                      )}
                      {planSpec && (
                        <li>
                          <Mono>PlanSpec</Mono>: <Mono>{planSpec.id}</Mono> ({planSteps.length} pasos:{' '}
                          {planSteps.map((s: any, idx: number) => (
                            <span key={s.id || idx}>
                              {idx > 0 && ', '}
                              <Mono>{s.action}</Mono>
                            </span>
                          ))}
                          )
                        </li>
                      )}
                      <li>
                        {operationalData.validation_status?.has_blocking_errors
                          ? 'Errores de validación detectados'
                          : `${planSteps.length}/${planSteps.length} acciones validadas contra el catálogo, existentes y tipadas`}
                      </li>
                    </ul>
                  ) : (
                    <p className="text-sm italic text-ink-subtle">
                      No se generaron artefactos automáticos debido a revisión requerida.
                    </p>
                  )}
                </div>
              )}
              <Button
                variant={primaryFor(2)}
                size={statusOf(2) === 'active' ? 'md' : 'sm'}
                onClick={handleStructure}
                disabled={!analysisData}
                loading={loadingStep === 'structure'}
              >
                {loadingStep === 'structure' ? 'Estructurando...' : 'Estructurar objetivos'}
              </Button>
            </div>
          </StepItem>

          {/* 4. Punto de control: aprobación humana */}
          <StepItem
            n={4}
            gate
            title="Aprobación humana"
            description="Registra aprobador, fecha y hash canónico. Sin esta firma no se generan archivos."
            status={statusOf(3)}
          >
            {isApproved ? (
              <dl className="space-y-3">
                <div>
                  <dt className="text-xs text-ink-subtle">Hash canónico</dt>
                  <dd>
                    <Mono>{approval?.approved_json_hash}</Mono>
                  </dd>
                </div>
                <div className="flex flex-wrap gap-x-8 gap-y-3">
                  <div>
                    <dt className="text-xs text-ink-subtle">Aprobador</dt>
                    <dd>
                      <Mono>{approval?.approver_id ?? approverId}</Mono>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-ink-subtle">Fecha</dt>
                    <dd>{formatDate(approval?.approved_at) ?? 'No registrada'}</dd>
                  </div>
                </div>
                <p className="flex items-center gap-1.5 text-ink-muted">
                  <Check className="size-4" aria-hidden="true" /> Firma inmutable registrada.
                </p>
              </dl>
            ) : (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field id="approver-id" label="Investigador">
                    {(control) => (
                      <Input
                        {...control}
                        type="text"
                        className="font-mono"
                        value={approverId}
                        onChange={(e) => setApproverId(e.target.value)}
                      />
                    )}
                  </Field>
                  <Field id="approval-notes" label="Notas de revisión">
                    {(control) => (
                      <Input
                        {...control}
                        type="text"
                        value={approvalNotes}
                        onChange={(e) => setApprovalNotes(e.target.value)}
                      />
                    )}
                  </Field>
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="flex items-center gap-1.5 text-status-conflictivo-fg">
                    <Lock className="size-4 shrink-0" aria-hidden="true" />
                    La generación de YAML permanece bloqueada hasta aprobar.
                  </p>
                  <Button
                    variant="primary"
                    onClick={handleApprove}
                    disabled={!operationalData}
                    loading={loadingStep === 'approve'}
                  >
                    {loadingStep === 'approve' ? 'Aprobando...' : 'Aprobar y fijar hash'}
                  </Button>
                </div>
              </div>
            )}
          </StepItem>

          {/* 5. Generación de YAML */}
          <StepItem
            n={5}
            title="Generación determinista de archivos YAML"
            description="Genera los archivos YAML de forma determinista a partir del JSON aprobado."
            status={statusOf(4)}
            blockedNote="Bloqueado hasta que el paso 4 registre la aprobación. Requiere un JSON aprobado cuyo hash coincida con la versión actual."
            summary={
              generatedYamls && (
                <>
                  {yamlCount} archivos YAML · <Mono>outputs/experiments/{experimentId}/yaml/</Mono>
                </>
              )
            }
          >
            <div className="space-y-4">
              {generatedYamls && (
                <ul className="space-y-2">
                  {Object.entries(generatedYamls.generated_files || {}).map(([key, path]) => (
                    <li key={key} className="rounded-lg border border-hairline bg-canvas px-3 py-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <Mono>{key}</Mono>
                        <Mono>{String(path).split('/').pop()}</Mono>
                      </div>
                      <Mono className="block truncate text-ink-subtle">{String(path)}</Mono>
                    </li>
                  ))}
                </ul>
              )}
              <Button
                variant={primaryFor(4)}
                size={statusOf(4) === 'active' ? 'md' : 'sm'}
                onClick={handleGenerateYaml}
                loading={loadingStep === 'generate'}
              >
                {loadingStep === 'generate' ? 'Generando...' : 'Generar archivos YAML'}
              </Button>
            </div>
          </StepItem>

          {/* 6. Instalación y rollback */}
          <StepItem
            n={6}
            isLast
            title="Instalación en sandbox experimental y rollback"
            description="Copia los YAML a la sandbox experimental con respaldo previo y rollback."
            status={statusOf(5)}
            pendingAction={
              <Button variant="secondary" size="sm" onClick={handleRollback} loading={loadingStep === 'rollback'}>
                <RotateCcw className="size-4" aria-hidden="true" />
                {loadingStep === 'rollback' ? 'Revirtiendo...' : 'Rollback de sandbox'}
              </Button>
            }
            summary={
              installationData && (
                <>
                  {installationData.installed_files?.length} archivos instalados · respaldo{' '}
                  <Mono>{installationData.backup_file}</Mono>
                </>
              )
            }
          >
            <div className="space-y-4">
              <p className="text-ink-muted">
                Destino: <Mono>outputs/experiments/{experimentId}/EthosTerra_experiment</Mono>
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  variant={primaryFor(5)}
                  size={statusOf(5) === 'active' ? 'md' : 'sm'}
                  onClick={handleInstall}
                  disabled={!generatedYamls}
                  loading={loadingStep === 'install'}
                >
                  <FolderSync className="size-4" aria-hidden="true" />
                  {loadingStep === 'install' ? 'Instalando...' : 'Instalar en sandbox'}
                </Button>
                <Button variant="secondary" size="sm" onClick={handleRollback} loading={loadingStep === 'rollback'}>
                  <RotateCcw className="size-4" aria-hidden="true" />
                  {loadingStep === 'rollback' ? 'Revirtiendo...' : 'Rollback de sandbox'}
                </Button>
              </div>
              {installationData && (
                <p className="text-ink-muted">
                  Respaldo creado: <Mono>{installationData.backup_file}</Mono> · Archivos instalados:{' '}
                  {installationData.installed_files?.length}
                </p>
              )}
            </div>
          </StepItem>
        </ol>

        <aside aria-label="Resumen del documento actual" className="order-first lg:sticky lg:top-28 lg:order-last">
          <Card className="p-5">
            <h3 className="text-[17px] font-semibold">Documento actual</h3>
            <p className="mt-0.5">
              <Mono className="text-ink-subtle">{docId}</Mono>
            </p>
            <dl className="mt-4 space-y-4">
              <SummaryRow label="SHA-256">
                {ingestData ? <Mono>{ingestData.sha256_hash}</Mono> : dash}
              </SummaryRow>
              <SummaryRow label="Fragmentos de evidencia">
                {analysisData ? analysisData.evidence_spans?.length ?? 0 : dash}
              </SummaryRow>
              <SummaryRow label="Aprobación">
                {isApproved ? (
                  <Badge tone="puro">Aprobado</Badge>
                ) : operationalData ? (
                  <Badge tone="conflictivo">Pendiente de aprobación</Badge>
                ) : (
                  dash
                )}
              </SummaryRow>
              <SummaryRow label="Ruta de sandbox">
                {installationData ? <Mono>outputs/experiments/{experimentId}/EthosTerra_experiment</Mono> : dash}
              </SummaryRow>
            </dl>
          </Card>
        </aside>
      </div>
    </div>
  );
}

type StepStatus = 'pending' | 'active' | 'completed' | 'blocked';

const statusLabel: Record<StepStatus, string> = {
  pending: 'Pendiente',
  active: 'Activo',
  completed: 'Completado',
  blocked: 'Bloqueado',
};

const dateFormat = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'long' });

function formatDate(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : dateFormat.format(date);
}

const dash = <span className="text-ink-subtle">—</span>;

function SummaryRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ink-subtle">{label}</dt>
      <dd className="mt-0.5">{children}</dd>
    </div>
  );
}

function EpistemicRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 py-2">
      <dt className="text-ink-subtle">{label}</dt>
      <dd className="flex flex-wrap items-center justify-end gap-2">{children}</dd>
    </div>
  );
}

function StepMarker({ n, status, gate }: { n: number; status: StepStatus; gate: boolean }) {
  const base = 'flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold';
  const icon = 'size-4';

  if (gate) {
    return status === 'completed' ? (
      <span className={cn(base, 'bg-status-puro-fg text-white')}>
        <ShieldCheck className={icon} aria-hidden="true" />
      </span>
    ) : (
      <span className={cn(base, 'bg-status-conflictivo-fg text-white')}>
        <Lock className={icon} aria-hidden="true" />
      </span>
    );
  }
  if (status === 'completed') {
    return (
      <span className={cn(base, 'bg-ink text-white')}>
        <Check className={icon} aria-hidden="true" />
      </span>
    );
  }
  if (status === 'active') return <span className={cn(base, 'bg-primary text-white')}>{n}</span>;
  if (status === 'blocked') {
    return (
      <span className={cn(base, 'border border-hairline bg-parchment text-ink-subtle')}>
        <Lock className={icon} aria-hidden="true" />
      </span>
    );
  }
  return <span className={cn(base, 'border border-hairline bg-canvas text-ink-subtle')}>{n}</span>;
}

interface StepItemProps {
  n: number;
  title: string;
  description: string;
  status: StepStatus;
  /** Resultado en una línea, visible cuando el paso está colapsado. */
  summary?: ReactNode;
  /** Motivo normal de bloqueo (gris, con candado); no es un error. */
  blockedNote?: string;
  /** Acción que sigue disponible aunque el paso aún esté pendiente. */
  pendingAction?: ReactNode;
  /** Punto de control con tratamiento propio (Approval Gate). */
  gate?: boolean;
  isLast?: boolean;
  children?: ReactNode;
}

function StepItem({
  n,
  title,
  description,
  status,
  summary,
  blockedNote,
  pendingAction,
  gate = false,
  isLast = false,
  children,
}: StepItemProps) {
  const muted = status === 'pending' || status === 'blocked';
  const approved = status === 'completed';

  return (
    <li aria-current={status === 'active' ? 'step' : undefined} className="flex gap-4">
      <div className="flex flex-col items-center">
        <StepMarker n={n} status={status} gate={gate} />
        {!isLast && <span aria-hidden="true" className="my-2 w-px flex-1 bg-hairline" />}
      </div>

      <div className={cn('min-w-0 flex-1', !isLast && 'pb-8')}>
        {gate ? (
          <div
            className={cn(
              'rounded-xl border p-5',
              approved
                ? 'border-status-puro-fg/30 bg-status-puro-bg/60'
                : 'border-status-conflictivo-fg/30 bg-status-conflictivo-bg/60',
            )}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <p className="text-xs text-ink-subtle">Punto de control</p>
                <h3 className="text-[17px] font-semibold">
                  <span className="sr-only">Paso {n}: </span>
                  {title}
                </h3>
              </div>
              <Badge tone={approved ? 'puro' : 'conflictivo'}>
                {approved ? 'Aprobado' : 'Pendiente de aprobación'}
              </Badge>
            </div>
            <p className="mt-1 text-ink-muted">{description}</p>
            {(status === 'active' || approved) && <div className="mt-4">{children}</div>}
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-baseline justify-between gap-x-4">
              <h3 className={cn('text-[17px] font-semibold', muted ? 'text-ink-subtle' : 'text-ink')}>
                <span className="sr-only">Paso {n}: </span>
                {title}
              </h3>
              <span className={cn('text-xs', status === 'active' ? 'font-semibold text-primary' : 'text-ink-subtle')}>
                {statusLabel[status]}
              </span>
            </div>
            <p className="mt-0.5 text-ink-subtle">{description}</p>

            {status === 'blocked' && blockedNote && (
              <p className="mt-2 flex items-start gap-1.5 text-ink-subtle">
                <Lock className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
                {blockedNote}
              </p>
            )}
            {status === 'pending' && pendingAction && <div className="mt-2">{pendingAction}</div>}
            {status === 'active' && <div className="mt-4">{children}</div>}
            {status === 'completed' && (
              <>
                {summary && <p className="mt-2">{summary}</p>}
                {children && (
                  <details className="mt-2">
                    <summary className="w-fit cursor-pointer text-primary hover:underline">Ver detalle</summary>
                    <div className="mt-3">{children}</div>
                  </details>
                )}
              </>
            )}
          </>
        )}
      </div>
    </li>
  );
}
