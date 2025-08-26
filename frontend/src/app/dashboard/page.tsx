'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Users, FileText, Brain, TrendingUp, Clock, Shield } from 'lucide-react';
import apiService from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

interface DashboardStats {
  totalClients: number;
  completedQuestionnaires: number;
  aiProposalsGenerated: number;
  documentsCreated: number;
  activeUsers: number;
  systemUptime: string;
  recentClients: number;
}

interface RecentActivity {
  type: string;
  description: string;
  time_ago: string;
  color: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, tokens } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalClients: 0,
    completedQuestionnaires: 0,
    aiProposalsGenerated: 0,
    documentsCreated: 0,
    activeUsers: 0,
    systemUptime: '0 days',
    recentClients: 0
  });
  const [recentActivities, setRecentActivities] = useState<RecentActivity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!isAuthenticated || authLoading) {
        return;
      }
      
      try {
        setIsLoading(true);
        setError(null);
        
        const dashboardData = await apiService.getDashboardStatistics();
        
        setStats(dashboardData.statistics);
        setRecentActivities(dashboardData.recent_activities || []);
        
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        setError('Failed to load dashboard data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [isAuthenticated, authLoading]);

  const getActivityColor = (color: string) => {
    const colorMap = {
      green: 'bg-green-400',
      blue: 'bg-blue-400',
      purple: 'bg-purple-400',
      orange: 'bg-orange-400',
      red: 'bg-red-400'
    };
    return colorMap[color as keyof typeof colorMap] || 'bg-gray-400';
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

  const StatCard = ({ icon: Icon, title, value, subtitle, color }: {
    icon: any;
    title: string;
    value: string | number;
    subtitle: string;
    color: string;
  }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <h3 className="text-sm font-medium text-gray-500">{title}</h3>
          <p className="text-2xl font-semibold text-gray-900">
            {isLoading ? '...' : value}
          </p>
          <p className="text-xs text-gray-400">{subtitle}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Overview of your HNC Legal Questionnaire System</p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <StatCard
          icon={Users}
          title="Total Clients"
          value={stats.totalClients}
          subtitle="Active client records"
          color="bg-blue-600"
        />
        <StatCard
          icon={FileText}
          title="Questionnaires"
          value={stats.completedQuestionnaires}
          subtitle="Completed submissions"
          color="bg-green-600"
        />
        <StatCard
          icon={Brain}
          title="AI Proposals"
          value={stats.aiProposalsGenerated}
          subtitle="Generated proposals"
          color="bg-purple-600"
        />
        <StatCard
          icon={TrendingUp}
          title="Documents"
          value={stats.documentsCreated}
          subtitle="Created documents"
          color="bg-orange-600"
        />
        <StatCard
          icon={Clock}
          title="Active Users"
          value={stats.activeUsers}
          subtitle="Currently online"
          color="bg-indigo-600"
        />
        <StatCard
          icon={Shield}
          title="System Uptime"
          value={stats.systemUptime}
          subtitle="Continuous operation"
          color="bg-emerald-600"
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
        </div>
        <div className="p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mr-2"></div>
              <span className="text-gray-600">Loading activities...</span>
            </div>
          ) : recentActivities.length > 0 ? (
            <div className="space-y-4">
              {recentActivities.map((activity, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${getActivityColor(activity.color)}`}></div>
                  <span className="text-sm text-gray-600 flex-1">
                    {activity.description}
                  </span>
                  <span className="text-xs text-gray-400">{activity.time_ago}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No recent activity</p>
              <p className="text-sm mt-1">Activity will appear here as users interact with the system</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}