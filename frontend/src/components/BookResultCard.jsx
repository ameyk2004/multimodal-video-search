import { useState } from 'react';
import { api } from '../utils/api';

export default function BookResultCard({ result, isMarathi, style }) {
  const [paragraphs, setParagraphs] = useState([result.marathi_raw]);
  const [topChunkIndex, setTopChunkIndex] = useState(result.chunk_index);
  const [bottomChunkIndex, setBottomChunkIndex] = useState(result.chunk_index);
  const [loadingNext, setLoadingNext] = useState(false);
  const [loadingPrev, setLoadingPrev] = useState(false);
  const [noMoreBottom, setNoMoreBottom] = useState(false);
  const [noMoreTop, setNoMoreTop] = useState(false);

  const lang = isMarathi ? 'mr' : 'en';
  const pct = Math.round((result.score || 0) * 100);

  const cleanText = (text) => {
    // Strip the "पुस्तक: ... विषय: ... भाग/लेख: ..." prefix if it exists
    // The prefix is usually separated by a double newline, but we'll use a regex to be safe
    const cleaned = text.replace(/^पुस्तक:[\s\S]*?भाग\/लेख:.*?\n+/s, '').trim();
    return cleaned || text; // Fallback if regex doesn't match perfectly
  };

  const handleReadMore = async () => {
    if (bottomChunkIndex === undefined || bottomChunkIndex === null) {
      alert("This chunk does not have an index (might be an older upload).");
      return;
    }
    setLoadingNext(true);
    try {
      const nextIdx = bottomChunkIndex + 1;
      const data = await api.getNextChunk(result.book_name, nextIdx);
      if (data && data.marathi_raw) {
        setParagraphs(prev => [...prev, data.marathi_raw]);
        setBottomChunkIndex(nextIdx);
      } else {
        setNoMoreBottom(true);
      }
    } catch (e) {
      console.error(e);
      if (e.message.includes("Chunk not found")) {
        setNoMoreBottom(true);
      } else {
        alert(`Failed to load next paragraph: ${e.message}`);
      }
    } finally {
      setLoadingNext(false);
    }
  };

  const handleReadPrevious = async () => {
    if (topChunkIndex === undefined || topChunkIndex === null) {
      alert("This chunk does not have an index (might be an older upload).");
      return;
    }
    if (topChunkIndex <= 0) {
      setNoMoreTop(true);
      return;
    }
    setLoadingPrev(true);
    try {
      const prevIdx = topChunkIndex - 1;
      const data = await api.getNextChunk(result.book_name, prevIdx);
      if (data && data.marathi_raw) {
        setParagraphs(prev => [data.marathi_raw, ...prev]);
        setTopChunkIndex(prevIdx);
      } else {
        setNoMoreTop(true);
      }
    } catch (e) {
      console.error(e);
      if (e.message.includes("Chunk not found")) {
        setNoMoreTop(true);
      } else {
        alert(`Failed to load previous paragraph: ${e.message}`);
      }
    } finally {
      setLoadingPrev(false);
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

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-start', marginTop: '16px', flexWrap: 'wrap' }}>
              {!noMoreTop && topChunkIndex > 0 && (
                <button 
                  className="read-more-book-btn" 
                  onClick={handleReadPrevious}
                  disabled={loadingPrev}
                  style={{ fontSize: '0.85rem', padding: '6px 16px' }}
                >
                  {loadingPrev 
                    ? (isMarathi ? 'लोड होत आहे...' : 'Loading...') 
                    : (isMarathi ? '↑ मागील परिच्छेद' : '↑ Read Previous')}
                </button>
              )}

              {!noMoreBottom && (
                <button 
                  className="read-more-book-btn" 
                  onClick={handleReadMore}
                  disabled={loadingNext}
                  style={{ fontSize: '0.85rem', padding: '6px 16px' }}
                >
                  {loadingNext 
                    ? (isMarathi ? 'लोड होत आहे...' : 'Loading...') 
                    : (isMarathi ? 'पुढील परिच्छेद ↓' : 'Read Next ↓')}
                </button>
              )}
            </div>
            
            {noMoreBottom && (
              <div className="end-of-book" style={{ marginTop: '16px' }}>
                {isMarathi ? '— पाठाचा शेवट —' : '— End of passage —'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
