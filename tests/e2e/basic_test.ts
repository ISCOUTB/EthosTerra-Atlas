import { test, expect } from '@playwright/test'

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000/v2'

test('flujo completo: UI classify endpoint contra API real', async ({ page }) => {
  // 1. Visitar interfaz UI
  await page.goto('http://localhost:5173')

  // 2. JSON de entrada caso puro (formato simplificado)
  const jsonInput = `{
    "simulator_id": "ST-Norte",
    "timestamp": "2026-09-08T10:00:00Z",
    "context_data": {
      "presion": 300,
      "estado_valvula": "abierta"
    }
  }`

  // 3. Llenar y submit
  await page.fill('textarea', jsonInput)
  await page.click('button:has-text("Analizar Contexto")')

  // 4. Verificar que hay un resultado (puro o conflictivo según modelo)
  await expect(page.locator('[data-testid="case-type"]')).toBeVisible({ timeout: 10000 })

  // 5. Validar que el trace_id está presente (trazabilidad forense)
  await expect(page.locator('[data-testid="trace-id"]')).toBeVisible({ timeout: 10000 })

  // 6. Verificar API de salud responde 200
  const apiResponse = await page.request.get(`${API_BASE}/health`)
  expect(apiResponse.status()).toBe(200)
})