# Documento de Migración AGY y Unificación de Repositorio

- **Fecha:** 2026-09-15
- **Objetivo:** Unificación arquitectónica y eliminación de repositorio Git anidado para consolidar el baseline de la Semana 5.

## 1. Razón de la migración
En la estructura del proyecto se identificó un repositorio Git anidado en `wellprodsim-ai/` dentro del repositorio principal `Prueba-llm-local/`. 
Dicho repositorio anidado:
- Carecía de commits (0 commits, rama `main` en estado unborn).
- No tenía remotos configurados (`git remote -v` vacío).
- No contenía código ejecutable, Dockerfiles, docker-compose, datasets ni dependencias.
- Era únicamente una plantilla/scaffold de configuración para agentes AGY.

Para mantener la simplicidad, evitar estados corruptos de gitlink/submódulo y centralizar la configuración en el monorepo oficial de Semana 5, se aprobó la migración del contenido de configuración a la raíz (`Prueba-llm-local/.agents/`).

## 2. Origen y Destino
- **Origen:** `Prueba-llm-local/wellprodsim-ai/.agents/`
- **Destino:** `Prueba-llm-local/.agents/`

## 3. Elementos migrados
- `.agents/agents/wellprod-architect/agent.md`: Definición y directrices del agente arquitecto senior.
- `.agents/skills/wellprod-domain/SKILL.md`: Skill de conocimiento del dominio agronómico (casos Puro vs Conflictivo).

## 4. Mecanismo de respaldo
Antes de cualquier movimiento o eliminación, se generó una copia de respaldo íntegra fuera del repositorio Git en:
`../backup-agents-before-migration-20260915-161246/`

## 5. Verificación mediante Hashes SHA-256
Los hashes criptográficos verificados en origen, respaldo y destino son idénticos:
- `wellprod-architect/agent.md`: `a89487d32c52c02f332fbe814b15bbcf63d38ae5b154221164a1166151acb3d2`
- `wellprod-domain/SKILL.md`: `ebf8b251494ae2ce7ae9bdb95947d1324c0bc6b45c775f4572b6c38926330105`

## 6. Estado del Simulador Real
- **Declaración:** El simulador real WellProdSim/BESA se encuentra fuera de este repositorio y permanece estrictamente intacto y fuera de alcance hasta las semanas 10–12.
- **Alcance preservado:** La API (FastAPI), la UI (React), Docker Compose, el dataset de pruebas y las evaluaciones del modelo de Semana 5 no sufrieron alteraciones.
