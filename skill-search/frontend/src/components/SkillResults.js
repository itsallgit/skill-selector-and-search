import React from 'react';

function SkillResults({ skills }) {
  if (!skills || skills.length === 0) {
    return null;
  }
  
  const getLevelLabel = (level) => {
    const labels = {
      1: 'Category',
      2: 'Sub-category',
      3: 'Skill',
      4: 'Technology'
    };
    return labels[level] || 'Unknown';
  };
  
  return (
    <section className="section">
      <h2>Matched Skills ({skills.length})</h2>
      <div className="skills-grid">
        {skills.map((skill, index) => (
          <div key={index} className="skill-card">
            <div className="skill-header">
              <span className="skill-title">{skill.title}</span>
              <span className="skill-emoji">{skill.color}</span>
            </div>
            <div className="skill-meta">
              <span className="skill-level">L{skill.level} - {getLevelLabel(skill.level)}</span>
              <span className="skill-similarity">
                {(skill.similarity * 100).toFixed(0)}% match
              </span>
            </div>
            {skill.parent_titles && skill.parent_titles.length > 0 && (
              <div className="skill-path">
                {skill.parent_titles.join(' > ')}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

export default SkillResults;
