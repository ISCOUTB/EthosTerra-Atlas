import { test } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

test('capturar pantallas de toda la interfaz para auditoria visual ui-ux-pro-max e impeccable', async ({ page }) => {
  const scratchDir = path.resolve('scratch')
  if (!fs.existsSync(scratchDir)) {
    fs.mkdirSync(scratchDir, { recursive: true })
  }

  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' })

  // 1. Atlas - Vista principal (Mapa / Cascada)
  await page.waitForTimeout(1000)
  await page.screenshot({ path: path.join(scratchDir, '01_atlas_main.png'), fullPage: true })

  // 2. Atlas - Pestaña Revisión y Cuarentena
  const cuarBtn = page.locator('button:has-text("Revisión y Cuarentena")').first()
  if (await cuarBtn.isVisible()) {
    await cuarBtn.click()
    await page.waitForTimeout(1000)
    await page.screenshot({ path: path.join(scratchDir, '02_atlas_quarantine.png'), fullPage: true })
  }

  // 3. Atlas - Pestaña Curación de Creencias
  const curBtn = page.locator('button:has-text("Curación de Creencias")').first()
  if (await curBtn.isVisible()) {
    await curBtn.click()
    await page.waitForTimeout(1000)
    await page.screenshot({ path: path.join(scratchDir, '03_atlas_curation.png'), fullPage: true })
  }

  // 4. Intenciones Manuales (B5)
  const intentsTab = page.locator('button:has-text("Intenciones Manuales")').first()
  if (await intentsTab.isVisible()) {
    await intentsTab.click()
    await page.waitForTimeout(1000)
    await page.screenshot({ path: path.join(scratchDir, '04_manual_intents.png'), fullPage: true })
  }

  // 5. Pipeline Documental eBDI
  const pipeTab = page.locator('button:has-text("Pipeline Documental")').first()
  if (await pipeTab.isVisible()) {
    await pipeTab.click()
    await page.waitForTimeout(1000)
    await page.screenshot({ path: path.join(scratchDir, '05_document_pipeline.png'), fullPage: true })
  }

  // 6. Clasificador Legacy
  const legacyTab = page.locator('button:has-text("Clasificador Legacy")').first()
  if (await legacyTab.isVisible()) {
    await legacyTab.click()
    await page.waitForTimeout(1000)
    await page.screenshot({ path: path.join(scratchDir, '06_clasificador_legacy.png'), fullPage: true })
  }
})
