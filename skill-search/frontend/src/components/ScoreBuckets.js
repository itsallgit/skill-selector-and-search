import React, { useState } from 'react';
import UserResults from './UserResults';

function ScoreBuckets({ buckets }) {
  const [expandedBuckets, setExpandedBuckets] = useState({});
  
  if (!buckets || buckets.length === 0) {
    return null;
  }
  
  const toggleBucket = (bucketName) => {
    setExpandedBuckets(prev => ({
      ...prev,
      [bucketName]: !prev[bucketName]
    }));
  };
  
  return (
    <section className="section buckets-section">
      <h2>Additional Matches</h2>
      {buckets.map((bucket) => {
        if (bucket.count === 0) {
          return null;
        }
        
        const isExpanded = expandedBuckets[bucket.name];
        
        return (
          <div key={bucket.name} className="score-bucket">
            <button 
              className="bucket-header"
              onClick={() => toggleBucket(bucket.name)}
            >
              <span className="bucket-name">{bucket.name}</span>
              <span className="bucket-info">
                <span className="bucket-score-range">
                  {bucket.min_score.toFixed(0)}-{bucket.max_score.toFixed(0)} points
                </span>
                <span className="bucket-count">{bucket.count} users</span>
                <span className={`bucket-toggle ${isExpanded ? 'expanded' : ''}`}>
                  {isExpanded ? '▼' : '▶'}
                </span>
              </span>
            </button>
            
            {isExpanded && (
              <div className="bucket-content">
                <UserResults 
                  users={bucket.users} 
                  title={`${bucket.name} - ${bucket.count} Users`}
                />
              </div>
            )}
          </div>
        );
      })}
    </section>
  );
}

export default ScoreBuckets;
