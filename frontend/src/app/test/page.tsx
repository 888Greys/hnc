'use client';

import { useState } from 'react';

export default function TestPage() {
  const [results, setResults] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addResult = (message: string) => {
    setResults(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const runTests = async () => {
    setIsLoading(true);
    setResults([]);
    
    try {
      // Test 1: Frontend health check
      addResult('🔄 Testing frontend...');
      const frontendResponse = await fetch('/api/health');
      const frontendData = await frontendResponse.json();
      addResult(`✅ Frontend: ${frontendData.status}`);
      
      // Test 2: Backend health check
      addResult('🔄 Testing backend connection...');
      const backendResponse = await fetch('http://localhost:8000/health');
      const backendData = await backendResponse.json();
      addResult(`✅ Backend: ${backendData.status}`);
      
      // Test 3: Authentication
      addResult('🔄 Testing authentication...');
      const loginResponse = await fetch('http://localhost:8000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });
      
      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        addResult(`✅ Login successful: ${loginData.user.username} (${loginData.user.role})`);
        
        // Test 4: Authenticated request
        addResult('🔄 Testing authenticated request...');
        const meResponse = await fetch('http://localhost:8000/auth/me', {
          headers: { 'Authorization': `Bearer ${loginData.access_token}` }
        });
        
        if (meResponse.ok) {
          const meData = await meResponse.json();
          addResult(`✅ Authenticated request: ${meData.user.username}`);
        } else {
          addResult('❌ Authenticated request failed');
        }
      } else {
        addResult('❌ Login failed');
      }
      
    } catch (error) {
      addResult(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            HNC Legal System - Communication Test
          </h1>
          
          <p className="text-gray-600 mb-8">
            This page tests the communication between frontend and backend services.
          </p>
          
          <button
            onClick={runTests}
            disabled={isLoading}
            className={`px-6 py-3 rounded-lg font-medium text-white ${
              isLoading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isLoading ? 'Running Tests...' : 'Run Communication Tests'}
          </button>
          
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Results:</h2>
            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
              {results.length === 0 ? (
                <div className="text-gray-400">Click "Run Communication Tests" to start...</div>
              ) : (
                results.map((result, index) => (
                  <div key={index} className="mb-1">{result}</div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}