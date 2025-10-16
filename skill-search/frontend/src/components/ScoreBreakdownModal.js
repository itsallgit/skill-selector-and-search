import React from 'react';
import { FiX, FiChevronDown, FiChevronUp } from 'react-icons/fi';

/**
 * ScoreBreakdownModal - Modal showing detailed score breakdown for individual user
 * 
 * Features:
 * - Shows Coverage and Expertise as primary dimensions
 * - Displays ALL matched skills with contribution details
 * - Shows raw score and display score
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
    coverage_score,
    coverage_percentage,
    expertise_multiplier,
    expertise_label,
    raw_score,
    display_score,
    skill_contributions,
    total_matched_skills
  } = scoreBreakdown;
  
  // Split skills: top 5 always visible, rest expandable
  const topSkills = skill_contributions?.slice(0, 5) || [];
  const remainingSkills = skill_contributions?.slice(5) || [];

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
  
  //Get expertise color class
  const getExpertiseColorClass = (expertiseLabel) => {
    const labelMap = {
      'Expert': 'expertise-expert',
      'Advanced': 'expertise-advanced',
      'Intermediate': 'expertise-intermediate',
      'Early Career': 'expertise-early',
      'Beginner': 'expertise-beginner'
    };
    return labelMap[expertiseLabel] || 'expertise-beginner';
  };
  
  // Get score color class
  const getScoreColorClass = (score) => {
    if (!score) return 'score-low';
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
          {skill.coverage_percentage?.toFixed(1) || '0.0'}% coverage
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
        <span className="skill-detail-badge rating-multiplier">
          {skill.rating_multiplier?.toFixed(1) || '1.0'}× multiplier
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

        {/* Two-Dimensional Score Summary */}
        <div className={`modal-score-summary ${getScoreColorClass(display_score || 0)}`}>
          <div className="score-dimensions-modal">
            <div className="dimension-item-modal">
              <span className="dimension-label-modal">Coverage</span>
              <span className="dimension-value-modal">{coverage_percentage?.toFixed(1) || '0.0'}%</span>
              <span className="dimension-detail-modal">Breadth of relevant skills</span>
            </div>
            <div className={`dimension-item-modal ${getExpertiseColorClass(expertise_label)}`}>
              <span className="dimension-label-modal">Expertise</span>
              <span className="dimension-value-modal">{expertise_label || 'Unknown'}</span>
              <span className="dimension-detail-modal">{expertise_multiplier?.toFixed(2) || '1.00'}× multiplier</span>
            </div>
          </div>
          <div className="score-display-modal-secondary">
            <div className="score-item-modal">
              <span className="score-label-modal">Raw Score</span>
              <span className="score-value-modal">{raw_score?.toFixed(4) || '0.0000'}</span>
            </div>
            <div className="score-item-modal">
              <span className="score-label-modal">Display Score</span>
              <span className="score-value-modal">{display_score?.toFixed(1) || '0.0'}/100</span>
            </div>
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
                      <FiChevronUp /> Hide {remainingSkills.length} skills
                    </>
                  ) : (
                    <>
                      <FiChevronDown /> Show {remainingSkills.length} more skills
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>

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
