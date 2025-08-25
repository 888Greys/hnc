'use client';

import { useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { 
  Home, 
  Users, 
  FileText, 
  Brain, 
  Download, 
  Settings, 
  LogOut, 
  Menu,
  X,
  User,
  Shield
} from 'lucide-react';

interface NavigationProps {
  user?: {
    username: string;
    role: string;
    first_name?: string;
    last_name?: string;
  };
  onLogout: () => void;
}

const navItems = [
  { 
    name: 'Dashboard', 
    href: '/dashboard', 
    icon: Home,
    description: 'Overview and statistics'
  },
  { 
    name: 'Clients', 
    href: '/clients', 
    icon: Users,
    description: 'Manage client records'
  },
  { 
    name: 'Questionnaire', 
    href: '/questionnaire', 
    icon: FileText,
    description: 'Digital client intake'
  },
  { 
    name: 'AI Proposals', 
    href: '/ai-proposals', 
    icon: Brain,
    description: 'Generated legal suggestions'
  },
  { 
    name: 'Documents', 
    href: '/documents', 
    icon: Download,
    description: 'Export and templates'
  },
  { 
    name: 'Settings', 
    href: '/settings', 
    icon: Settings,
    description: 'System configuration',
    adminOnly: true
  },
];

export function Navigation({ user, onLogout }: NavigationProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const isAdmin = user?.role === 'admin';
  const displayName = user?.first_name && user?.last_name 
    ? `${user.first_name} ${user.last_name}`
    : user?.username || 'User';

  const filteredNavItems = navItems.filter(item => 
    !item.adminOnly || isAdmin
  );

  const handleNavigation = (href: string) => {
    router.push(href);
    setIsMobileMenuOpen(false);
  };

  const handleLogout = () => {
    onLogout();
    setIsMobileMenuOpen(false);
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col lg:fixed lg:inset-y-0 lg:bg-gray-900">
        <div className="flex flex-col flex-grow pt-5 pb-4 overflow-y-auto">
          {/* Logo */}
          <div className="flex items-center flex-shrink-0 px-4">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-indigo-400" />
              <div className="ml-3">
                <h1 className="text-xl font-bold text-white">HNC Legal</h1>
                <p className="text-xs text-gray-300">Questionnaire System</p>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="mt-8 flex-1 px-2 space-y-1">
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              
              return (
                <button
                  key={item.name}
                  onClick={() => handleNavigation(item.href)}
                  className={cn(
                    "group flex items-center px-2 py-2 text-sm font-medium rounded-md w-full text-left transition-colors",
                    isActive
                      ? "bg-gray-800 text-white"
                      : "text-gray-300 hover:bg-gray-700 hover:text-white"
                  )}
                >
                  <Icon
                    className={cn(
                      "mr-3 h-5 w-5",
                      isActive ? "text-white" : "text-gray-400 group-hover:text-white"
                    )}
                  />
                  <div>
                    <div>{item.name}</div>
                    <div className="text-xs text-gray-400 group-hover:text-gray-300">
                      {item.description}
                    </div>
                  </div>
                </button>
              );
            })}
          </nav>

          {/* User Info */}
          <div className="flex-shrink-0 px-4 py-4 border-t border-gray-700">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-8 w-8 bg-indigo-500 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-white" />
                </div>
              </div>
              <div className="ml-3 flex-1">
                <p className="text-sm font-medium text-white">{displayName}</p>
                <p className="text-xs text-gray-300 capitalize">{user?.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="ml-3 text-gray-400 hover:text-white transition-colors"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Header */}
      <div className="lg:hidden">
        <div className="flex items-center justify-between bg-gray-900 px-4 py-3">
          <div className="flex items-center">
            <Shield className="h-6 w-6 text-indigo-400" />
            <h1 className="ml-2 text-lg font-bold text-white">HNC Legal</h1>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <p className="text-sm font-medium text-white">{displayName}</p>
              <p className="text-xs text-gray-300 capitalize">{user?.role}</p>
            </div>
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-400 hover:text-white"
            >
              {isMobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="bg-gray-900 border-t border-gray-700">
            <nav className="px-2 py-3 space-y-1">
              {filteredNavItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                
                return (
                  <button
                    key={item.name}
                    onClick={() => handleNavigation(item.href)}
                    className={cn(
                      "group flex items-center px-3 py-2 text-sm font-medium rounded-md w-full text-left transition-colors",
                      isActive
                        ? "bg-gray-800 text-white"
                        : "text-gray-300 hover:bg-gray-700 hover:text-white"
                    )}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    <div>
                      <div>{item.name}</div>
                      <div className="text-xs text-gray-400">{item.description}</div>
                    </div>
                  </button>
                );
              })}
              
              <div className="pt-3 border-t border-gray-700">
                <button
                  onClick={handleLogout}
                  className="group flex items-center px-3 py-2 text-sm font-medium rounded-md w-full text-left text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
                >
                  <LogOut className="mr-3 h-5 w-5" />
                  Logout
                </button>
              </div>
            </nav>
          </div>
        )}
      </div>
    </>
  );
}