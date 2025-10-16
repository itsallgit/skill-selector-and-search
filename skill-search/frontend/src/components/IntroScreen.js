import React, { useRef, useEffect } from 'react';
import { FiSearch, FiZap, FiUsers } from 'react-icons/fi';

/**
 * IntroScreen - Hero center landing page shown before search
 * 
 * Features:
 * - Professional tagline above centered search
 * - Visual flow with line icons: Search → Skills → Users
 * - Search bar integrated below flow with textarea for multi-line support
 * - Transparent green icon backgrounds
 * - Clean, minimal design with professional aesthetic
 * - Hidden once search results appear
 * - Auto-focuses search input when component mounts
 */
function IntroScreen({ onSearch, loading }) {
  const [query, setQuery] = React.useState('');
  const textareaRef = useRef(null);
  
  // Auto-focus the search input when component mounts
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []); // Empty dependency array means this runs once on mount
  
  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [query]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };
  
  const handleKeyDown = (e) => {
    // Submit on Enter, allow Shift+Enter for new lines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
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
          <textarea
            ref={textareaRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter role description or required skills..."
            disabled={loading}
            className="intro-search-input intro-search-textarea"
            rows={1}
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
