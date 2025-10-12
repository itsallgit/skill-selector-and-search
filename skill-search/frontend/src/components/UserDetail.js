import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

function UserDetail() {
  const { email } = useParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await fetch(`/api/users/${encodeURIComponent(email)}`);
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch user');
        }
        
        const data = await response.json();
        setUser(data);
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUser();
  }, [email]);
  
  const getRatingLabel = (rating) => {
    const labels = {
      1: 'Beginner',
      2: 'Intermediate',
      3: 'Advanced'
    };
    return labels[rating] || 'Unknown';
  };
  
  const getRatingClass = (rating) => {
    return `rating-${rating}`;
  };
  
  const renderSkillSection = (title, skills) => {
    if (!skills || skills.length === 0) {
      return null;
    }
    
    return (
      <div className="skill-section">
        <h3>{title} ({skills.length})</h3>
        <div className="skills-tags">
          {skills.map((skill, index) => (
            <span 
              key={index} 
              className={`skill-tag ${getRatingClass(skill.rating)}`}
            >
              {skill.title}
              <span className="skill-tag-meta">
                {getRatingLabel(skill.rating)}
              </span>
            </span>
          ))}
        </div>
      </div>
    );
  };
  
  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading user details...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="container">
        <header className="header">
          <h1>Error</h1>
        </header>
        <div className="error-message">
          <p>⚠️ {error}</p>
          <Link to="/" className="btn btn-secondary">← Back to Search</Link>
        </div>
      </div>
    );
  }
  
  if (!user) {
    return null;
  }
  
  return (
    <div className="container">
      <header className="header">
        <Link to="/" className="back-link">← Back to Search</Link>
        <h1>{user.name}</h1>
        <p className="user-email">{user.email}</p>
        <p className="user-stats">{user.total_skills} total skills</p>
      </header>
      
      <div className="user-detail-content">
        {renderSkillSection('Categories (L1)', user.l1_skills)}
        {renderSkillSection('Sub-categories (L2)', user.l2_skills)}
        {renderSkillSection('Skills (L3)', user.l3_skills)}
        {renderSkillSection('Technologies (L4)', user.l4_skills)}
        
        {user.total_skills === 0 && (
          <div className="empty-state">
            <p>This user has no skills recorded.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default UserDetail;
