import React, { useState } from 'react';
import { FiChevronDown, FiChevronUp } from 'react-icons/fi';

/**
 * ScoringExplanation - Expandable accordion explaining the scoring algorithm
 * 
 * Features:
 * - Collapsed by default with clear expand indicator
 * - Visual formula presentation
 * - Score interpretation guide (ranges + distribution + guidance)
 * - Non-interactive visual elements
 * - Professional, digestible content
 */
function ScoringExplanation() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="scoring-explanation">
      <button
        className="scoring-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <h3>How is scoring calculated?</h3>
        {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
      </button>

      {isExpanded && (
        <div className="scoring-content">
          {/* Formula Overview */}
          <div className="scoring-section">
            <h4>Scoring Formula</h4>
            <div className="formula-box">
              <p className="formula-text">
                <strong>Skill Score</strong> = Similarity × Level Weight × Proficiency Multiplier
              </p>
              <p className="formula-text">
                <strong>User Total</strong> = Σ(All Skill Scores) + Transfer Bonus
              </p>
              <p className="formula-text">
                <strong>Final Score</strong> = (User Total ÷ Max Possible) × 100
              </p>
            </div>
          </div>

          {/* Skill Level Weights */}
          <div className="scoring-section">
            <h4>Skill Level Weights</h4>
            <p className="scoring-description">
              Different skill hierarchy levels contribute different amounts to the overall score:
            </p>
            <div className="weight-bars">
              <div className="weight-bar-item">
                <span className="weight-label">L3 Generic Skills</span>
                <div className="weight-bar-container">
                  <div className="weight-bar" style={{ width: '50%' }}></div>
                  <span className="weight-value">50%</span>
                </div>
              </div>
              <div className="weight-bar-item">
                <span className="weight-label">L4 Technologies</span>
                <div className="weight-bar-container">
                  <div className="weight-bar" style={{ width: '30%' }}></div>
                  <span className="weight-value">30%</span>
                </div>
              </div>
              <div className="weight-bar-item">
                <span className="weight-label">L2 Sub-categories</span>
                <div className="weight-bar-container">
                  <div className="weight-bar" style={{ width: '20%' }}></div>
                  <span className="weight-value">20%</span>
                </div>
              </div>
              <div className="weight-bar-item">
                <span className="weight-label">L1 Categories</span>
                <div className="weight-bar-container">
                  <div className="weight-bar" style={{ width: '10%' }}></div>
                  <span className="weight-value">10%</span>
                </div>
              </div>
            </div>
            <p className="scoring-note">
              Generic skills (L3) are weighted highest as they represent core competencies.
            </p>
          </div>

          {/* User Proficiency Multipliers */}
          <div className="scoring-section">
            <h4>User Proficiency Multipliers</h4>
            <p className="scoring-description">
              User self-assessed proficiency exponentially increases score contribution:
            </p>
            <div className="multiplier-grid">
              <div className="multiplier-card">
                <div className="multiplier-badge beginner">1</div>
                <p className="multiplier-label">Beginner</p>
                <p className="multiplier-value">×1.0</p>
              </div>
              <div className="multiplier-card">
                <div className="multiplier-badge intermediate">2</div>
                <p className="multiplier-label">Intermediate</p>
                <p className="multiplier-value">×2.0</p>
              </div>
              <div className="multiplier-card">
                <div className="multiplier-badge advanced">3</div>
                <p className="multiplier-label">Advanced</p>
                <p className="multiplier-value">×4.0</p>
              </div>
            </div>
            <p className="scoring-note">
              Advanced proficiency in core skills significantly boosts rankings.
            </p>
          </div>

          {/* Transfer Bonus */}
          <div className="scoring-section">
            <h4>Transfer Bonus (up to 15%)</h4>
            <p className="scoring-description">
              Users receive partial credit for relevant technology experience in different contexts.
            </p>
            <div className="transfer-example">
              <p className="transfer-scenario">
                <strong>Example:</strong> Query matches "Serverless Architecture → AWS"
              </p>
              <p className="transfer-scenario">
                User has "Cloud Security → AWS" ✓ Receives transfer bonus
              </p>
            </div>
            <p className="scoring-note">
              This recognizes transferable technology competence across different domains.
            </p>
          </div>

          {/* Score Interpretation Guide */}
          <div className="scoring-section score-interpretation">
            <h4>Understanding Scores</h4>
            <div className="score-ranges">
              <div className="score-range excellent">
                <div className="score-range-badge">80-100</div>
                <div className="score-range-info">
                  <p className="score-range-label">Excellent Match</p>
                  <p className="score-range-description">Strong alignment with query requirements</p>
                </div>
              </div>
              <div className="score-range strong">
                <div className="score-range-badge">60-79</div>
                <div className="score-range-info">
                  <p className="score-range-label">Strong Match</p>
                  <p className="score-range-description">Good alignment with most requirements</p>
                </div>
              </div>
              <div className="score-range good">
                <div className="score-range-badge">40-59</div>
                <div className="score-range-info">
                  <p className="score-range-label">Good Match</p>
                  <p className="score-range-description">Solid foundation with some gaps</p>
                </div>
              </div>
              <div className="score-range fair">
                <div className="score-range-badge">20-39</div>
                <div className="score-range-info">
                  <p className="score-range-label">Fair Match</p>
                  <p className="score-range-description">Some relevant skills, needs development</p>
                </div>
              </div>
              <div className="score-range low">
                <div className="score-range-badge">0-19</div>
                <div className="score-range-info">
                  <p className="score-range-label">Weak Match</p>
                  <p className="score-range-description">Limited alignment with requirements</p>
                </div>
              </div>
            </div>
            
            <div className="score-guidance">
              <p><strong>Typical Distribution:</strong> Most queries produce scores between 20-80</p>
              <p><strong>Recommendation:</strong> Scores above 60 indicate strong candidates for the role</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScoringExplanation;
