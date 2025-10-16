import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { FiInfo } from 'react-icons/fi';
import ScoreBreakdownModal from './ScoreBreakdownModal';

function UserResults({ users, title = "Users" }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  
  if (!users || users.length === 0) {
    return null;
  }
  
  const handleScoreClick = (user) => {
    setSelectedUser(user);
    setModalOpen(true);
  };
  
  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedUser(null);
  };
  
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
  
  const getLevelLabel = (level) => {
    const labels = {
      1: 'L1 Capability',
      2: 'L2 Capability', 
      3: 'Generic Skill',
      4: 'Technology'
    };
    return labels[level] || `Level ${level}`;
  };
  
  // Get score color class based on value (0-100 scale)
  const getScoreColorClass = (score) => {
    if (score >= 80) return 'score-excellent'; // Dark green
    if (score >= 60) return 'score-strong';    // Green
    if (score >= 40) return 'score-good';      // Yellow-green
    if (score >= 20) return 'score-fair';      // Orange
    return 'score-low';                         // Gray
  };
  
  // Format parent titles WITHOUT the skill itself at the end (since it's already in the title row)
  const formatSkillHierarchy = (parentTitles, skillTitle) => {
    if (!parentTitles || parentTitles.length === 0) {
      return null; // No hierarchy to show
    }
    // Only show parent titles, NOT the skill itself
    return parentTitles.join(' → ');
  };
  
  return (
    <section className="matched-skills-section">
      <div className="section-header-row">
        <div className="section-header-main">
          <h2>{title} ({users.length})</h2>
        </div>
      </div>
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
              <div className={`user-score ${getScoreColorClass(user.score)}`}>
                <div className="score-display">
                  <span className="score-value">{user.score.toFixed(1)}</span>
                  <span className="score-label">Score</span>
                </div>
                {user.score_breakdown && (
                  <button 
                    className="score-info-button"
                    onClick={() => handleScoreClick(user)}
                    aria-label="View score breakdown"
                    title="View detailed score breakdown"
                  >
                    <FiInfo />
                  </button>
                )}
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
                  {user.matched_skills.map((skill, index) => {
                    const hierarchy = formatSkillHierarchy(skill.parent_titles, skill.title);
                    return (
                      <div 
                        key={index} 
                        className={`skill-tag-enhanced ${getRatingClass(skill.rating || 1)}`}
                      >
                        <div className="skill-tag-title">{skill.title}</div>
                        {hierarchy && (
                          <div className="skill-tag-hierarchy">
                            {hierarchy}
                          </div>
                        )}
                        <div className="skill-tag-meta">
                          <span className="skill-level-label">{getLevelLabel(skill.level)}</span>
                          <span className="skill-rating-badge">{getRatingLabel(skill.rating || 1)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* Score Breakdown Modal */}
      <ScoreBreakdownModal
        isOpen={modalOpen}
        onClose={handleCloseModal}
        userName={selectedUser?.name}
        scoreBreakdown={selectedUser?.score_breakdown}
      />
    </section>
  );
}

export default UserResults;
