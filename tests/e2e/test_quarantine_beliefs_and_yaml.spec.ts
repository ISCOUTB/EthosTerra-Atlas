import { test } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

test('validar interfaz de creencias, edicion dual y compilador yaml', async ({ page }) => {
  const scratchDir = path.resolve('scratch')
  if (!fs.existsSync(scratchDir)) {
    fs.mkdirSync(scratchDir, { recursive: true })
  }

  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' })

  // 1. Ir a Revisión y Cuarentena
  const cuarBtn = page.locator('button:has-text("Revisión y Cuarentena")').first()
  if (await cuarBtn.isVisible()) {
    await cuarBtn.click()
    await page.waitForTimeout(1000)
  }

  // 2. Abrir Creencias eBDI del primer documento disponible
  const beliefsBtn = page.locator('button:has-text("Creencias eBDI")').first()
  if (await beliefsBtn.isVisible()) {
    await beliefsBtn.click()
    await page.waitForTimeout(1500)
    await page.screenshot({ path: path.join(scratchDir, '07_beliefs_view_with_cards.png'), fullPage: true })

    // 3. Probar botón Editar
    const editBtn = page.locator('button:has-text("Editar")').first()
    if (await editBtn.isVisible()) {
      await editBtn.click()
      await page.waitForTimeout(600)
      await page.screenshot({ path: path.join(scratchDir, '08_belief_friendly_edit_modal.png'), fullPage: true })

      // Alternar a Editor JSON
      const jsonTabBtn = page.locator('button:has-text("Editor JSON")').first()
      if (await jsonTabBtn.isVisible()) {
        await jsonTabBtn.click()
        await page.waitForTimeout(600)
        await page.screenshot({ path: path.join(scratchDir, '09_belief_programmer_json_modal.png'), fullPage: true })
      }

      // Cerrar modal de edición
      const cancelBtn = page.locator('button:has-text("Cancelar")').first()
      if (await cancelBtn.isVisible()) {
        await cancelBtn.click()
        await page.waitForTimeout(500)
      }
    }

    // 4. Probar Compilar a YAML si está presente
    const compileBtn = page.locator('button:has-text("Compilar a YAML de Simulación")').first()
    if (await compileBtn.isVisible()) {
      await compileBtn.click()
      await page.waitForTimeout(1000)
      await page.screenshot({ path: path.join(scratchDir, '10_compiled_yamls_modal.png'), fullPage: true })
    }
  }
})
