import React, { useState } from 'react'
import { ShieldCheck, Lock, User, AlertCircle, ArrowRight, Compass } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

export const LoginView: React.FC = () => {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      setError('Por favor ingresa tu usuario y contraseña.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      await login(username.trim(), password)
    } catch (err: any) {
      setError(err.message || 'Error al iniciar sesión. Verifica tus credenciales.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f7f5f0] p-4 sm:p-6 font-sans">
      <div className="w-full max-w-md">
        {/* Cabecera institucional */}
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#0066cc]/10 text-[#0066cc] mb-3 shadow-xs border border-[#0066cc]/20">
            <Compass className="w-8 h-8" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1c1b18]">
            EthosTerra Atlas
          </h1>
          <p className="text-sm text-[#66635b]">
            Sistema Soberano de Inteligencia Territorial y Política Agraria
          </p>
          <div className="pt-1 flex justify-center">
            <Badge tone="puro" className="gap-1.5 text-xs py-0.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Acceso Soberano Autenticado (Zero-Trust)</span>
            </Badge>
          </div>
        </div>

        {/* Tarjeta de autenticación */}
        <div className="p-6 sm:p-8 shadow-sm border border-[#e4e1d8] rounded-xl bg-white">
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-[#1c1b18]">Iniciar Sesión</h2>
            <p className="text-xs text-[#807d75] mt-1">
              Ingresa tus credenciales autorizadas para acceder al corpus y herramientas territoriales.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3.5 rounded-lg bg-red-50 border border-red-200/80 flex items-start gap-2.5 text-xs text-red-700 animate-fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#403e38] mb-1.5">
                Usuario Autorizado
              </label>
              <div className="relative">
                <input
                  type="text"
                  autoComplete="username"
                  required
                  placeholder="ej. admin"
                  value={username}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUsername(e.target.value)}
                  disabled={loading}
                  className="w-full pl-9.5 pr-3 py-2 bg-white border border-[#d6d3c9] rounded-lg text-sm text-[#1c1b18] placeholder-[#a3a096] focus:outline-none focus:ring-2 focus:ring-[#0066cc]/30 focus:border-[#0066cc] disabled:bg-slate-50 transition-colors"
                />
                <User className="w-4 h-4 text-[#a3a096] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#403e38] mb-1.5">
                Contraseña
              </label>
              <div className="relative">
                <input
                  type="password"
                  autoComplete="current-password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                  disabled={loading}
                  className="w-full pl-9.5 pr-3 py-2 bg-white border border-[#d6d3c9] rounded-lg text-sm text-[#1c1b18] placeholder-[#a3a096] focus:outline-none focus:ring-2 focus:ring-[#0066cc]/30 focus:border-[#0066cc] disabled:bg-slate-50 transition-colors"
                />
                <Lock className="w-4 h-4 text-[#a3a096] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                disabled={loading}
                className="w-full justify-center py-2.5 text-sm gap-2 font-medium cursor-pointer"
              >
                {loading ? (
                  <span>Verificando credenciales...</span>
                ) : (
                  <>
                    <span>Ingresar al Sistema</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            </div>
          </form>

          <div className="mt-6 pt-5 border-t border-[#f0ede6] text-center">
            <p className="text-[11px] text-[#99968d]">
              Todas las acciones de curación y compilación quedan firmadas y vinculadas criptográficamente a tu perfil.
            </p>
          </div>
        </div>

        {/* Pie de página con versión e invariantes */}
        <div className="mt-8 text-center text-xs text-[#a8a59b] space-y-1">
          <p>PDET Subregión Montes de María · 15 Municipios Piloto</p>
          <p className="text-[10px]">Autonomía Local Offline-First · ai/gemma4:E4B</p>
        </div>
      </div>
    </div>
  )
}
