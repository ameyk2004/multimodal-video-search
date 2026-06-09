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
  updateSessionFilter,
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
          <div key={session.id || si} className="chat-thread" ref={isLatest ? latestSessionRef : null}>
            <div className="user-bubble-row">
              <div className="user-bubble">{session.query}</div>
            </div>

            {session.error && (
              <div className="error-box">⚠ {session.error}</div>
            )}

            {session.loading ? (
              <div className="loading-wrapper">
                <div className="energy-ring" />
                <span className="loading-text">{t.loading}</span>
              </div>
            ) : session.results.length > 0 && (
              <div>
                <div className="inline-filter-wrap">
                  <div className="search-type-toggle inline-toggle">
                    <button 
                      className={`toggle-btn ${session.selectedFilter === 'video' ? 'active' : ''}`}
                      onClick={() => updateSessionFilter(session.id, 'video')}
                    >
                      {lang === 'mr' ? 'प्रवचने (Videos)' : 'Videos'}
                    </button>
                    <button 
                      className={`toggle-btn ${session.selectedFilter === 'book' ? 'active' : ''}`}
                      onClick={() => updateSessionFilter(session.id, 'book')}
                    >
                      {lang === 'mr' ? 'पुस्तके (Books)' : 'Books'}
                    </button>
                    <button 
                      className={`toggle-btn ${session.selectedFilter === 'combined' ? 'active' : ''}`}
                      onClick={() => updateSessionFilter(session.id, 'combined')}
                    >
                      {lang === 'mr' ? 'सर्व (Combined)' : 'Combined'}
                    </button>
                  </div>
                </div>

                <div className="results-header">
                  <span>✧ {lang === 'mr' ? `येथे काही उत्तरे आहेत` : `Here are some answers`}</span>
                </div>
                <div className="results-list">
                  {(() => {
                    let displayResults = session.results;
                    if (session.selectedFilter === 'video') {
                      displayResults = session.results.filter(r => r.type === 'video').slice(0, 5);
                    } else if (session.selectedFilter === 'book') {
                      displayResults = session.results.filter(r => r.type === 'book').slice(0, 5);
                    } else {
                      // Combined: sort by score, top 5 total
                      displayResults = [...session.results].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 5);
                    }

                    if (displayResults.length === 0) {
                      return <div className="no-filter-results">{lang === 'mr' ? 'या विभागात काही आढळले नाही.' : 'Nothing found in this category.'}</div>;
                    }

                    return displayResults.map((r, i) => (
                      <ResultCard
                        key={`${r.video_id || r.book_name}-${r.start_time || r.page_number}-${i}`}
                        result={r}
                        rank={i + 1}
                        isMarathi={lang === 'mr'}
                        onSearch={handleSearch}
                        style={{ animationDelay: `${i * 0.08}s` }}
                        playingVideoId={playingVideoId}
                        setPlayingVideoId={setPlayingVideoId}
                      />
                    ));
                  })()}
                </div>
                
                <RelatedQuestions 
                  relatedQueries={session.related_queries} 
                  onSearch={handleSearch} 
                  lang={lang}
                />
              </div>
            )}
          </div>
        );
      })}

      {/* Floating Search Bar for SearchPage */}
      <div ref={bottomRef} />
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
