import { useState, useRef, useEffect } from 'react';
import ParticleCanvas from './components/ParticleCanvas';
import ResultCard from './components/ResultCard';

const API_URL = import.meta.env.VITE_API_URL;

const CONTENT = {
  mr: {
    title: 'श्री पेठेकाका ज्ञानकोश',
    subtitle: 'डॉ. सुहास पेठे (श्री पेठेकाका) यांच्या शिकवणींचा आणि साहित्याचा AI-आधारित शोध. अभंग, आरत्या, श्लोक आणि चिंतने येथे शोधा.',
    placeholder: 'मराठी किंवा इंग्रजीत प्रश्न विचारा...',
    suggestions: ['ध्यान मार्ग', 'अभंग', 'सृष्टीची दुःखे', 'आरती', 'ज्ञानेश्वरी'],
    loading: 'शोधत आहे...',
    found: 'ज्ञानाचे मोती सापडले',
    searchErr: 'शोध अयशस्वी'
  },
  en: {
    title: 'Shree Pethe Kaka Knowledge Portal',
    subtitle: 'AI-powered search through the teachings, abhangs, and spiritual literature of Dr. Suhas Pethe (Shree Pethe Kaka).',
    placeholder: 'Ask your question in English or Marathi...',
    suggestions: ['Meditation path', 'Abhangs', 'Sorrows of life', 'Arati', 'Dnyaneshwari'],
    loading: 'Searching wisdom...',
    found: 'teachings found',
    searchErr: 'Search failed'
  }
};

export default function App() {
  const [lang, setLang] = useState('mr'); // 'mr' or 'en'
  const [query, setQuery] = useState('');
  const [sessions, setSessions] = useState([]); // [{query, results, error}]
  const [loading, setLoading] = useState(false);
  
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const t = CONTENT[lang];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, loading]);

  const handleSearch = async (q) => {
    const searchQuery = (q || query).trim();
    if (!searchQuery || loading) return;
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || t.searchErr);
      setSessions(prev => [...prev, { query: searchQuery, results: data.results || [], error: null }]);
    } catch (err) {
      setSessions(prev => [...prev, { query: searchQuery, results: [], error: err.message }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  return (
    <>
      <div className="bg-gradient" />
      <ParticleCanvas />

      <div className="app">
        {/* Header */}
        <header className="header">
          <a className="logo" href="/">
            <span className="logo-icon">🪔</span>
            <span className="logo-text">{lang === 'mr' ? 'श्री पेठेकाका' : 'Shree Pethe Kaka'}</span>
          </a>
          <div className="header-controls">
            <button className="lang-toggle" onClick={() => setLang(l => l === 'mr' ? 'en' : 'mr')}>
              {lang === 'mr' ? 'English' : 'मराठी'}
            </button>
          </div>
        </header>

        {/* Main content */}
        <main className="main">
          {sessions.length === 0 && !loading && (
            <div className="hero">
              <span className="hero-om">🪔</span>
              <h1 className="hero-title">{t.title}</h1>
              <p className="hero-sub">{t.subtitle}</p>
              <div className="hero-suggestions">
                {t.suggestions.map(s => (
                  <button key={s} className="suggestion-chip" onClick={() => handleSearch(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Chat thread */}
          {sessions.map((session, si) => (
            <div key={si} className="chat-thread">
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
                        key={`${r.video_id}-${r.start_time}`}
                        result={r}
                        rank={i + 1}
                        isMarathi={lang === 'mr'}
                        style={{ animationDelay: `${i * 0.08}s` }}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Loading State */}
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
        </main>

        {/* Fixed search bar */}
        <div className="search-bar-wrap">
          <div className="search-form">
            <input
              ref={inputRef}
              className="search-input"
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKey}
              placeholder={t.placeholder}
              autoComplete="off"
              disabled={loading}
            />
            <button
              className="search-btn"
              onClick={() => handleSearch()}
              disabled={loading || !query.trim()}
            >
              ➔
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
