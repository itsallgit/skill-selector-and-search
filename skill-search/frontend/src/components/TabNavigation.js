import React, { useEffect, useRef, useState } from 'react';

/**
 * TabNavigation - Three-tab navigation with sliding selector
 * 
 * Features:
 * - Three tabs: Relevant Skills | User Scoring | Ranked Users (default)
 * - Sliding black selector pill animates to active tab
 * - White text on selected, black text on unselected
 * - Rounded corners, professional design
 * - Sticky on desktop, scrollable on mobile
 * 
 * Props:
 * - activeTab: 'skills' | 'scoring' | 'users' (controlled)
 * - onTabChange: (tab) => void callback
 * - skillCount: number of matched skills
 * - userCount: number of ranked users
 */
function TabNavigation({ activeTab, onTabChange, skillCount = 0, userCount = 0 }) {
  const [selectorStyle, setSelectorStyle] = useState({});
  const tabRefs = useRef({});

  // Update selector position when active tab changes
  useEffect(() => {
    const activeTabElement = tabRefs.current[activeTab];
    if (activeTabElement) {
      setSelectorStyle({
        width: activeTabElement.offsetWidth,
        transform: `translateX(${activeTabElement.offsetLeft}px)`
      });
    }
  }, [activeTab]);

  const tabs = [
    { id: 'skills', label: 'Relevant Skills', count: skillCount },
    { id: 'scoring', label: 'User Scoring', count: null },
    { id: 'users', label: 'Ranked Users', count: userCount }
  ];

  return (
    <div className="tab-navigation">
      <div className="tab-container">
        <div className="tab-selector" style={selectorStyle}></div>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            ref={(el) => (tabRefs.current[tab.id] = el)}
            className={`tab-button-pill ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => onTabChange(tab.id)}
            aria-pressed={activeTab === tab.id}
          >
            <span className="tab-label">{tab.label}</span>
            {tab.count !== null && tab.count > 0 && (
              <span className="tab-count">{tab.count}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

export default TabNavigation;
