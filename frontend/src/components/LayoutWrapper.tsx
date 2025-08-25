'use client';

import { useState, useEffect } from 'react';
import { Navigation } from './Navigation';

interface User {
  username: string;
  role: string;
  first_name?: string;
  last_name?: string;
}

interface LayoutWrapperProps {
  children: React.ReactNode;
}

export function LayoutWrapper({ children }: LayoutWrapperProps) {
  const [user, setUser] = useState<User | null>(null);

  // Mock user for now - in real app, this would come from auth context
  useEffect(() => {
    // Simulate loading user data
    const mockUser: User = {
      username: 'admin',
      role: 'admin',
      first_name: 'System',
      last_name: 'Administrator'
    };
    setUser(mockUser);
  }, []);

  const handleLogout = () => {
    // In a real implementation, this would:
    // 1. Call the API service logout method
    // 2. Clear any local state
    // 3. Redirect to login page
    console.log('Logout function called');
    setUser(null);
    // For now, just refresh the page or redirect
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen flex">
      <Navigation user={user || undefined} onLogout={handleLogout} />
      <main className="flex-1 lg:ml-64">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}