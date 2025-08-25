'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Search, Filter, Users, Download, Eye, Edit, Trash2, Plus, RefreshCw } from 'lucide-react'
import { useToast } from '@/components/Toast'

interface Client {
  clientId: string
  fullName: string
  maritalStatus: string
  objective: string
  createdAt: string
  lastUpdated: string
  submittedBy: string
}

interface SearchFilters {
  maritalStatus: string
  objective: string
  dateRange: string
  economicStanding: string
}

interface ExportOptions {
  format: 'pdf' | 'excel'
  includeAIProposals: boolean
  includeSummary: boolean
}

export function ClientSearch() {
  const [clients, setClients] = useState<Client[]>([])
  const [filteredClients, setFilteredClients] = useState<Client[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedClientIds, setSelectedClientIds] = useState<Set<string>>(new Set())
  const [showFilters, setShowFilters] = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(10)
  
  const [filters, setFilters] = useState<SearchFilters>({
    maritalStatus: '',
    objective: '',
    dateRange: '',
    economicStanding: ''
  })
  
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'pdf',
    includeAIProposals: true,
    includeSummary: true
  })

  const { addToast } = useToast()

  // Fetch clients from API
  const fetchClients = useCallback(async () => {
    setIsLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        addToast({ type: 'error', title: 'Please login to access client data' })
        return
      }

      const response = await fetch('/api/clients/search', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setClients(data.results || [])
      setFilteredClients(data.results || [])
    } catch (error) {
      console.error('Error fetching clients:', error)
      addToast({ type: 'error', title: 'Failed to fetch client data' })
    } finally {
      setIsLoading(false)
    }
  }, [addToast])

  // Search clients with query
  const searchClients = useCallback(async (query: string) => {
    if (!query.trim()) {
      setFilteredClients(clients)
      return
    }

    setIsLoading(true)
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`/api/clients/search?q=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setFilteredClients(data.results || [])
    } catch (error) {
      console.error('Error searching clients:', error)
      addToast({ type: 'error', title: 'Search failed' })
    } finally {
      setIsLoading(false)
    }
  }, [clients, addToast])

  // Apply local filters
  const applyFilters = useCallback(() => {
    let filtered = searchQuery ? filteredClients : clients

    if (filters.maritalStatus) {
      filtered = filtered.filter(client => client.maritalStatus === filters.maritalStatus)
    }

    if (filters.objective) {
      filtered = filtered.filter(client => client.objective === filters.objective)
    }

    if (filters.dateRange) {
      const now = new Date()
      const filterDate = new Date()
      
      switch (filters.dateRange) {
        case 'week':
          filterDate.setDate(now.getDate() - 7)
          break
        case 'month':
          filterDate.setMonth(now.getMonth() - 1)
          break
        case 'quarter':
          filterDate.setMonth(now.getMonth() - 3)
          break
        case 'year':
          filterDate.setFullYear(now.getFullYear() - 1)
          break
      }

      if (filters.dateRange !== '') {
        filtered = filtered.filter(client => new Date(client.createdAt) >= filterDate)
      }
    }

    setFilteredClients(filtered)
    setCurrentPage(1) // Reset to first page when filtering
  }, [clients, filteredClients, filters, searchQuery])

  // Handle search input
  const handleSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value
    setSearchQuery(query)
    
    // Debounce search
    const timeoutId = setTimeout(() => {
      searchClients(query)
    }, 300)

    return () => clearTimeout(timeoutId)
  }, [searchClients])

  // Export selected clients
  const handleExport = async () => {
    if (selectedClientIds.size === 0) {
      addToast({ type: 'warning', title: 'Please select clients to export' })
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      const endpoint = exportOptions.format === 'pdf' ? '/api/export/pdf' : '/api/export/excel'
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          clientIds: Array.from(selectedClientIds),
          format: exportOptions.format,
          includeAIProposals: exportOptions.includeAIProposals,
          includeSummary: exportOptions.includeSummary
        })
      })

      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`)
      }

      const data = await response.json()
      
      // Trigger download
      const downloadResponse = await fetch(data.downloadUrl, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!downloadResponse.ok) {
        throw new Error('Download failed')
      }

      const blob = await downloadResponse.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = data.filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      addToast({ type: 'success', title: `Export completed: ${data.filename}` })
      setShowExportModal(false)
      setSelectedClientIds(new Set())
    } catch (error) {
      console.error('Export error:', error)
      addToast({ type: 'error', title: 'Export failed' })
    }
  }

  // View client details
  const viewClient = (clientId: string) => {
    window.open(`/client/${clientId}`, '_blank')
  }

  // Edit client
  const editClient = (clientId: string) => {
    window.location.href = `/questionnaire?clientId=${clientId}`
  }

  // Delete client
  const deleteClient = async (clientId: string) => {
    if (!confirm('Are you sure you want to delete this client? This action cannot be undone.')) {
      return
    }

    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`/api/clients/${clientId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Delete failed')
      }

      addToast({ type: 'success', title: 'Client deleted successfully' })
      fetchClients() // Refresh the list
    } catch (error) {
      console.error('Delete error:', error)
      addToast({ type: 'error', title: 'Failed to delete client' })
    }
  }

  // Pagination logic
  const totalPages = Math.ceil(filteredClients.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const currentClients = filteredClients.slice(startIndex, endIndex)

  // Load clients on mount
  useEffect(() => {
    fetchClients()
  }, [fetchClients])

  // Apply filters when they change
  useEffect(() => {
    applyFilters()
  }, [applyFilters])

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-2">
          <Users className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Client Management</h1>
          <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2.5 py-0.5 rounded">
            {filteredClients.length} clients
          </span>
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
          
          <button
            onClick={() => setShowExportModal(true)}
            disabled={selectedClientIds.size === 0}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4" />
            Export ({selectedClientIds.size})
          </button>
          
          <button
            onClick={() => window.location.href = '/questionnaire'}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            New Client
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search clients by name, objective, or marital status..."
          value={searchQuery}
          onChange={handleSearch}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
        <button
          onClick={fetchClients}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
        >
          <RefreshCw className={`h-4 w-4 text-gray-400 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-gray-50 p-4 rounded-lg border">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Marital Status</label>
              <select
                value={filters.maritalStatus}
                onChange={(e) => setFilters({...filters, maritalStatus: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="Single">Single</option>
                <option value="Married">Married</option>
                <option value="Divorced">Divorced</option>
                <option value="Widowed">Widowed</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Objective</label>
              <select
                value={filters.objective}
                onChange={(e) => setFilters({...filters, objective: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="Create Will">Create Will</option>
                <option value="Create Trust">Create Trust</option>
                <option value="Create Living Will">Create Living Will</option>
                <option value="Sell Asset">Sell Asset</option>
                <option value="Other">Other</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date Range</label>
              <select
                value={filters.dateRange}
                onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Time</option>
                <option value="week">Last Week</option>
                <option value="month">Last Month</option>
                <option value="quarter">Last Quarter</option>
                <option value="year">Last Year</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={() => setFilters({maritalStatus: '', objective: '', dateRange: '', economicStanding: ''})}
                className="w-full px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      <div className="bg-white rounded-lg border">
        {isLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400 mb-2" />
            <p className="text-gray-500">Loading clients...</p>
          </div>
        ) : currentClients.length === 0 ? (
          <div className="p-8 text-center">
            <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500 text-lg">No clients found</p>
            <p className="text-gray-400 text-sm">Try adjusting your search or filters</p>
          </div>
        ) : (
          <>
            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b">
                  <tr>
                    <th className="px-4 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedClientIds.size === currentClients.length && currentClients.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedClientIds(new Set(currentClients.map(c => c.clientId)))
                          } else {
                            setSelectedClientIds(new Set())
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-900">Client Name</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-900">Marital Status</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-900">Objective</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-900">Created</th>
                    <th className="px-4 py-3 text-left text-sm font-medium text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {currentClients.map((client) => (
                    <tr key={client.clientId} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={selectedClientIds.has(client.clientId)}
                          onChange={(e) => {
                            const newSelected = new Set(selectedClientIds)
                            if (e.target.checked) {
                              newSelected.add(client.clientId)
                            } else {
                              newSelected.delete(client.clientId)
                            }
                            setSelectedClientIds(newSelected)
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{client.fullName}</div>
                        <div className="text-sm text-gray-500">{client.clientId}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">{client.maritalStatus}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{client.objective}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {new Date(client.createdAt).toLocaleDateString()}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => viewClient(client.clientId)}
                            className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                            title="View Details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => editClient(client.clientId)}
                            className="p-2 text-green-600 hover:bg-green-50 rounded"
                            title="Edit"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => deleteClient(client.clientId)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded"
                            title="Delete"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t">
                <div className="text-sm text-gray-700">
                  Showing {startIndex + 1} to {Math.min(endIndex, filteredClients.length)} of {filteredClients.length} results
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-700">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Export Options</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Format</label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="pdf"
                      checked={exportOptions.format === 'pdf'}
                      onChange={(e) => setExportOptions({...exportOptions, format: e.target.value as 'pdf' | 'excel'})}
                      className="mr-2"
                    />
                    PDF (Single Client)
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      value="excel"
                      checked={exportOptions.format === 'excel'}
                      onChange={(e) => setExportOptions({...exportOptions, format: e.target.value as 'pdf' | 'excel'})}
                      className="mr-2"
                    />
                    Excel (Multiple Clients)
                  </label>
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={exportOptions.includeAIProposals}
                    onChange={(e) => setExportOptions({...exportOptions, includeAIProposals: e.target.checked})}
                    className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  Include AI Proposals
                </label>
                
                {exportOptions.format === 'excel' && (
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={exportOptions.includeSummary}
                      onChange={(e) => setExportOptions({...exportOptions, includeSummary: e.target.checked})}
                      className="mr-2 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    Include Summary Sheet
                  </label>
                )}
              </div>
              
              <div className="text-sm text-gray-600">
                Selected clients: {selectedClientIds.size}
              </div>
            </div>
            
            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleExport}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Export
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}