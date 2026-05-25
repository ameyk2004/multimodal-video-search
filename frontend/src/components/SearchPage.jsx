import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ResultCard from './ResultCard';
import RelatedQuestions from './RelatedQuestions';
import SearchGreeting from './SearchGreeting';
import { api } from '../utils/api';

export default function SearchPage({ 
  lang, t, 
  query, setQuery, 
  sessions, setSessions, 
  loading, setLoading,
  isListening, setIsListening,
  handleSearch, startVoiceSearch,
  bottomRef, latestSessionRef, inputRef
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [playingVideoId, setPlayingVideoId] = useState(null);

  useEffect(() => {
    if (loading) {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    } else if (latestSessionRef.current) {
      setTimeout(() => latestSessionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
    } else {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  }, [sessions, loading]);



  return (
    <div className="search-page" style={{ paddingBottom: '100px' }}>
      {sessions.length === 0 && !loading && (
        <SearchGreeting onSearch={handleSearch} lang={lang} />
      )}

      {sessions.map((session, si) => {
        const isLatest = si === sessions.length - 1;

        return (
          <div key={si} className="chat-thread" ref={isLatest ? latestSessionRef : null}>
            <div className="user-bubble-row">
              <div className="user-bubble">{session.query}</div>
            </div>

            {session.error && (
              <div className="error-box">⚠ {session.error}</div>
            )}

            {session.results.length > 0 && (
              <div>
                <div className="results-header">
                  <span>✧ {lang === 'mr' ? `${session.results.length} ${t.found}` : `${session.results.length} ${t.found}`}</span>
                </div>
                <div className="results-list">
                  {session.results.map((r, i) => (
                    <ResultCard
                      key={`${r.video_id}-${r.start_time}-${i}`}
                      result={r}
                      rank={i + 1}
                      isMarathi={lang === 'mr'}
                      metadata={session.metadata?.[r.video_id]}
                      onSearch={handleSearch}
                      style={{ animationDelay: `${i * 0.08}s` }}
                      playingVideoId={playingVideoId}
                      setPlayingVideoId={setPlayingVideoId}
                    />
                  ))}
                </div>
                
                <RelatedQuestions 
                  metadata={session.metadata} 
                  onSearch={handleSearch} 
                  lang={lang}
                />
              </div>
            )}
          </div>
        );
      })}

      {loading && (
        <div className="chat-thread">
          <div className="user-bubble-row">
            <div className="user-bubble" style={{ opacity: 0.7 }}>...</div>
          </div>
          <div className="loading-wrapper">
            <div className="energy-ring" />
            <span className="loading-text">{t.loading}</span>
          </div>
        </div>
      )}
      <div ref={bottomRef} />

      {/* Floating Search Bar for SearchPage */}
      <div className="search-bar-wrap">
        <div className="search-form">
          <input
            ref={inputRef}
            className="search-input"
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder={t.placeholder}
            autoComplete="off"
            disabled={loading}
          />
          <button 
            onClick={() => startVoiceSearch(setQuery)} 
            className={`icon-btn ${isListening ? 'listening' : ''}`}
            title="Voice Search"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
          </button>
          <button 
            className="search-btn" 
            onClick={() => handleSearch()} 
            disabled={!query.trim() || loading}
          >
            {loading ? '✧' : '→'}
          </button>
        </div>
      </div>
    </div>
  );
}
