import { test, expect } from '@playwright/test'

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000/v2'
const UI_BASE = process.env.UI_BASE_URL || 'http://localhost:5173'

test.describe('Atlas Territorial & Gobernanza de Creencias eBDI', () => {
  test('API: Endpoints de creencias, curación granular y cascada piloto responden correctamente', async ({ request }) => {
    // 1. Verificar healthcheck
    const healthRes = await request.get(`http://localhost:8000/health`)
    expect(healthRes.status()).toBe(200)

    // 2. Verificar artefactos en cuarentena
    const quarantineRes = await request.get(`${API_BASE}/atlas/artifacts/quarantine`)
    expect(quarantineRes.status()).toBe(200)
    const quarantineData = await quarantineRes.json()
    expect(quarantineData.documents.length).toBeGreaterThan(0)

    // 3. Verificar creencias extraídas de art_patr_montes_de_maria
    const beliefsRes = await request.get(`${API_BASE}/atlas/artifacts/art_patr_montes_de_maria/beliefs`)
    expect(beliefsRes.status()).toBe(200)
    const beliefsData = await beliefsRes.json()
    expect(beliefsData.source_id).toBe('art_patr_montes_de_maria')
    expect(beliefsData.verified_beliefs_count).toBeGreaterThan(0)
    expect(beliefsData.beliefs.length).toBeGreaterThan(0)

    const firstBelief = beliefsData.beliefs[0]
    expect(firstBelief.raw_excerpt).toBeTruthy()
    expect(firstBelief.ebdi_belief_assertion).toBeTruthy()

    // 4. Probar curación granular (PATCH) de una creencia individual
    const curateRes = await request.patch(
      `${API_BASE}/atlas/artifacts/art_patr_montes_de_maria/beliefs/${firstBelief.belief_id}`,
      {
        data: {
          decision: 'admitted_ebdi',
          curator_id: 'revisor_e2e_playwright',
          notes: 'Admitida formalmente mediante prueba E2E automatizada Playwright',
        },
      }
    )
    expect(curateRes.status()).toBe(200)
    const curatedData = await curateRes.json()
    expect(curatedData.curation_status).toBe('admitted_ebdi')
    expect(curatedData.curator_id).toBe('revisor_e2e_playwright')

    // 5. Verificar agregación de creencias en cascada para piloto El Carmen de Bolívar (13244)
    const pilotBeliefsRes = await request.get(`${API_BASE}/atlas/pilots/13244/beliefs`)
    expect(pilotBeliefsRes.status()).toBe(200)
    const pilotData = await pilotBeliefsRes.json()
    expect(pilotData.divipola).toBe('13244')
    expect(pilotData.total_applicable_beliefs).toBeGreaterThan(0)
  })

  test('UI: Navegación por el Atlas, verificación de banner de gobernanza e inspección JSON', async ({ page }) => {
    // 1. Abrir aplicación UI
    await page.goto(UI_BASE)

    // 2. Navegar a la pestaña de Atlas de Política Territorial
    const atlasTab = page.locator('button:has-text("Atlas Territorial"), button:has-text("Atlas")').first()
    if (await atlasTab.isVisible()) {
      await atlasTab.click()
    }

    // 3. Abrir la pestaña de Revisión Contextual Cuarentena
    const quarantineTab = page.locator('button:has-text("Revisión Contextual Cuarentena")')
    await expect(quarantineTab).toBeVisible({ timeout: 10000 })
    await quarantineTab.click()

    // 4. Verificar que el banner de Gobernanza Dinámica está visible y actualizado
    const governanceBanner = page.locator('text=Revisión Contextual Humana y Gobernanza Criptográfica')
    await expect(governanceBanner).toBeVisible()

    // 5. Ubicar el artefacto aprobado art_patr_montes_de_maria y abrir modal de creencias
    const patrCard = page.locator('div:has-text("art_patr_montes_de_maria")').first()
    await expect(patrCard).toBeVisible()

    const openBeliefsBtn = page.locator('button:has-text("Creencias eBDI")').first()
    await expect(openBeliefsBtn).toBeVisible()
    await openBeliefsBtn.click()

    // 6. Verificar que el modal de creencias eBDI se abrió
    const modalHeader = page.locator('text=ai/gemma4:E4B (Local Soberano)')
    await expect(modalHeader).toBeVisible({ timeout: 10000 })

    // 7. Verificar que los controles de curación y JSON están presentes
    const verJsonBtn = page.locator('button:has-text("Ver JSON")').first()
    await expect(verJsonBtn).toBeVisible()

    const admitirBtn = page.locator('button:has-text("Admitir eBDI")').first()
    await expect(admitirBtn).toBeVisible()

    const descartarBtn = page.locator('button:has-text("Descartar Ruido")').first()
    await expect(descartarBtn).toBeVisible()

    // 8. Abrir el bloque JSON de la primera creencia y validar contenido
    await verJsonBtn.click()
    const jsonBlock = page.locator('text=JSON de la Creencia #1')
    await expect(jsonBlock).toBeVisible()

    const copyBtn = page.locator('button:has-text("Copiar")').first()
    await expect(copyBtn).toBeVisible()

    // 9. Ocultar JSON
    const ocultarJsonBtn = page.locator('button:has-text("Ocultar JSON")').first()
    await ocultarJsonBtn.click()
    await expect(jsonBlock).not.toBeVisible()

    // 10. Cerrar modal limpiamente
    const closeBtn = page.locator('button:has-text("Cerrar")')
    await closeBtn.click()
  })
})
