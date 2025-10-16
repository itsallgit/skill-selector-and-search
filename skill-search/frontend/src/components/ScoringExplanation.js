import React, { useState } from 'react';
import { FiBarChart2, FiAward } from 'react-icons/fi';

/**
 * ScoringExplanation - Expandable accordion explaining the two-dimensional scoring algorithm
 * 
 * Features:
 * - Expanded by default to show scoring details immediately
 * - Two-dimensional approach: Coverage × Expertise
 * - Clear formula presentation with examples
 * - Score interpretation guide
 * - Professional, digestible content with no legacy algorithm references
 */
function ScoringExplanation() {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="scoring-explanation">
      <button
        className="scoring-toggle-no-arrow"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <h3>How is scoring calculated?</h3>
      </button>

      {isExpanded && (
        <div className="scoring-content">
          {/* Overview */}
          <div className="scoring-section">
            <h4>Two-Dimensional Scoring Algorithm</h4>
            <p className="scoring-description">
              Users are evaluated across two key dimensions that together determine their ranking:
            </p>
            <div className="dimensions-overview">
              <div className="dimension-card">
                <div className="dimension-icon-line"><FiBarChart2 /></div>
                <h5>Coverage (Breadth)</h5>
                <p>How many relevant skills the user possesses</p>
              </div>
              <div className="dimension-card">
                <div className="dimension-icon-line"><FiAward /></div>
                <h5>Expertise (Depth)</h5>
                <p>The proficiency level across matched skills</p>
              </div>
            </div>
          </div>

          {/* Coverage Dimension */}
          <div className="scoring-section">
            <h4>Coverage: Measuring Skill Breadth</h4>
            <p className="scoring-description">
              Coverage measures how well a user's skills align with the query. Each matched skill contributes based on its semantic similarity.
            </p>
            <div className="formula-box">
              <p className="formula-text">
                <strong>Coverage</strong> = Σ(similarity²) for all matched skills
              </p>
            </div>
            <p className="scoring-note">
              <strong>Why square the similarity?</strong> This emphasizes stronger matches while still giving credit to weaker ones.
            </p>
            <div className="coverage-example">
              <p className="example-title"><strong>Example:</strong> Query: "AWS Lambda and serverless"</p>
              <ul className="example-list">
                <li>AWS Lambda (similarity: 0.95) → contributes <strong>0.90</strong></li>
                <li>Serverless Architecture (similarity: 0.88) → contributes <strong>0.77</strong></li>
                <li>API Gateway (similarity: 0.75) → contributes <strong>0.56</strong></li>
              </ul>
              <p className="example-result">Total Coverage = <strong>2.23</strong></p>
              <p className="example-note">Displayed as percentage relative to maximum possible coverage</p>
            </div>
          </div>

          {/* Expertise Dimension */}
          <div className="scoring-section">
            <h4>Expertise: Measuring Proficiency Depth</h4>
            <p className="scoring-description">
              Expertise is the weighted average proficiency level across matched skills. Higher proficiency levels receive exponentially greater weight.
            </p>
            <div className="formula-box">
              <p className="formula-text">
                <strong>Expertise</strong> = Σ(similarity² × rating_multiplier) ÷ Σ(similarity²)
              </p>
            </div>
            
            <div className="multiplier-grid">
              <div className="multiplier-card">
                <div className="multiplier-badge beginner">1</div>
                <p className="multiplier-label">Beginner</p>
                <p className="multiplier-value">×1.0</p>
              </div>
              <div className="multiplier-card">
                <div className="multiplier-badge intermediate">2</div>
                <p className="multiplier-label">Intermediate</p>
                <p className="multiplier-value">×3.0</p>
              </div>
              <div className="multiplier-card">
                <div className="multiplier-badge advanced">3</div>
                <p className="multiplier-label">Advanced</p>
                <p className="multiplier-value">×6.0</p>
              </div>
            </div>
            
            <p className="scoring-note">
              <strong>Why exponential?</strong> Advanced proficiency represents significantly more value than intermediate knowledge.
            </p>
            
            <div className="expertise-example">
              <p className="example-title"><strong>Example:</strong> Using the same 3 matched skills</p>
              <ul className="example-list">
                <li>AWS Lambda (0.90 × <strong>6.0</strong> for Advanced) = 5.40</li>
                <li>Serverless Architecture (0.77 × <strong>3.0</strong> for Intermediate) = 2.31</li>
                <li>API Gateway (0.56 × <strong>6.0</strong> for Advanced) = 3.36</li>
              </ul>
              <p className="example-result">Expertise = (5.40 + 2.31 + 3.36) ÷ 2.23 = <strong>4.96</strong></p>
              <p className="example-note">Displayed as label: <strong>Advanced</strong></p>
            </div>

            <div className="expertise-labels">
              <h5>Expertise Labels</h5>
              <div className="label-grid">
                <div className="label-item expert"><span className="label-badge">5.0+</span> Expert</div>
                <div className="label-item advanced"><span className="label-badge">3.5-4.9</span> Advanced</div>
                <div className="label-item intermediate"><span className="label-badge">2.0-3.4</span> Intermediate</div>
                <div className="label-item early"><span className="label-badge">1.3-1.9</span> Early Career</div>
                <div className="label-item beginner"><span className="label-badge">&lt;1.3</span> Beginner</div>
              </div>
            </div>
          </div>

          {/* Final Ranking */}
          <div className="scoring-section">
            <h4>Final Ranking Formula</h4>
            <div className="formula-box">
              <p className="formula-text">
                <strong>Raw Score</strong> = Coverage × Expertise
              </p>
              <p className="formula-text">
                <strong>Display Score</strong> = (Raw Score ÷ Top User Raw Score) × 100
              </p>
            </div>
            <p className="scoring-description">
              The raw score is used to rank all users. The display score (0-100) shows each user's performance relative to the top-ranked user, who always scores 100.
            </p>
            <div className="ranking-example">
              <p className="example-title"><strong>Complete Example:</strong></p>
              <p className="example-calc">Coverage = 2.23 × Expertise = 4.96 = <strong>Raw Score: 11.1</strong></p>
              <p className="example-calc">If this is the top user → <strong>Display Score: 100</strong></p>
              <p className="example-calc">If top user has 13.3 → (11.1 ÷ 13.3) × 100 = <strong>Display Score: 83.5</strong></p>
            </div>
          </div>

          {/* Why This Approach? */}
          <div className="scoring-section">
            <h4>Why Two Dimensions?</h4>
            <div className="rationale-grid">
              <div className="rationale-card">
                <h5>Balances Breadth and Depth</h5>
                <p>A user with deep expertise in fewer skills can rank higher than a user with shallow knowledge in many skills.</p>
              </div>
              <div className="rationale-card">
                <h5>Semantic Understanding</h5>
                <p>Vector similarity ensures the algorithm understands meaning, not just keyword matches.</p>
              </div>
              <div className="rationale-card">
                <h5>Proficiency Matters</h5>
                <p>Advanced users in highly relevant skills are prioritized over beginners with tangentially related skills.</p>
              </div>
            </div>
          </div>

          {/* Score Interpretation Guide */}
          <div className="scoring-section score-interpretation">
            <h4>Understanding Display Scores</h4>
            <div className="score-ranges">
              <div className="score-range excellent">
                <div className="score-range-badge">80-100</div>
                <div className="score-range-info">
                  <p className="score-range-label">Excellent Match</p>
                  <p className="score-range-description">Strong coverage and expertise alignment</p>
                </div>
              </div>
              <div className="score-range strong">
                <div className="score-range-badge">60-79</div>
                <div className="score-range-info">
                  <p className="score-range-label">Strong Match</p>
                  <p className="score-range-description">Good coverage or high expertise</p>
                </div>
              </div>
              <div className="score-range good">
                <div className="score-range-badge">40-59</div>
                <div className="score-range-info">
                  <p className="score-range-label">Good Match</p>
                  <p className="score-range-description">Solid foundation with room to grow</p>
                </div>
              </div>
              <div className="score-range fair">
                <div className="score-range-badge">20-39</div>
                <div className="score-range-info">
                  <p className="score-range-label">Fair Match</p>
                  <p className="score-range-description">Some relevant skills, limited depth</p>
                </div>
              </div>
              <div className="score-range low">
                <div className="score-range-badge">0-19</div>
                <div className="score-range-info">
                  <p className="score-range-label">Weak Match</p>
                  <p className="score-range-description">Limited alignment with query</p>
                </div>
              </div>
            </div>
            
            <div className="score-guidance">
              <p><strong>Remember:</strong> Display scores are relative to the top-ranked user for each query</p>
              <p><strong>Recommendation:</strong> Focus on both Coverage and Expertise dimensions for a complete picture</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScoringExplanation;
