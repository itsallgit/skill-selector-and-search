import React, { useState, useEffect } from 'react';

function SkillResults({ skills }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [skillsData, setSkillsData] = useState(null);
  const [levelFilters, setLevelFilters] = useState({
    1: true,
    2: true,
    3: true,
    4: true
  });
  const [levelMapping, setLevelMapping] = useState({
    1: 'Level 1 Capability',
    2: 'Level 2 Capability',
    3: 'Generic Skill',
    4: 'Technology'
  });
  const [expandedGroups, setExpandedGroups] = useState({
    'excellent': true,
    'very-good': true,
    'good': true,
    'fair': true,
    'moderate': true,
    'low': true
  });

  // Build a flat lookup map of skill ID to skill object
  const buildSkillsLookup = (skillsArray, lookup = {}, ancestors = []) => {
    if (!Array.isArray(skillsArray)) {
      console.error('buildSkillsLookup expects an array, got:', typeof skillsArray);
      return lookup;
    }
    skillsArray.forEach(skill => {
      lookup[skill.id] = {
        ...skill,
        ancestors: [...ancestors]
      };
      if (skill.skills && skill.skills.length > 0) {
        buildSkillsLookup(skill.skills, lookup, [...ancestors, { id: skill.id, title: skill.title }]);
      }
    });
    return lookup;
  };

  // Fetch skills master data and level mapping on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch skills master - try relative path first
        const skillsResponse = await fetch('/data/skills-master.json');
        if (!skillsResponse.ok) {
          throw new Error(`Failed to fetch skills-master.json: ${skillsResponse.status}`);
        }
        const skillsJson = await skillsResponse.json();
        console.log('Fetched skills data:', Array.isArray(skillsJson) ? 'Array' : typeof skillsJson);
        setSkillsData(buildSkillsLookup(skillsJson));

        // Fetch level mapping
        const levelResponse = await fetch('/data/skill-levels-mapping.json');
        if (!levelResponse.ok) {
          throw new Error(`Failed to fetch skill-levels-mapping.json: ${levelResponse.status}`);
        }
        const levelJson = await levelResponse.json();
        const mapping = {};
        levelJson.skillNames.forEach(item => {
          mapping[item.level] = item.name;
        });
        setLevelMapping(mapping);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };
    fetchData();
  }, []);

  if (!skills || skills.length === 0) {
    return null;
  }

  // Get match color based on similarity - green to grey gradient
  const getMatchColor = (similarity) => {
    if (similarity >= 0.85) return 'dark-green';
    if (similarity >= 0.75) return 'green';
    if (similarity >= 0.65) return 'light-green';
    if (similarity >= 0.55) return 'yellow';
    if (similarity >= 0.45) return 'orange';
    return 'gray';
  };

  const getMatchColorClass = (similarity) => {
    const color = getMatchColor(similarity);
    return `match-color-${color}`;
  };

  // Get ancestor titles from IDs
  const getAncestorTitles = (ancestorIds) => {
    if (!skillsData || !ancestorIds || ancestorIds.length === 0) {
      return [];
    }
    return ancestorIds
      .map(id => skillsData[id]?.title)
      .filter(title => title !== undefined);
  };

  // Toggle level filter
  const toggleLevelFilter = (level) => {
    setLevelFilters(prev => ({
      ...prev,
      [level]: !prev[level]
    }));
  };

  // Toggle quality group
  const toggleGroup = (groupKey) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupKey]: !prev[groupKey]
    }));
  };

  // Get quality group info
  const getQualityGroup = (similarity) => {
    if (similarity >= 0.85) return { key: 'excellent', label: 'Excellent', range: '85-100%' };
    if (similarity >= 0.75) return { key: 'very-good', label: 'Very Good', range: '75-84%' };
    if (similarity >= 0.65) return { key: 'good', label: 'Good', range: '65-74%' };
    if (similarity >= 0.55) return { key: 'fair', label: 'Fair', range: '55-64%' };
    if (similarity >= 0.45) return { key: 'moderate', label: 'Moderate', range: '45-54%' };
    return { key: 'low', label: 'Low', range: '<45%' };
  };

  // Filter skills by selected levels
  const filteredSkills = skills.filter(skill => levelFilters[skill.level]);

  // Group filtered skills by quality
  const qualityGroups = {
    'excellent': { label: 'Excellent', range: '85-100%', skills: [] },
    'very-good': { label: 'Very Good', range: '75-84%', skills: [] },
    'good': { label: 'Good', range: '65-74%', skills: [] },
    'fair': { label: 'Fair', range: '55-64%', skills: [] },
    'moderate': { label: 'Moderate', range: '45-54%', skills: [] },
    'low': { label: 'Low', range: '<45%', skills: [] }
  };

  filteredSkills.forEach(skill => {
    const group = getQualityGroup(skill.similarity);
    qualityGroups[group.key].skills.push(skill);
  });

  return (
    <section className="matched-skills-section">
      <div className="section-header-row">
        <div className="section-header-main">
          <h2>Matched Skills ({filteredSkills.length})</h2>
          <button 
            className="collapse-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? "Collapse matched skills" : "Expand matched skills"}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>
      </div>
      <p className="section-summary"></p>

      {isExpanded && (
        <>
          {/* Legend */}
          <div className="similarity-legend">
            <span className="legend-label">Match Quality:</span>
            <div className="legend-items">
              <div className="legend-item">
                <span className="legend-dot match-color-dark-green"></span>
                <span className="legend-text">Excellent (85-100%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot match-color-green"></span>
                <span className="legend-text">Very Good (75-84%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot match-color-light-green"></span>
                <span className="legend-text">Good (65-74%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot match-color-yellow"></span>
                <span className="legend-text">Fair (55-64%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot match-color-orange"></span>
                <span className="legend-text">Moderate (45-54%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-dot match-color-gray"></span>
                <span className="legend-text">Low (&lt;45%)</span>
              </div>
            </div>
          </div>

          {/* Level Filters - Pill Style */}
          <div className="level-filters">
            <span className="filters-label">Filter by Level:</span>
            <div className="filter-pills">
              {[1, 2, 3, 4].map(level => (
                <button
                  key={level}
                  className={`filter-pill ${levelFilters[level] ? 'active' : ''}`}
                  onClick={() => toggleLevelFilter(level)}
                >
                  <span>{levelMapping[level]}</span>
                  {levelFilters[level] && <span className="pill-cross">×</span>}
                </button>
              ))}
            </div>
          </div>

          {/* Quality Groups */}
          {Object.entries(qualityGroups).map(([groupKey, groupData]) => {
            const isExpanded = expandedGroups[groupKey];
            const hasSkills = groupData.skills.length > 0;
            
            return (
              <div key={groupKey} className="quality-group">
                <div 
                  className={`quality-group-header ${!hasSkills ? 'non-expandable' : ''}`}
                  onClick={hasSkills ? () => toggleGroup(groupKey) : undefined}
                  style={hasSkills ? { cursor: 'pointer' } : { cursor: 'default' }}
                >
                  <div className="quality-group-left">
                    <span className={`quality-group-dot ${getMatchColorClass(groupKey === 'excellent' ? 0.9 : groupKey === 'very-good' ? 0.8 : groupKey === 'good' ? 0.7 : groupKey === 'fair' ? 0.6 : groupKey === 'moderate' ? 0.5 : 0.4)}`}></span>
                    <span className="quality-group-label">{groupData.label}</span>
                    <span className="quality-group-range">({groupData.range})</span>
                  </div>
                  <div className="quality-group-right">
                    <span className={`quality-group-count ${hasSkills ? '' : 'empty'}`}>
                      {groupData.skills.length} skills
                    </span>
                  </div>
                </div>
                
                {isExpanded && hasSkills && (
                  <div className="quality-group-content">
                    <div className="skills-list">
                      {groupData.skills.map((skill, index) => {
                        const ancestorTitles = getAncestorTitles(skill.parent_titles);
                        return (
                          <div key={index} className={`skill-list-item ${getMatchColorClass(skill.similarity)}`}>
                            <div className="skill-list-main">
                              <h3 className="skill-title-prominent">{skill.title}</h3>
                              <div className="skill-list-meta-row">
                                {ancestorTitles.length > 0 && (
                                  <div className="skill-breadcrumbs">
                                    {ancestorTitles.map((title, idx) => (
                                      <React.Fragment key={idx}>
                                        {idx > 0 && <span className="breadcrumb-separator">›</span>}
                                        <span className="breadcrumb-item">{title}</span>
                                      </React.Fragment>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="skill-list-metrics">
                              <div className="skill-list-metrics-row">
                                <div className={`match-indicator ${getMatchColorClass(skill.similarity)}`}>
                                  <span className="match-dot"></span>
                                </div>
                                <span className="skill-list-similarity">
                                  {(skill.similarity * 100).toFixed(0)}%
                                </span>
                              </div>
                              <span className={`skill-level-badge level-${skill.level}`}>
                                {levelMapping[skill.level]}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </>
      )}
    </section>
  );
}

export default SkillResults;
