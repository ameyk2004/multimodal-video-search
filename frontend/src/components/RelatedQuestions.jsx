import React, { useState, useEffect } from 'react';
import './RelatedQuestions.css';

export default function RelatedQuestions({ metadata, onSearch, lang, customTitle, fallbackQueries }) {
  const [randomQueries, setRandomQueries] = useState([]);

  useEffect(() => {
    let queriesToUse = [];
    
    if (metadata && Object.keys(metadata).length > 0) {
      const videoIds = Object.keys(metadata);
      if (videoIds.length > 0) {
        const randomVid = videoIds[Math.floor(Math.random() * videoIds.length)];
        queriesToUse = metadata[randomVid]?.queries || [];
      }
    } else if (fallbackQueries && fallbackQueries.length > 0) {
      queriesToUse = fallbackQueries;
    }

    if (queriesToUse.length === 0) return;

    // Shuffle and pick up to 5
    const shuffled = [...queriesToUse].sort(() => 0.5 - Math.random());
    const selected = shuffled.slice(0, 5);

    setRandomQueries(selected);
  }, [metadata, fallbackQueries]);

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
        {randomQueries.map((q, idx) => (
          <button 
            key={idx} 
            className="rq-chip" 
            onClick={() => onSearch(q)}
            style={{ animationDelay: `${idx * 0.1}s` }}
          >
            <span className="rq-chip-glow"></span>
            <span className="rq-chip-text">{q}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
