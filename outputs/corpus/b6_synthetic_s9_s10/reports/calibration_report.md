# Reporte de Calibración de Prompts eBDI (Semanas S9–S10)

**Dataset ID:** `b6_synthetic_s9_s10_v1`
**Modelo Oficial:** `ai/gemma4:E4B`
**Model Digest:** `sha256:533eb3ccab62c3c296657d0f5bd92d63a4858e9fe131fd20c153872c7c3e557a`
**Fecha UTC:** `2026-10-06T22:07:59.739105+00:00`
**Ámbito Territorial:** Montes de María, Bolívar

---

## 1. Resumen Ejecutivo y Criterios de Aceptación

| Criterio | Meta Exigida | Resultado Baseline | Resultado eBDI Rules | Resultado Strict Abstention | Estado |
|---|---|---|---|---|---|
| **Tasa de JSON Válido** | **100% (1.00)** | 100.0% | 100.0% | 100.0% | **CUMPLIDO** |
| **Falsos Positivos de Colisión** | **≤ 10% (0.10)** | 0.0% | 0.0% | 0.0% | **CUMPLIDO** |
| **Accuracy Global** | N/A | 100.0% | 100.0% | 100.0% | **CALIBRADO** |
| **Invarianza ante Sesgos** | 100% | - | - | 100.0% | **CUMPLIDO** |

---

## 2. Comparativa Cuantitativa de Prompts

### A. Prompt Baseline (`baseline`)
- **Accuracy:** 100.0%
- **Latencia promedio:** 104005.33 ms
- **Falsos positivos de colisión:** 0 (0.0%)

### B. Prompt con Reglas eBDI (`ebdi_rules`)
- **Accuracy:** 100.0%
- **Latencia promedio:** 112598.37 ms
- **Falsos positivos de colisión:** 0 (0.0%)

### C. Prompt con Reglas y Control de Abstención (`strict_abstention`)
- **Accuracy:** 100.0%
- **Latencia promedio:** 88699.41 ms
- **Falsos positivos de colisión:** 0 (0.0%)
- **Métricas por clase:**
  - `pure`: Precision=1.0, Recall=1.0, F1=1.0
  - `conflict`: Precision=1.0, Recall=1.0, F1=1.0
  - `insufficient`: Precision=1.0, Recall=1.0, F1=1.0

---

## 3. Mitigación de Sesgos Contrafactuales
Se evaluaron pares idénticos alterando únicamente variables protegidas o contextuales:
- **Género (Campesina Rosalba vs Campesino Manuel):** Clasificación idéntica (invariante).
- **Municipio (El Carmen de Bolívar vs María La Baja):** Clasificación idéntica (invariante).
- **Cultivo (Maíz tradicional vs Frijol cuarentano):** Clasificación idéntica (invariante).

---

## 4. Limitaciones Metodológicas Inmutables
1. Este banco es **estrictamente sintético** y diseñado para calibración algorítmica y sensibilidad de prompts.
2. **No sustituye** el trabajo de campo real ni entrevistas con productores campesinos.
3. No demuestra validez ecológica ni constituye evidencia empírica territorial.
4. **No autoriza el cierre de B6** ni califica para el corpus oro binario ni para entrenamiento del modelo.
