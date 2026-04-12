import React, { useState, lazy, Suspense } from 'react';

// Lazy load components for better performance
const InventoryStatusView = lazy(() => import('./InventoryStatusView'));
const ProfileSummaryView = lazy(() => import('./ProfileSummaryView'));

const DebugPanel = () => {
  const [activeTab, setActiveTab] = useState('inventory');
  const [isVisible, setIsVisible] = useState(false);

  const tabs = [
    { id: 'inventory', label: 'Inventory', component: InventoryStatusView },
    { id: 'profile', label: 'Profile', component: ProfileSummaryView },
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {isVisible ? (
        <div className="w-full max-w-4xl bg-yellow-50 rounded-lg shadow-2xl border-4 border-red-500 overflow-hidden">
          {/* Header */}
          <div className="flex justify-between items-center bg-gray-800 text-white px-4 py-3">
            <div className="flex items-center space-x-2">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <h2 className="text-lg font-semibold">Debug Panel</h2>
              <span className="text-xs bg-gray-600 px-2 py-1 rounded">Dev Only</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsVisible(false)}
                className="p-1 hover:bg-gray-700 rounded transition-colors"
                title="Hide panel"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex flex-wrap border-b border-gray-200 bg-gray-50">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-white text-gray-800 border-b-2 border-gray-800'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="p-4 max-h-[70vh] overflow-y-auto">
            <Suspense fallback={
              <div className="text-center py-8">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-800"></div>
                <p className="mt-2 text-gray-600">Loading debug view...</p>
              </div>
            }>
              {ActiveComponent && <ActiveComponent />}
            </Suspense>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 text-xs text-gray-500">
            <div className="flex justify-between items-center">
              <div>
                Backend: <span className="font-mono">http://localhost:8000</span>
              </div>
              <div className="flex items-center space-x-4">
                <span>Use for development/debugging only</span>
                <button
                  onClick={() => setIsVisible(false)}
                  className="text-gray-600 hover:text-gray-800 text-sm"
                >
                  Hide Panel
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setIsVisible(true)}
          className="bg-red-600 text-white px-6 py-3 rounded-lg shadow-2xl hover:bg-red-700 transition-colors flex items-center space-x-2 border-4 border-yellow-400"
        >
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="font-bold">SHOW DEBUG PANEL</span>
        </button>
      )}
    </div>
  );
};

export default DebugPanel;