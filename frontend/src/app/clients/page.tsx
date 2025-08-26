'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Plus, Eye, Edit, Trash2, Download, Filter } from 'lucide-react';
import apiService from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

interface Client {
  id: string;
  fullName: string;
  maritalStatus: string;
  email?: string;
  phone?: string;
  status: 'active' | 'pending' | 'completed';
  createdAt: string;
  lastUpdated: string;
}

export default function ClientsPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, tokens } = useAuth();
  const [clients, setClients] = useState<Client[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalClients, setTotalClients] = useState(0);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, authLoading, router]);

  const fetchClients = async (search?: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await apiService.getClients(1, 100, search);
      
      if (response && response.clients) {
        setClients(response.clients);
        setTotalClients(response.total || response.clients.length);
      } else {
        setClients([]);
        setTotalClients(0);
      }
    } catch (error) {
      console.error('Failed to fetch clients:', error);
      setError('Failed to load clients. Please try again.');
      setClients([]);
      setTotalClients(0);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchTerm) {
        fetchClients(searchTerm);
      } else {
        fetchClients();
      }
    }, 500); // Debounce search

    return () => clearTimeout(timeoutId);
  }, [searchTerm]);

  const handleDeleteClient = async (clientId: string, clientName: string) => {
    if (window.confirm(`Are you sure you want to delete ${clientName}?`)) {
      try {
        await apiService.deleteClient(clientId);
        await fetchClients(searchTerm); // Refresh the list
      } catch (error) {
        console.error('Failed to delete client:', error);
        alert('Failed to delete client. Please try again.');
      }
    }
  };

  const handleNewClient = () => {
    router.push('/questionnaire');
  };

  const filteredClients = clients.filter(client => {
    const matchesSearch = client.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         client.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || client.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  // Show loading while authenticating
  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Client Management</h1>
        <p className="text-gray-600">Manage and track client records and questionnaires</p>
      </div>

      {/* Search and Filter Bar */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder="Search clients by name or ID..."
            className="input-high-contrast w-full pl-10 pr-4 py-2 rounded-lg focus:ring-2 focus:ring-indigo-500"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex gap-2">
          <select
            className="select-high-contrast px-4 py-2 rounded-lg focus:ring-2 focus:ring-indigo-500"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
          </select>
          
          <button 
            onClick={handleNewClient}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Client
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => fetchClients(searchTerm)}
            className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Clients Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Client
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mr-2"></div>
                      Loading clients...
                    </div>
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-red-500">
                    {error}
                  </td>
                </tr>
              ) : filteredClients.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                    No clients found
                  </td>
                </tr>
              ) : (
                filteredClients.map((client) => (
                  <tr key={client.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {client.fullName}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {client.id}
                        </div>
                        <div className="text-xs text-gray-400">
                          {client.maritalStatus}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{client.email}</div>
                      <div className="text-sm text-gray-500">{client.phone}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadge(client.status)}`}>
                        {client.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(client.createdAt).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <button className="text-indigo-600 hover:text-indigo-900">
                          <Eye className="h-4 w-4" />
                        </button>
                        <button className="text-green-600 hover:text-green-900">
                          <Edit className="h-4 w-4" />
                        </button>
                        <button className="text-blue-600 hover:text-blue-900">
                          <Download className="h-4 w-4" />
                        </button>
                        <button 
                          onClick={() => handleDeleteClient(client.id, client.fullName)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete client"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Results Summary */}
      {!isLoading && !error && (
        <div className="mt-4 text-sm text-gray-500">
          Showing {filteredClients.length} of {totalClients} clients
        </div>
      )}
    </div>
  );
}