'use client';

import { useState, useEffect } from 'react';
import { Users, FileText, Brain, TrendingUp, Clock, Shield } from 'lucide-react';

interface DashboardStats {
  totalClients: number;
  completedQuestionnaires: number;
  aiProposalsGenerated: number;
  documentsCreated: number;
  activeUsers: number;
  systemUptime: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalClients: 0,
    completedQuestionnaires: 0,
    aiProposalsGenerated: 0,
    documentsCreated: 0,
    activeUsers: 0,
    systemUptime: '0 days'
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Simulate loading data - in real app, this would fetch from API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        setStats({
          totalClients: 24,
          completedQuestionnaires: 18,
          aiProposalsGenerated: 15,
          documentsCreated: 12,
          activeUsers: 3,
          systemUptime: '7 days'
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

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
          subtitle="Completed this month"
          color="bg-green-600"
        />
        <StatCard
          icon={Brain}
          title="AI Proposals"
          value={stats.aiProposalsGenerated}
          subtitle="Generated this month"
          color="bg-purple-600"
        />
        <StatCard
          icon={TrendingUp}
          title="Documents"
          value={stats.documentsCreated}
          subtitle="Created this month"
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
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
              <span className="text-sm text-gray-600">
                New questionnaire completed by John Doe
              </span>
              <span className="text-xs text-gray-400">2 hours ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
              <span className="text-sm text-gray-600">
                AI proposal generated for estate planning
              </span>
              <span className="text-xs text-gray-400">4 hours ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
              <span className="text-sm text-gray-600">
                Will document created for client_58a83757
              </span>
              <span className="text-xs text-gray-400">6 hours ago</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
              <span className="text-sm text-gray-600">
                System backup completed successfully
              </span>
              <span className="text-xs text-gray-400">1 day ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}