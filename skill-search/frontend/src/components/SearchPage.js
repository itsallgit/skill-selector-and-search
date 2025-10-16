import React, { useState } from 'react';
import SearchBar from './SearchBar';
import IntroScreen from './IntroScreen';
import TabNavigation from './TabNavigation';
import SkillResults from './SkillResults';
import ScoringExplanation from './ScoringExplanation';
import UserResults from './UserResults';
import ScoreBuckets from './ScoreBuckets';

function SearchPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [activeTab, setActiveTab] = useState('users'); // Default to "Ranked Users"
  const [hasSearched, setHasSearched] = useState(false); // Track if search has been performed
  const [currentQuery, setCurrentQuery] = useState(''); // Track the current search query
  
  const handleSearch = async (query) => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResults(null);
    setActiveTab('users'); // Reset to users tab on new search
    setCurrentQuery(query); // Store the current query
    
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          top_k_skills: 10,
          top_n_users: 5
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Search failed');
      }
      
      const data = await response.json();
      setResults(data);
      setHasSearched(true); // Mark that search has been performed
      
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Failed to search. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleNewSearch = () => {
    // Clear everything and return to intro screen
    setHasSearched(false);
    setResults(null);
    setError(null);
    setCurrentQuery('');
    setActiveTab('users');
  };
  
  const handleTabChange = (tab) => {
    setActiveTab(tab);
  };
  
  return (
    <div className="app-wrapper">
      <header className="header full-bleed">
        <div className="container">
          <div className="nav-bar">
            <h1>Skill Search</h1>
          </div>
        </div>
      </header>
      
      <div className="container">
        {/* Intro Screen with integrated search - only shown when no search has been performed */}
        {!hasSearched && !loading && !error && (
          <IntroScreen onSearch={handleSearch} loading={loading} />
        )}
        
        {/* Query Display and New Search Button - shown at top after first search */}
        {hasSearched && (
          <div className="search-results-header">
            <div className="query-display-quotes">
              <span className="quote-icon quote-left">"</span>
              <p className="query-text-italic">{currentQuery}</p>
              <span className="quote-icon quote-right">"</span>
            </div>
            <button 
              onClick={handleNewSearch}
              disabled={loading}
              className="btn btn-primary new-search-button"
            >
              New Search
            </button>
          </div>
        )}
      
        {/* Error Message */}
        {error && (
          <div className="error-message">
            <p>⚠️ {error}</p>
          </div>
        )}
      
        {/* Results with Tab Navigation */}
        {results && (
          <>
            {/* Tab Navigation - sticky on desktop */}
            <TabNavigation
              activeTab={activeTab}
              onTabChange={handleTabChange}
              skillCount={results.matched_skills?.length || 0}
              userCount={results.top_users?.length || 0}
            />
            
            {/* Tab Content */}
            <div className="tab-content">
              {/* Relevant Skills Tab */}
              {activeTab === 'skills' && (
                <div className="skills-tab">
                  <SkillResults skills={results.matched_skills} />
                </div>
              )}
              
              {/* User Scoring Tab */}
              {activeTab === 'scoring' && (
                <div className="scoring-tab">
                  <ScoringExplanation />
                </div>
              )}
              
              {/* Ranked Users Tab */}
              {activeTab === 'users' && (
                <div className="users-tab">
                  <UserResults users={results.top_users} title="Top Ranked Users" />
                  <ScoreBuckets buckets={results.buckets} />
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default SearchPage;
