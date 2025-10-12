import React, { useState } from 'react';

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };
  
  return (
    <form onSubmit={handleSubmit} className="search-bar">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g., AWS Lambda and serverless architecture"
        disabled={loading}
        className="search-input"
      />
      <button 
        type="submit" 
        disabled={loading || !query.trim()}
        className="btn btn-primary"
      >
        {loading ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}

export default SearchBar;
