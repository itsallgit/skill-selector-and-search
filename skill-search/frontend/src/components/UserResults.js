import React from 'react';
import { Link } from 'react-router-dom';

function UserResults({ users, title = "Users" }) {
  if (!users || users.length === 0) {
    return null;
  }
  
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
  
  return (
    <section className="section">
      <h2>{title} ({users.length})</h2>
      <div className="users-list">
        {users.map((user) => (
          <div key={user.email} className="user-card">
            <div className="user-header">
              <div className="user-info">
                <span className="user-rank">#{user.rank}</span>
                <Link to={`/user/${encodeURIComponent(user.email)}`} className="user-name">
                  {user.name}
                </Link>
                <span className="user-email">{user.email}</span>
              </div>
              <div className="user-score">
                <span className="score-value">{user.score.toFixed(1)}</span>
                <span className="score-label">Score</span>
              </div>
            </div>
            
            {user.matched_skills && user.matched_skills.length > 0 && (
              <div className="user-skills">
                <p className="skills-header">
                  Matched Skills ({user.matched_skills.length})
                  {user.transfer_bonus > 0 && (
                    <span className="transfer-bonus" title="Transfer bonus for related technologies">
                      +{(user.transfer_bonus * 100).toFixed(1)}% transfer
                    </span>
                  )}
                </p>
                <div className="skills-tags">
                  {user.matched_skills.map((skill, index) => (
                    <span 
                      key={index} 
                      className={`skill-tag ${getRatingClass(skill.rating || 1)}`}
                    >
                      {skill.title}
                      <span className="skill-tag-meta">
                        L{skill.level} · {getRatingLabel(skill.rating || 1)}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

export default UserResults;
