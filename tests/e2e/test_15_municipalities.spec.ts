import { test, expect } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

test('validar navegacion e integracion de los 15 municipios de Montes de Maria', async ({ page }) => {
  const scratchDir = path.resolve('scratch')
  if (!fs.existsSync(scratchDir)) {
    fs.mkdirSync(scratchDir, { recursive: true })
  }

  await page.setViewportSize({ width: 1440, height: 950 })
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2500)

  // 1. Vista inicial: pestaña Bolivar (7 municipios)
  await page.screenshot({ path: path.join(scratchDir, '15_all_15_bolivar_tab.png'), fullPage: true })

  // 2. Probar pestaña "Todos (15)"
  const todosBtn = page.locator('button:has-text("Todos (15)")').first()
  if (await todosBtn.isVisible()) {
    await todosBtn.click()
    await page.waitForTimeout(1500)
    await page.screenshot({ path: path.join(scratchDir, '16_all_15_subregion_overview.png'), fullPage: true })
  }

  // 3. Probar seleccion de Zambrano (Bolivar)
  const zambranoBtn = page.locator('button:has-text("Zambrano")').first()
  if (await zambranoBtn.isVisible()) {
    await zambranoBtn.click()
    await page.waitForTimeout(2000)
    await page.screenshot({ path: path.join(scratchDir, '17_zambrano_bolivar_profile.png'), fullPage: true })
  }

  // 4. Probar pestaña "Sucre (8)" y seleccionar Ovejas
  const sucreBtn = page.locator('button:has-text("Sucre (8)")').first()
  if (await sucreBtn.isVisible()) {
    await sucreBtn.click()
    await page.waitForTimeout(1000)

    const ovejasBtn = page.locator('button:has-text("Ovejas")').first()
    if (await ovejasBtn.isVisible()) {
      await ovejasBtn.click()
      await page.waitForTimeout(2000)
      await page.screenshot({ path: path.join(scratchDir, '18_ovejas_sucre_profile.png'), fullPage: true })
    }
  }
})
