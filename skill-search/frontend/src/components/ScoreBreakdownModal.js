import React from 'react';
import { FiX } from 'react-icons/fi';

/**
 * ScoreBreakdownModal - Modal showing detailed score breakdown for individual user
 * 
 * Features:
 * - Shows top skills representing 80% of total score
 * - Displays point contribution per skill
 * - Detailed transfer bonus with source → matched skill relationships
 * - Clean, professional modal design
 * - Close on backdrop click or X button
 * 
 * Props:
 * - isOpen: boolean
 * - onClose: () => void callback
 * - userName: string
 * - scoreBreakdown: object from API (score_breakdown field)
 */
function ScoreBreakdownModal({ isOpen, onClose, userName, scoreBreakdown }) {
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
        <div className="modal-score-summary">
          <div className="modal-score-value">
            {normalized_score.toFixed(1)}
          </div>
          <div className="modal-score-label">
            {score_interpretation}
          </div>
        </div>

        {/* Matched Skills Contributions */}
        <div className="modal-section">
          <h4>Top Contributing Skills</h4>
          <p className="modal-section-subtitle">
            Showing top contributors (representing ~80% of score from {total_matched_skills} matched skills)
          </p>
          
          <div className="skill-contributions-list">
            {skill_contributions.map((skill, index) => (
              <div key={skill.skill_id} className="skill-contribution-item">
                <div className="skill-contribution-header">
                  <div className="skill-contribution-title">
                    <span className="skill-contribution-number">{index + 1}.</span>
                    <strong>{skill.title}</strong>
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
            ))}
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
