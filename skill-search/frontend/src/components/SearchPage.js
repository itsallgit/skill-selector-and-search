import React, { useState } from 'react';
import SearchBar from './SearchBar';
import SkillResults from './SkillResults';
import UserResults from './UserResults';
import ScoreBuckets from './ScoreBuckets';

function SearchPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  
  const handleSearch = async (query) => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    setLoading(true);
    setError(null);
    setResults(null);
    
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
      
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Failed to search. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="container">
      <header className="header">
        <h1>Skills Search</h1>
        <p>Find users by skills using natural language queries</p>
      </header>
      
      <SearchBar onSearch={handleSearch} loading={loading} />
      
      {error && (
        <div className="error-message">
          <p>⚠️ {error}</p>
        </div>
      )}
      
      {results && (
        <div className="results-container">
          <SkillResults skills={results.matched_skills} />
          <UserResults users={results.top_users} title="Top Matches" />
          <ScoreBuckets buckets={results.buckets} />
        </div>
      )}
      
      {!loading && !error && !results && (
        <div className="empty-state">
          <p>Enter a search query to find users with matching skills</p>
          <p className="hint">Example: "AWS Lambda and serverless architecture"</p>
        </div>
      )}
    </div>
  );
}

export default SearchPage;
