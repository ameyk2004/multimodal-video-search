import React, { useState, useEffect } from 'react';
import './RelatedQuestions.css';

export default function RelatedQuestions({ relatedQueries, onSearch, lang, customTitle, fallbackQueries }) {
  const [randomQueries, setRandomQueries] = useState([]);

  useEffect(() => {
    let queriesToUse = [];
    
    if (relatedQueries && relatedQueries.length > 0) {
      // Normalize relatedQueries to objects if they are strings (legacy support)
      queriesToUse = relatedQueries.map(q => typeof q === 'string' ? { query: q, type: 'direct' } : q);
      // We don't need to shuffle if it's the structured mix from backend
      setRandomQueries(queriesToUse.slice(0, 5));
    } else if (fallbackQueries && fallbackQueries.length > 0) {
      queriesToUse = fallbackQueries.map(q => ({ query: q, type: 'direct' }));
      // Shuffle fallback queries and pick 5
      const shuffled = [...queriesToUse].sort(() => 0.5 - Math.random());
      setRandomQueries(shuffled.slice(0, 5));
    } else {
      setRandomQueries([]);
    }
  }, [relatedQueries, fallbackQueries]);

  if (randomQueries.length === 0) return null;

  return (
    <div className="related-questions-container">
      <div className="rq-header">
        <div className="rq-lottie-mock">
          <div className="rq-radar-ring"></div>
          <div className="rq-radar-core"></div>
        </div>
        <h3>{customTitle ? customTitle : (lang === 'mr' ? 'अधिक प्रश्न विचारा' : 'Ask More Questions')}</h3>
      </div>
      <div className="rq-chips-wrapper">
        {randomQueries.map((item, idx) => (
          <button 
            key={idx} 
            className={`rq-chip rq-chip-${item.type}`} 
            onClick={() => onSearch(item.query)}
            style={{ animationDelay: `${idx * 0.1}s` }}
          >
            <span className="rq-chip-glow"></span>
            {item.type === 'wildcard' && <span className="rq-chip-icon">✨ </span>}
            {item.type === 'tangential' && <span className="rq-chip-icon">🌿 </span>}
            <span className="rq-chip-text">{item.query}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
