'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'admin' | 'lawyer' | 'assistant'
  is_active: boolean
  created_at: string
  last_login?: string
}

interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

interface LoginCredentials {
  username: string
  password: string
  remember_me?: boolean
}

interface AuthContextType {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  updateProfile: (updates: Partial<User>) => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [tokens, setTokens] = useState<AuthTokens | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const isAuthenticated = !!user && !!tokens

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedTokens = localStorage.getItem('auth_tokens')
        const storedUser = localStorage.getItem('auth_user')

        if (storedTokens && storedUser) {
          const parsedTokens = JSON.parse(storedTokens)
          const parsedUser = JSON.parse(storedUser)

          // Check if token is expired
          const tokenExpiry = localStorage.getItem('token_expiry')
          if (tokenExpiry && new Date() > new Date(tokenExpiry)) {
            // Try to refresh token
            try {
              await refreshTokenInternal(parsedTokens.refresh_token)
            } catch (error) {
              // Refresh failed, clear stored data
              clearAuthData()
            }
          } else {
            setTokens(parsedTokens)
            setUser(parsedUser)
          }
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        clearAuthData()
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  // Auto-refresh token before expiry
  useEffect(() => {
    if (!tokens) return

    const refreshTimer = setInterval(async () => {
      const tokenExpiry = localStorage.getItem('token_expiry')
      if (tokenExpiry) {
        const expiryTime = new Date(tokenExpiry)
        const now = new Date()
        const timeUntilExpiry = expiryTime.getTime() - now.getTime()

        // Refresh if token expires in less than 5 minutes
        if (timeUntilExpiry < 5 * 60 * 1000 && timeUntilExpiry > 0) {
          try {
            await refreshTokenInternal(tokens.refresh_token)
          } catch (error) {
            console.error('Auto-refresh failed:', error)
            await logout()
          }
        }
      }
    }, 60000) // Check every minute

    return () => clearInterval(refreshTimer)
  }, [tokens])

  const clearAuthData = () => {
    localStorage.removeItem('auth_tokens')
    localStorage.removeItem('auth_user')
    localStorage.removeItem('token_expiry')
    setTokens(null)
    setUser(null)
  }

  const storeAuthData = (authTokens: AuthTokens, userData: User) => {
    localStorage.setItem('auth_tokens', JSON.stringify(authTokens))
    localStorage.setItem('auth_user', JSON.stringify(userData))
    
    // Calculate and store token expiry
    const expiry = new Date(Date.now() + authTokens.expires_in * 1000)
    localStorage.setItem('token_expiry', expiry.toISOString())
    
    setTokens(authTokens)
    setUser(userData)
  }

  const makeAuthenticatedRequest = async (url: string, options: RequestInit = {}) => {
    if (!tokens) {
      throw new Error('No authentication tokens available')
    }

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${tokens.access_token}`,
      ...options.headers,
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      // Token might be expired, try to refresh
      try {
        await refreshTokenInternal(tokens.refresh_token)
        // Retry the original request with new token
        return await fetch(`${API_BASE_URL}${url}`, {
          ...options,
          headers: {
            ...headers,
            'Authorization': `Bearer ${tokens.access_token}`,
          },
        })
      } catch (refreshError) {
        // Refresh failed, logout user
        await logout()
        throw new Error('Authentication failed')
      }
    }

    return response
  }

  const login = async (credentials: LoginCredentials) => {
    try {
      setIsLoading(true)

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      const data = await response.json()
      
      // Store authentication data
      storeAuthData(
        {
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          token_type: data.token_type,
          expires_in: data.expires_in,
        },
        data.user
      )

    } catch (error) {
      console.error('Login error:', error)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const refreshTokenInternal = async (refreshToken: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) {
      throw new Error('Token refresh failed')
    }

    const data = await response.json()
    
    // Update tokens while keeping user data
    const newTokens = {
      access_token: data.access_token,
      refresh_token: refreshToken, // Keep the same refresh token
      token_type: data.token_type,
      expires_in: data.expires_in,
    }

    if (user) {
      storeAuthData(newTokens, user)
    }
  }

  const refreshToken = async () => {
    if (!tokens) {
      throw new Error('No refresh token available')
    }

    await refreshTokenInternal(tokens.refresh_token)
  }

  const logout = async () => {
    try {
      if (tokens) {
        // Notify server about logout
        await makeAuthenticatedRequest('/auth/logout', {
          method: 'POST',
        })
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuthData()
      router.push('/login')
    }
  }

  const updateProfile = async (updates: Partial<User>) => {
    try {
      const response = await makeAuthenticatedRequest('/auth/profile', {
        method: 'PUT',
        body: JSON.stringify(updates),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Profile update failed')
      }

      const data = await response.json()
      
      // Update stored user data
      const updatedUser = { ...user, ...data.user }
      localStorage.setItem('auth_user', JSON.stringify(updatedUser))
      setUser(updatedUser)

    } catch (error) {
      console.error('Profile update error:', error)
      throw error
    }
  }

  const changePassword = async (currentPassword: string, newPassword: string) => {
    try {
      const response = await makeAuthenticatedRequest('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Password change failed')
      }

    } catch (error) {
      console.error('Password change error:', error)
      throw error
    }
  }

  const value: AuthContextType = {
    user,
    tokens,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshToken,
    updateProfile,
    changePassword,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Hook for making authenticated API requests
export function useAuthenticatedFetch() {
  const { tokens, logout } = useAuth()

  const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
    if (!tokens) {
      throw new Error('No authentication tokens available')
    }

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${tokens.access_token}`,
      ...options.headers,
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    })

    if (response.status === 401) {
      // Authentication failed, logout user
      await logout()
      throw new Error('Authentication failed')
    }

    return response
  }

  return authenticatedFetch
}

// Higher-order component for protected routes
export function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  requiredRole?: string
) {
  return function AuthenticatedComponent(props: P) {
    const { isAuthenticated, isLoading, user } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!isLoading) {
        if (!isAuthenticated) {
          router.push('/login')
          return
        }

        if (requiredRole && user?.role !== requiredRole) {
          router.push('/unauthorized')
          return
        }
      }
    }, [isAuthenticated, isLoading, user, router])

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      )
    }

    if (!isAuthenticated) {
      return null
    }

    if (requiredRole && user?.role !== requiredRole) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
            <p className="text-gray-600">You don't have permission to access this page.</p>
          </div>
        </div>
      )
    }

    return <WrappedComponent {...props} />
  }
}

// Hook for role-based access control
export function usePermissions() {
  const { user } = useAuth()

  const hasRole = (role: string) => user?.role === role
  const hasAnyRole = (roles: string[]) => roles.includes(user?.role || '')
  const isAdmin = () => user?.role === 'admin'
  const isLawyer = () => user?.role === 'lawyer'
  const isAssistant = () => user?.role === 'assistant'

  return {
    hasRole,
    hasAnyRole,
    isAdmin,
    isLawyer,
    isAssistant,
    canCreateUsers: isAdmin(),
    canManageUsers: isAdmin(),
    canDeleteClients: hasAnyRole(['admin', 'lawyer']),
    canExportData: hasAnyRole(['admin', 'lawyer']),
    canViewAllClients: hasAnyRole(['admin', 'lawyer']),
    canCreateClients: hasAnyRole(['admin', 'lawyer', 'assistant']),
  }
}