import React, { useState, useEffect, useRef } from 'react';

function SearchBar({ onSearch, onNewSearch, loading, currentQuery = '', showResults = false }) {
  const [query, setQuery] = useState(currentQuery);
  const textareaRef = useRef(null);
  
  // Update query when currentQuery prop changes
  useEffect(() => {
    setQuery(currentQuery);
  }, [currentQuery]);
  
  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [query]);
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };
  
  const handleNewSearch = () => {
    setQuery(''); // Clear the input
    onNewSearch(); // Call parent handler to return to intro
  };
  
  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <textarea
        ref={textareaRef}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g., AWS Lambda and serverless architecture"
        disabled={loading}
        className="search-input search-textarea"
        rows={1}
      />
      {showResults ? (
        <button 
          type="button"
          onClick={handleNewSearch}
          disabled={loading}
          className="btn btn-primary"
        >
          New Search
        </button>
      ) : (
        <button 
          type="submit" 
          disabled={loading || !query.trim()}
          className="btn btn-primary"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      )}
    </form>
  );
}

export default SearchBar;
