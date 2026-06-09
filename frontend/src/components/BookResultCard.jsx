import { useState } from 'react';
import { api } from '../utils/api';

export default function BookResultCard({ result, isMarathi, style }) {
  const [paragraphs, setParagraphs] = useState([result.marathi_raw]);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(result.chunk_index);
  const [loadingNext, setLoadingNext] = useState(false);
  const [noMoreContent, setNoMoreContent] = useState(false);

  const lang = isMarathi ? 'mr' : 'en';
  const pct = Math.round((result.score || 0) * 100);

  const cleanText = (text) => {
    // Strip the "पुस्तक: ... विषय: ... भाग/लेख: ..." prefix if it exists
    // The prefix is usually separated by a double newline, but we'll use a regex to be safe
    const cleaned = text.replace(/^पुस्तक:[\s\S]*?भाग\/लेख:.*?\n+/s, '').trim();
    return cleaned || text; // Fallback if regex doesn't match perfectly
  };

  const handleReadMore = async () => {
    if (currentChunkIndex === undefined || currentChunkIndex === null) {
      alert("This chunk does not have an index (might be an older upload).");
      return;
    }
    setLoadingNext(true);
    try {
      const nextIdx = currentChunkIndex + 1;
      const data = await api.getNextChunk(result.book_name, nextIdx);
      if (data && data.marathi_raw) {
        setParagraphs(prev => [...prev, data.marathi_raw]);
        setCurrentChunkIndex(nextIdx);
      } else {
        setNoMoreContent(true);
      }
    } catch (e) {
      console.error(e);
      console.error(e);
      if (e.message.includes("Chunk not found")) {
        setNoMoreContent(true);
      } else {
        alert(`Failed to load next paragraph: ${e.message}`);
      }
    } finally {
      setLoadingNext(false);
    }
  };

  return (
    <div className="result-card book-card" style={style}>
      <div className="book-card-inner">
        {/* Left Side: Cinematic Book Cover */}
        <div className="book-cover-section">
          <div 
            className="book-cover-blur-bg" 
            style={{ backgroundImage: `url(/books/${result.book_name}.jpg)` }}
          />
          <img 
            src={`/books/${result.book_name}.jpg`} 
            alt={result.book_name}
            className="book-cover-img"
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.previousElementSibling.style.display = 'none'; // hide blur
              e.target.nextElementSibling.style.display = 'flex'; // show fallback
            }}
          />
          <div className="book-cover-fallback" style={{display: 'none'}}>
            <span className="book-icon">📚</span>
            <span className="fallback-title">{result.book_name}</span>
          </div>
        </div>

        {/* Right Side: Content */}
        <div className="book-content-section">
          <div className="card-header">
            <div className="relevance-group">
              <span className="relevance-badge">
                <span className="sparkle">✧</span> {isMarathi ? `सुसंगतता: ${pct}%` : `Relevance: ${pct}%`}
              </span>
              <span className="book-name-badge highlight-book">
                {result.book_name} {lang === 'mr' ? `(पान ${result.page_number})` : `(Page ${result.page_number})`}
              </span>
            </div>
          </div>

          <div className="book-text-flow">
            {paragraphs.map((p, idx) => (
              <p key={idx} className="marathi-text book-paragraph">
                {cleanText(p)}
              </p>
            ))}
          </div>

          {!noMoreContent && (
            <button 
              className="read-more-book-btn" 
              onClick={handleReadMore}
              disabled={loadingNext}
            >
              {loadingNext 
                ? (isMarathi ? 'लोड होत आहे...' : 'Loading...') 
                : (isMarathi ? 'पुढील परिच्छेद वाचा ➔' : 'Read Next Paragraph ➔')}
            </button>
          )}
          {noMoreContent && (
            <div className="end-of-book">
              {isMarathi ? '— पाठाचा शेवट —' : '— End of passage —'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
