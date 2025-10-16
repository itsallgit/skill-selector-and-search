import React from 'react';

/**
 * TabNavigation - Two-tab navigation for search results
 * 
 * Features:
 * - Two tabs: "Skills & Scoring" | "Ranked Users" (default)
 * - Sticky on desktop, scrollable on mobile
 * - Hard separation - clicking switches visible content
 * - Clear visual indicator of active tab
 * - Minimal screen real estate
 * 
 * Props:
 * - activeTab: 'skills' | 'users' (controlled)
 * - onTabChange: (tab) => void callback
 * - skillCount: number of matched skills
 * - userCount: number of ranked users
 */
function TabNavigation({ activeTab, onTabChange, skillCount = 0, userCount = 0 }) {
  return (
    <div className="tab-navigation">
      <div className="tab-buttons">
        <button
          className={`tab-button ${activeTab === 'skills' ? 'active' : ''}`}
          onClick={() => onTabChange('skills')}
          aria-pressed={activeTab === 'skills'}
        >
          <span className="tab-label">Skills & Scoring</span>
          {skillCount > 0 && (
            <span className="tab-count">{skillCount}</span>
          )}
        </button>
        
        <button
          className={`tab-button ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => onTabChange('users')}
          aria-pressed={activeTab === 'users'}
        >
          <span className="tab-label">Ranked Users</span>
          {userCount > 0 && (
            <span className="tab-count">{userCount}</span>
          )}
        </button>
      </div>
    </div>
  );
}

export default TabNavigation;
