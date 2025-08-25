'use client';

import { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  Plus, 
  Filter, 
  MoreVertical, 
  Eye, 
  Edit, 
  Trash2,
  FileText,
  Calendar,
  DollarSign,
  Target,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import apiService from '@/services/api';

interface Client {
  clientId: string;
  bioData: {
    fullName: string;
    maritalStatus: string;
    spouseName?: string;
    children: string;
  };
  financialData: {
    assets: Array<{
      type: string;
      description: string;
      value: number;
    }>;
    liabilities: string;
    incomeSources: string;
  };
  economicContext: {
    economicStanding: string;
    distributionPrefs: string;
  };
  objectives: {
    objective: string;
    details: string;
  };
  lawyerNotes: string;
  lastUpdated: string;
  savedAt?: string;
}

interface ClientCardProps {
  client: Client;
  onView: (client: Client) => void;
  onEdit: (client: Client) => void;
  onDelete: (clientId: string) => void;
}

function ClientCard({ client, onView, onEdit, onDelete }: ClientCardProps) {
  const [showDropdown, setShowDropdown] = useState(false);
  
  const totalAssetValue = client.financialData.assets.reduce(
    (sum, asset) => sum + asset.value, 0
  );

  const getStatusColor = (objective: string) => {
    switch (objective) {
      case 'Create Will':
        return 'bg-blue-100 text-blue-800';
      case 'Create Trust':
        return 'bg-green-100 text-green-800';
      case 'Sell Asset':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">
              {client.bioData.fullName}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              ID: {client.clientId}
            </p>
            
            <div className="mt-3 space-y-2">
              <div className="flex items-center text-sm text-gray-600">
                <Users className="h-4 w-4 mr-2" />
                <span>{client.bioData.maritalStatus}</span>
                {client.bioData.spouseName && (
                  <span className="ml-2">• Spouse: {client.bioData.spouseName}</span>
                )}
              </div>
              
              <div className="flex items-center text-sm text-gray-600">
                <DollarSign className="h-4 w-4 mr-2" />
                <span>Assets: KES {totalAssetValue.toLocaleString()}</span>
              </div>
              
              <div className="flex items-center text-sm text-gray-600">
                <Target className="h-4 w-4 mr-2" />
                <span className={cn(
                  "px-2 py-1 rounded-full text-xs font-medium",
                  getStatusColor(client.objectives.objective)
                )}>
                  {client.objectives.objective}
                </span>
              </div>
            </div>
          </div>
          
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
            >
              <MoreVertical className="h-4 w-4" />
            </button>
            
            {showDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                <div className="py-1">
                  <button
                    onClick={() => {
                      onView(client);
                      setShowDropdown(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </button>
                  <button
                    onClick={() => {
                      onEdit(client);
                      setShowDropdown(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </button>
                  <button
                    onClick={() => {
                      onDelete(client.clientId);
                      setShowDropdown(false);
                    }}
                    className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center">
              <Calendar className="h-3 w-3 mr-1" />
              Last updated: {new Date(client.lastUpdated).toLocaleDateString()}
            </div>
            <div className="flex items-center">
              <FileText className="h-3 w-3 mr-1" />
              {client.lawyerNotes ? 'Has notes' : 'No notes'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function ClientDashboard() {
  const [clients, setClients] = useState<Client[]>([]);
  const [filteredClients, setFilteredClients] = useState<Client[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBy, setFilterBy] = useState('all');
  const [sortBy, setSortBy] = useState('newest');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [showClientModal, setShowClientModal] = useState(false);

  useEffect(() => {
    loadClients();
  }, []);

  useEffect(() => {
    filterAndSortClients();
  }, [clients, searchTerm, filterBy, sortBy]);

  const loadClients = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await apiService.getClients();
      setClients(data.clients || []);
    } catch (error) {
      console.error('Failed to load clients:', error);
      setError('Failed to load clients. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const filterAndSortClients = () => {
    let filtered = [...clients];

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(client =>
        client.bioData.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.clientId.toLowerCase().includes(searchTerm.toLowerCase()) ||
        client.objectives.objective.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply category filter
    if (filterBy !== 'all') {
      filtered = filtered.filter(client =>
        client.objectives.objective === filterBy
      );
    }

    // Apply sorting
    switch (sortBy) {
      case 'newest':
        filtered.sort((a, b) => new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime());
        break;
      case 'oldest':
        filtered.sort((a, b) => new Date(a.lastUpdated).getTime() - new Date(b.lastUpdated).getTime());
        break;
      case 'name':
        filtered.sort((a, b) => a.bioData.fullName.localeCompare(b.bioData.fullName));
        break;
      case 'assets':
        filtered.sort((a, b) => {
          const aAssets = a.financialData.assets.reduce((sum, asset) => sum + asset.value, 0);
          const bAssets = b.financialData.assets.reduce((sum, asset) => sum + asset.value, 0);
          return bAssets - aAssets;
        });
        break;
    }

    setFilteredClients(filtered);
  };

  const handleDeleteClient = async (clientId: string) => {
    if (!confirm('Are you sure you want to delete this client? This action cannot be undone.')) {
      return;
    }

    try {
      await apiService.deleteClient(clientId);
      setClients(clients.filter(client => client.clientId !== clientId));
    } catch (error) {
      console.error('Failed to delete client:', error);
      alert('Failed to delete client. Please try again.');
    }
  };

  const objectiveOptions = [
    'Create Will',
    'Create Living Will',
    'Create Share Transfer Will',
    'Create Trust',
    'Sell Asset',
    'Other'
  ];

  const stats = {
    total: clients.length,
    totalAssets: clients.reduce((sum, client) => 
      sum + client.financialData.assets.reduce((assetSum, asset) => assetSum + asset.value, 0), 0
    ),
    byObjective: objectiveOptions.reduce((acc, objective) => {
      acc[objective] = clients.filter(client => client.objectives.objective === objective).length;
      return acc;
    }, {} as Record<string, number>)
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        <span className="ml-2 text-gray-600">Loading clients...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Client Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage and view all client records</p>
        </div>
        <button
          onClick={() => window.location.href = '/questionnaire'}
          className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4" />
          <span>New Client</span>
        </button>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-indigo-600" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              <p className="text-gray-600">Total Clients</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <DollarSign className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                KES {stats.totalAssets.toLocaleString()}
              </p>
              <p className="text-gray-600">Total Assets</p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center">
            <FileText className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-2xl font-bold text-gray-900">
                {stats.byObjective['Create Will'] || 0}
              </p>
              <p className="text-gray-600">Will Requests</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search clients by name, ID, or objective..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={filterBy}
                onChange={(e) => setFilterBy(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="all">All Objectives</option>
                {objectiveOptions.map(option => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="name">By Name</option>
              <option value="assets">By Asset Value</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertCircle className="h-4 w-4 text-red-600 mr-2" />
            <p className="text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Client Grid */}
      {filteredClients.length === 0 ? (
        <div className="text-center py-12">
          <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No clients found</h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || filterBy !== 'all' 
              ? 'Try adjusting your search or filter criteria.' 
              : 'Get started by creating your first client questionnaire.'
            }
          </p>
          <button
            onClick={() => window.location.href = '/questionnaire'}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create First Client
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredClients.map((client) => (
            <ClientCard
              key={client.clientId}
              client={client}
              onView={(client) => {
                setSelectedClient(client);
                setShowClientModal(true);
              }}
              onEdit={(client) => {
                // Navigate to edit form
                window.location.href = `/questionnaire?edit=${client.clientId}`;
              }}
              onDelete={handleDeleteClient}
            />
          ))}
        </div>
      )}
    </div>
  );
}