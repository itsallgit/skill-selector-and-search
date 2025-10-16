import React from 'react';
import { FiX, FiChevronDown, FiChevronUp } from 'react-icons/fi';

/**
 * ScoreBreakdownModal - Modal showing detailed score breakdown for individual user
 * 
 * Features:
 * - Shows ALL skills with top 80% visible, rest expandable
 * - Displays point contribution and skill hierarchy per skill
 * - Detailed transfer bonus with source → matched skill relationships
 * - Clean, professional modal design matching user card styling
 * - Close on backdrop click or X button
 * 
 * Props:
 * - isOpen: boolean
 * - onClose: () => void callback
 * - userName: string
 * - scoreBreakdown: object from API (score_breakdown field)
 */
function ScoreBreakdownModal({ isOpen, onClose, userName, scoreBreakdown }) {
  const [showAllSkills, setShowAllSkills] = React.useState(false);
  
  // Prevent scroll when modal is open - MUST be before early returns
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // Early return AFTER all hooks
  if (!isOpen || !scoreBreakdown) return null;

  const {
    normalized_score,
    score_interpretation,
    skill_contributions,
    transfer_bonus_total,
    transfer_bonus_details,
    total_matched_skills
  } = scoreBreakdown;

  // Calculate which skills are in top 80%
  const totalPoints = skill_contributions.reduce((sum, skill) => sum + skill.points_contributed, 0);
  let cumulativePercentage = 0;
  let top80Index = skill_contributions.length;
  
  for (let i = 0; i < skill_contributions.length; i++) {
    cumulativePercentage += (skill_contributions[i].points_contributed / totalPoints) * 100;
    if (cumulativePercentage >= 80 && top80Index === skill_contributions.length) {
      top80Index = Math.max(i + 1, 3); // Show at least 3 skills
      break;
    }
  }

  const topSkills = skill_contributions.slice(0, top80Index);
  const remainingSkills = skill_contributions.slice(top80Index);
  const remainingPercentage = remainingSkills.reduce((sum, skill) => sum + skill.percentage_of_total, 0);

  // Rating label helper
  const getRatingLabel = (rating) => {
    const labels = { 1: 'Beginner', 2: 'Intermediate', 3: 'Advanced' };
    return labels[rating] || 'Unknown';
  };

  // Level label helper
  const getLevelLabel = (level) => {
    const labels = {
      1: 'L1 Category',
      2: 'L2 Sub-category',
      3: 'L3 Generic Skill',
      4: 'L4 Technology'
    };
    return labels[level] || `Level ${level}`;
  };
  
  // Get score color class
  const getScoreColorClass = (score) => {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-strong';
    if (score >= 40) return 'score-good';
    if (score >= 20) return 'score-fair';
    return 'score-low';
  };
  
  // Format hierarchy - exclude current skill level from path
  const formatSkillHierarchy = (parentTitles) => {
    if (!parentTitles || parentTitles.length === 0) {
      return null;
    }
    return parentTitles.join(' → ');
  };
  
  // Render skill item
  const renderSkillItem = (skill, index, isTopContributor = true) => (
    <div key={skill.skill_id} className={`skill-contribution-item ${!isTopContributor ? 'remaining-skill' : ''}`}>
      <div className="skill-contribution-header">
        <div className="skill-contribution-title-block">
          <div className="skill-contribution-title">
            <span className="skill-contribution-number">{index + 1}.</span>
            <strong>{skill.title}</strong>
          </div>
          {skill.parent_titles && skill.parent_titles.length > 0 && (
            <div className="skill-contribution-hierarchy">
              {formatSkillHierarchy(skill.parent_titles)}
            </div>
          )}
        </div>
        <div className="skill-contribution-points">
          +{skill.points_contributed} pts
        </div>
      </div>
      
      <div className="skill-contribution-details">
        <span className="skill-detail-badge level">
          {getLevelLabel(skill.level)}
        </span>
        <span className={`skill-detail-badge rating rating-${skill.rating}`}>
          {getRatingLabel(skill.rating)}
        </span>
        <span className="skill-detail-badge similarity">
          {(skill.similarity * 100).toFixed(0)}% match
        </span>
        <span className="skill-detail-badge percentage">
          {skill.percentage_of_total.toFixed(1)}% of total
        </span>
      </div>
    </div>
  );

  // Handle backdrop click
  const handleBackdropClick = (e) => {
    if (e.target.classList.contains('modal-backdrop')) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content score-breakdown-modal">
        {/* Header */}
        <div className="modal-header">
          <div>
            <h3>Score Breakdown</h3>
            <p className="modal-subtitle">{userName}</p>
          </div>
          <button className="modal-close-button" onClick={onClose} aria-label="Close modal">
            <FiX />
          </button>
        </div>

        {/* Overall Score */}
        <div className={`modal-score-summary ${getScoreColorClass(normalized_score)}`}>
          <div className="modal-score-value">
            {normalized_score.toFixed(1)}
          </div>
          <div className="modal-score-label">
            {score_interpretation}
          </div>
        </div>

        {/* Matched Skills Contributions */}
        <div className="modal-section">
          <h4>Skill Contributions</h4>
          <p className="modal-section-subtitle">
            All {total_matched_skills} matched skills shown below
          </p>
          
          <div className="skill-contributions-list">
            {/* Top 80% contributors */}
            {topSkills.map((skill, index) => renderSkillItem(skill, index, true))}
            
            {/* Remaining skills (expandable) */}
            {remainingSkills.length > 0 && (
              <>
                {showAllSkills && remainingSkills.map((skill, index) => 
                  renderSkillItem(skill, topSkills.length + index, false)
                )}
                
                <button 
                  className="expand-remaining-button"
                  onClick={() => setShowAllSkills(!showAllSkills)}
                >
                  {showAllSkills ? (
                    <>
                      <FiChevronUp /> Hide {remainingSkills.length} skills ({remainingPercentage.toFixed(1)}% of score)
                    </>
                  ) : (
                    <>
                      <FiChevronDown /> Show {remainingSkills.length} more skills ({remainingPercentage.toFixed(1)}% of score)
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>

        {/* Transfer Bonus Details */}
        {transfer_bonus_total > 0 && transfer_bonus_details.length > 0 && (
          <div className="modal-section transfer-bonus-section">
            <h4>Transfer Bonus</h4>
            <div className="transfer-bonus-summary">
              <span>+{transfer_bonus_total.toFixed(2)} points</span>
              <span className="transfer-bonus-description">
                Credit for related technology experience
              </span>
            </div>
            
            <div className="transfer-details-list">
              {transfer_bonus_details.map((detail, index) => (
                <div key={index} className="transfer-detail-item">
                  <div className="transfer-path">
                    <div className="transfer-source">
                      <span className="transfer-label">Your Experience:</span>
                      <span className="transfer-skill">{detail.source_parent_title}</span>
                      <span className="transfer-arrow">→</span>
                      <span className="transfer-tech">{detail.source_skill_title}</span>
                    </div>
                    <div className="transfer-matched">
                      <span className="transfer-label">Matched To:</span>
                      <span className="transfer-skill">{detail.matched_parent_title}</span>
                      <span className="transfer-arrow">→</span>
                      <span className="transfer-tech">{detail.matched_skill_title}</span>
                    </div>
                  </div>
                  <div className="transfer-bonus-amount">
                    +{(detail.bonus_amount * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer with close button */}
        <div className="modal-footer">
          <button className="modal-action-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default ScoreBreakdownModal;
