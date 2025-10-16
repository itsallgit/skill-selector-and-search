import React from 'react';
import { FiSearch, FiZap, FiUsers } from 'react-icons/fi';

/**
 * IntroScreen - Hero center landing page shown before search
 * 
 * Features:
 * - Professional tagline above centered search
 * - Visual flow with line icons: Search → Skills → Users
 * - Search bar integrated below flow
 * - Transparent green icon backgrounds
 * - Clean, minimal design with professional aesthetic
 * - Hidden once search results appear
 */
function IntroScreen({ onSearch, loading }) {
  const [query, setQuery] = React.useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <div className="intro-screen">
      <div className="intro-content">
        {/* Tagline */}
        <h2 className="intro-tagline">Describe the role, discover the talent</h2>
        
        {/* Visual Process Flow */}
        <div className="intro-flow">
          <div className="intro-flow-step">
            <div className="intro-icon-wrapper">
              <FiSearch className="intro-icon" />
            </div>
            <p className="intro-step-label">Role Description</p>
          </div>
          
          <div className="intro-flow-arrow">
            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
              <path d="M0 12H38M38 12L28 2M38 12L28 22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          
          <div className="intro-flow-step">
            <div className="intro-icon-wrapper">
              <FiZap className="intro-icon" />
            </div>
            <p className="intro-step-label">Relevant Skills</p>
          </div>
          
          <div className="intro-flow-arrow">
            <svg width="40" height="24" viewBox="0 0 40 24" fill="none">
              <path d="M0 12H38M38 12L28 2M38 12L28 22" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          
          <div className="intro-flow-step">
            <div className="intro-icon-wrapper">
              <FiUsers className="intro-icon" />
            </div>
            <p className="intro-step-label">Ranked Users</p>
          </div>
        </div>

        {/* Integrated Search Bar */}
        <form onSubmit={handleSubmit} className="intro-search-form">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter role description or required skills..."
            disabled={loading}
            className="intro-search-input"
          />
          <button 
            type="submit" 
            disabled={loading || !query.trim()}
            className="intro-search-button"
          >
            {loading ? 'Searching...' : 'Find Matching Users'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default IntroScreen;
