import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

export interface UserProfile {
  username: string
  role: 'admin' | 'territorial_curator' | 'agronomic_researcher' | 'auditor'
  display_name: string
  is_active: boolean
}

export interface AuthContextType {
  user: UserProfile | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  authFetch: (url: string, init?: RequestInit) => Promise<Response>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE = (import.meta.env.VITE_API_URL as string) || '/v2'

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('ethosterra_token'))
  const [user, setUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem('ethosterra_user')
    try {
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const logout = useCallback(() => {
    localStorage.removeItem('ethosterra_token')
    localStorage.removeItem('ethosterra_user')
    setToken(null)
    setUser(null)
  }, [])

  // Interceptor global en window.fetch para inyectar automáticamente el Bearer token
  // en todas las llamadas a la API sin requerir refactorizaciones invasivas en los componentes
  useEffect(() => {
    const originalFetch = window.fetch
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const urlStr = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
      const currentToken = localStorage.getItem('ethosterra_token')

      let effectiveInit = init
      if (
        currentToken &&
        !urlStr.includes('/auth/login') &&
        (urlStr.startsWith('/v2') || urlStr.includes(API_BASE) || urlStr.startsWith('http://localhost:8000'))
      ) {
        const headers = new Headers(init?.headers || (input instanceof Request ? input.headers : {}))
        if (!headers.has('Authorization')) {
          headers.set('Authorization', `Bearer ${currentToken}`)
        }
        effectiveInit = { ...init, headers }
      }

      const response = await originalFetch(input, effectiveInit)
      if (response.status === 401 && !urlStr.includes('/auth/login') && !urlStr.includes('/auth/me')) {
        logout()
      }
      return response
    }

    return () => {
      window.fetch = originalFetch
    }
  }, [logout])

  // Validar vigencia del token con el backend al inicializar la app
  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem('ethosterra_token')
      if (!storedToken) {
        setIsLoading(false)
        return
      }

      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
        })

        if (res.ok) {
          const profile: UserProfile = await res.json()
          setUser(profile)
          localStorage.setItem('ethosterra_user', JSON.stringify(profile))
        } else {
          // Token inválido, expirado o revocado
          logout()
        }
      } catch (err) {
        console.warn('Verificación de sesión omitida por red offline:', err)
      } finally {
        setIsLoading(false)
      }
    }

    verifySession()
  }, [logout])

  const login = async (username: string, password: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Credenciales de acceso inválidas.')
    }

    const data = await res.json()
    const receivedToken = data.access_token
    const receivedUser = data.user

    localStorage.setItem('ethosterra_token', receivedToken)
    localStorage.setItem('ethosterra_user', JSON.stringify(receivedUser))
    setToken(receivedToken)
    setUser(receivedUser)
  }

  // Envoltorio para peticiones fetch con inyección automática del Bearer token
  const authFetch = useCallback(
    async (url: string, init: RequestInit = {}): Promise<Response> => {
      const headers = new Headers(init.headers || {})
      if (token) {
        headers.set('Authorization', `Bearer ${token}`)
      }

      const res = await fetch(url, { ...init, headers })
      if (res.status === 401) {
        logout()
      }
      return res
    },
    [token, logout]
  )

  const value = {
    user,
    token,
    isAuthenticated: Boolean(token && user),
    isLoading,
    login,
    logout,
    authFetch,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe utilizarse dentro de un AuthProvider.')
  }
  return context
}
