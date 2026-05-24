import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ResultCard from './ResultCard';
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
    if (latestSessionRef.current) {
      latestSessionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [sessions, loading]);



  return (
    <div className="search-page" style={{ paddingBottom: '100px' }}>
      {sessions.length === 0 && !loading && (
        <div className="search-empty-state" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '10vh' }}>
          <h1 style={{ fontSize: '32px', marginBottom: '16px', fontFamily: 'var(--font-dev)', color: 'var(--gold-soft)' }}>
            {t.searchTab}
          </h1>
          <div className="hero-search-prompt" style={{ width: '100%', maxWidth: '800px', padding: '30px', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '24px', border: '1px dashed rgba(249, 115, 22, 0.3)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <p style={{ color: 'var(--gold-soft)', fontSize: '18px', marginBottom: '20px' }}>{t.placeholder}</p>
            <div className="hero-suggestions" style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', justifyContent: 'center' }}>
              {t.suggestions.map(s => (
                <button key={s} className="suggestion-chip" onClick={() => handleSearch(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {sessions.map((session, si) => {
        const isLatest = si === sessions.length - 1;
        const allSuggestions = new Set();
        Object.values(session.metadata || {}).forEach(m => {
          if (m.suggested_queries) m.suggested_queries.forEach(sq => allSuggestions.add(sq));
        });
        const topSuggestions = Array.from(allSuggestions).slice(0, 5);

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
                
                {topSuggestions.length > 0 && (
                  <div className="dynamic-suggestions">
                    <div className="suggestions-label">{t.tryThese}</div>
                    <div className="hero-suggestions" style={{justifyContent: 'flex-start', marginTop: '8px'}}>
                      {topSuggestions.map(s => (
                        <button key={s} className="suggestion-chip" onClick={() => handleSearch(s)}>
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
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
            🎤
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
