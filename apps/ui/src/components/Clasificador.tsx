import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Copy,
  Loader2,
  ShieldAlert,
  Database,
  Sparkles,
  Cpu,
  FileCode,
  Sliders,
  Lock,
} from 'lucide-react';
import { cn } from '../lib/utils';

type ProposalStatus = "propuesta" | "validada" | "requires_review" | "rejected";
type CaseType = "pure" | "conflict" | "unclear";

interface ProposalResponse {
  trace_id: string;
  status: ProposalStatus;
  case_type: CaseType;
  data: any;
  validation_errors: string[];
  requires_human_review: boolean;
  metadata: {
    model_name: string;
    model_digest: string;
    latency_ms: number;
    tokens_used: number;
  };
}

const DEFAULT_JSON = `{
  "simulator_id": "ST-Norte",
  "timestamp": "2026-09-08T10:00:00Z",
  "context_data": {
    "presion": 300,
    "estado_valvula": "abierta"
  }
}`;

const mockAnalyze = async (_payload: any): Promise<ProposalResponse> => {
  await new Promise(resolve => setTimeout(resolve, 1500));
  return {
    trace_id: "a1b2c3d4-e5f6-47a8-b9c0-1234567890ab",
    status: "requires_review",
    case_type: "conflict",
    data: {
      titulo: "Contradicción en presión vs válvula",
      colisiones: [
        { fuente: "Sensor_1", conflicto: "Lectura de presión excesivamente alta" },
        { fuente: "Valvula_A", conflicto: "Reporta abierta pese a alta presión" }
      ]
    },
    validation_errors: ["'presion' no indica unidad métrica."],
    requires_human_review: true,
    metadata: {
      model_name: "gemma4:e4b",
      model_digest: "sha256:8f43b...",
      latency_ms: 1250,
      tokens_used: 124
    }
  };
};

export default function Clasificador() {
  const [jsonInput, setJsonInput] = useState(DEFAULT_JSON);
  const [isValidJson, setIsValidJson] = useState(true);
  const [showTechData, setShowTechData] = useState(false);

  const mutation = useMutation({
    mutationFn: mockAnalyze, 
  });

  const handleJsonChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setJsonInput(val);
    try {
      JSON.parse(val);
      setIsValidJson(true);
    } catch {
      setIsValidJson(false);
    }
  };

  const handleAnalyze = () => {
    if (!isValidJson) return;
    mutation.mutate(JSON.parse(jsonInput));
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[80vh]">
      {/* Panel Izquierdo: Entrada */}
      <div className="flex flex-col bg-white rounded-2xl shadow-xs border border-slate-200 overflow-hidden">
        <div className="bg-slate-50/80 border-b border-slate-200 px-5 py-3.5 flex justify-between items-center">
          <h2 className="font-semibold text-sm flex items-center gap-2 text-slate-800">
            <Database className="w-4 h-4 text-blue-600" aria-hidden="true" />
            <span>Contexto de Entrada (Simulador)</span>
          </h2>
          <div className="flex items-center gap-2">
            {isValidJson ? (
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" /> JSON Válido
              </span>
            ) : (
              <span className="text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200/60 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <AlertCircle className="w-3 h-3 text-rose-600" /> JSON Inválido
              </span>
            )}
          </div>
        </div>
        <div className="p-5 flex-1 flex flex-col gap-4">
          <textarea
            value={jsonInput}
            onChange={handleJsonChange}
            className={cn(
              "flex-1 w-full bg-slate-950 text-slate-100 p-4 rounded-xl font-mono text-xs leading-relaxed resize-none focus:outline-none focus:ring-2 border",
              isValidJson ? "focus:ring-blue-500/50 border-slate-800" : "focus:ring-red-500 border-red-500"
            )}
            spellCheck="false"
          />
          <button
            onClick={handleAnalyze}
            disabled={!isValidJson || mutation.isPending}
            className="w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 disabled:bg-blue-300 text-white font-semibold py-3 rounded-xl flex justify-center items-center gap-2 shadow-xs transition-all duration-150 cursor-pointer disabled:cursor-not-allowed"
          >
            {mutation.isPending ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Analizando Contexto...</>
            ) : (
              <><Sparkles className="w-4 h-4" /> Analizar Contexto</>
            )}
          </button>
        </div>
      </div>

      {/* Panel Derecho: Evaluación */}
      <div className="flex flex-col bg-white rounded-2xl shadow-xs border border-slate-200 overflow-hidden">
        <div className="bg-slate-50/80 border-b border-slate-200 px-5 py-3.5 flex justify-between items-center">
          <h2 className="font-semibold text-sm flex items-center gap-2 text-slate-800">
            <Cpu className="w-4 h-4 text-indigo-600" aria-hidden="true" />
            <span>Evaluación del Micro-LLM Soberano</span>
          </h2>
          <span className="text-[11px] font-mono font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
            ai/gemma4:E4B
          </span>
        </div>
        
        <div className="p-5 flex-1 flex flex-col gap-6 overflow-y-auto">
          {!mutation.data && !mutation.isPending && (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <div className="size-12 rounded-2xl bg-slate-100 border border-slate-200/80 flex items-center justify-center mb-3 text-slate-400">
                <ShieldAlert className="w-6 h-6 stroke-[1.5]" />
              </div>
              <h3 className="text-sm font-semibold text-slate-700 mb-1">Esperando Contexto para Auditar</h3>
              <p className="text-xs text-slate-500 max-w-xs">
                Ingresa los parámetros de telemetría y pulsa "Analizar Contexto" para evaluar casos puros y conflictivos.
              </p>
            </div>
          )}

          {mutation.isPending && (
             <div className="flex-1 flex flex-col items-center justify-center text-blue-500 h-full">
               <Loader2 className="w-10 h-10 animate-spin mb-4" />
               <p className="animate-pulse">Generando inferencia local...</p>
             </div>
          )}

          {mutation.data && (
            <>
              {/* Badges de Estado */}
              <div className="flex flex-wrap gap-2">
                <span className={cn(
                  "px-3 py-1 text-sm font-semibold rounded-full border",
                  mutation.data.status === 'requires_review' ? "bg-yellow-50 text-yellow-700 border-yellow-200" : 
                  mutation.data.status === 'validada' ? "bg-green-50 text-green-700 border-green-200" :
                  "bg-slate-50 text-slate-700 border-slate-200"
                )}>
                  Estado: {mutation.data.status.toUpperCase()}
                </span>
                <span className={cn(
                  "px-3 py-1 text-sm font-semibold rounded-full border",
                  mutation.data.case_type === 'conflict' ? "bg-orange-50 text-orange-700 border-orange-200" : 
                  "bg-blue-50 text-blue-700 border-blue-200"
                )}>
                  Tipo: {mutation.data.case_type === 'conflict' ? 'CONFLICTIVO' : mutation.data.case_type.toUpperCase()}
                </span>
              </div>

              {/* Advertencias */}
              {mutation.data.validation_errors.length > 0 && (
                <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-md">
                  <h3 className="text-amber-800 font-semibold flex items-center gap-2 text-sm mb-1">
                    <AlertCircle className="w-4 h-4" /> Advertencias Semánticas
                  </h3>
                  <ul className="list-disc list-inside text-sm text-amber-700">
                    {mutation.data.validation_errors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Desglose de la Propuesta */}
              <div className="border border-slate-200 rounded-xl overflow-hidden shadow-xs">
                <div className="bg-slate-50/80 px-4 py-2.5 border-b border-slate-200 font-semibold text-xs text-slate-800 flex items-center gap-2">
                  <FileCode className="w-4 h-4 text-blue-600" />
                  <span>Desglose de la Propuesta: {mutation.data.data.titulo}</span>
                </div>
                <div className="p-4 bg-white">
                  {mutation.data.data.colisiones && (
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-50 text-slate-600 border-b border-slate-100">
                        <tr>
                          <th className="px-3 py-2 font-semibold">Fuente</th>
                          <th className="px-3 py-2 font-semibold">Conflicto</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {mutation.data.data.colisiones.map((col: any, i: number) => (
                          <tr key={i}>
                            <td className="px-3 py-2 font-mono text-xs text-slate-600">{col.fuente}</td>
                            <td className="px-3 py-2 text-slate-800">{col.conflicto}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>

              {/* Acordeón de Datos Técnicos */}
              <div className="border border-slate-200 rounded-xl overflow-hidden shadow-xs">
                <button 
                  onClick={() => setShowTechData(!showTechData)}
                  className="w-full bg-slate-50/80 px-4 py-3 flex justify-between items-center hover:bg-slate-100/80 transition-colors"
                >
                  <span className="font-semibold text-xs text-slate-700 flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-slate-500" />
                    <span>Datos Técnicos y Auditoría</span>
                  </span>
                  <ChevronDown className={cn("w-4 h-4 text-slate-500 transition-transform", showTechData && "rotate-180")} />
                </button>
                
                {showTechData && (
                  <div className="p-4 bg-white border-t border-slate-200 flex flex-col gap-3 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Trace ID:</span>
                      <div className="flex items-center gap-2">
                        <code className="bg-slate-100 px-2 py-1 rounded text-[11px] font-mono">{mutation.data.trace_id}</code>
                        <button onClick={() => handleCopy(mutation.data.trace_id)} className="text-slate-400 hover:text-blue-600 p-1">
                          <Copy className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Modelo:</span>
                      <span className="font-mono text-[11px] bg-slate-100 px-2 py-0.5 rounded">{mutation.data.metadata.model_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Latencia:</span>
                      <span className="text-slate-700 font-mono">{mutation.data.metadata.latency_ms} ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Tokens:</span>
                      <span className="text-slate-700 font-mono">{mutation.data.metadata.tokens_used}</span>
                    </div>
                    <button 
                      onClick={() => handleCopy(JSON.stringify(mutation.data.data, null, 2))}
                      className="mt-2 text-blue-600 text-xs font-semibold hover:underline text-left cursor-pointer"
                    >
                      Copiar JSON Crudo de la Propuesta
                    </button>
                  </div>
                )}
              </div>

              {/* Botón de Aprobación */}
              <div className="mt-auto pt-4">
                <button disabled className="w-full bg-slate-100 text-slate-400 border border-slate-200 font-semibold py-3 rounded-xl flex justify-center items-center gap-2 cursor-not-allowed text-xs">
                  <Lock className="w-4 h-4 text-slate-400" />
                  <span>Aprobar Propuesta (Deshabilitado - Sem 5)</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
