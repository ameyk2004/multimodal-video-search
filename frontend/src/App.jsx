import { useState, useRef, useEffect } from 'react';
import ParticleCanvas from './components/ParticleCanvas';
import ResultCard from './components/ResultCard';
import petheImage from './assets/images/pethekaka.png';

const CONTENT = {
  mr: {
    title: 'श्री पेठेकाका ज्ञानकोश',
    subtitle: 'डॉ. सुहास पेठे (श्री पेठेकाका) यांच्या शिकवणींचा आणि साहित्याचा AI-आधारित शोध. अभंग, आरत्या, श्लोक आणि चिंतने येथे शोधा.',
    bio: 'संत श्री पेठे काका हे साताऱ्याच्या भूमीतून अध्यात्म, साधना आणि नामस्मरणाचा दिवा प्रज्वलित करणारे एक प्रेरणादायी व्यक्तिमत्त्व मानले जातात. त्यांच्या वाणीमध्ये साधेपणा, विचारांमध्ये गूढ अध्यात्म आणि प्रत्येक भक्ताविषयी अपार प्रेम दिसून येते. त्यांनी लोकांना केवळ धर्म शिकवला नाही, तर जीवन कसे शांत, समाधानी आणि सद्गुणी पद्धतीने जगावे हेही समजावून सांगितले. त्यांच्या मार्गदर्शनामुळे अनेकांच्या जीवनात सकारात्मक बदल घडले असून, श्रद्धा, भक्ती आणि आत्मविश्वासाचा नवा प्रकाश निर्माण झाला आहे. त्यांच्या शिकवणीत अहंकारापेक्षा नम्रता, दिखाव्यापेक्षा साधेपणा आणि शब्दांपेक्षा आचरणाला अधिक महत्त्व दिले जाते. अशा या संतस्वरूप व्यक्तिमत्त्वाने अनेकांच्या मनात अढळ श्रद्धेचे स्थान निर्माण केले आहे.',
    placeholder: 'मराठी किंवा इंग्रजीत प्रश्न विचारा...',
    suggestions: ['ध्यान मार्ग', 'अभंग', 'सृष्टीची दुःखे', 'आरती', 'ज्ञानेश्वरी'],
    loading: 'शोधत आहे...',
    found: 'ज्ञानाचे मोती सापडले',
    searchErr: 'शोध अयशस्वी',
    tryThese: 'हे प्रश्न विचारून पहा:'
  },
  en: {
    title: 'Shree Pethe Kaka Knowledge Portal',
    subtitle: 'AI-powered search through the teachings, abhangs, and spiritual literature of Dr. Suhas Pethe (Shree Pethe Kaka).',
    bio: 'Sant Shree Pethe Kaka is considered an inspiring personality from the land of Satara who ignited the lamp of spirituality, spiritual practice, and chanting. His speech reflects simplicity, his thoughts deep spirituality, and his immense love for every devotee. He not only taught religion but also how to live a peaceful, contented, and virtuous life. Under his guidance, many have experienced positive changes in their lives, bringing a new light of faith, devotion, and self-confidence. His teachings emphasize humility over ego, simplicity over show, and action over words. Such a saintly figure has created a place of unwavering faith in the minds of many.',
    placeholder: 'Ask your question in English or Marathi...',
    suggestions: ['Meditation path', 'Abhangs', 'Sorrows of life', 'Arati', 'Dnyaneshwari'],
    loading: 'Searching wisdom...',
    found: 'teachings found',
    searchErr: 'Search failed',
    tryThese: 'Suggested Queries:'
  }
};

export default function App() {
  const [lang, setLang] = useState('mr'); // 'mr' or 'en'
  const [query, setQuery] = useState('');
  const [sessions, setSessions] = useState([]); // [{query, results, metadata, error}]
  const [loading, setLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL);
  const [configLoaded, setConfigLoaded] = useState(false);
  
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  const t = CONTENT[lang];

  // Fetch config.json on mount to support AWS Custom Resource dynamic API URLs
  useEffect(() => {
    fetch('/config.json')
      .then(res => res.json())
      .then(data => {
        if (data.VITE_API_URL) {
          setApiUrl(data.VITE_API_URL);
        }
      })
      .catch(err => console.log('No config.json found, falling back to .env'))
      .finally(() => setConfigLoaded(true));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [sessions, loading]);

  const handleSearch = async (q) => {
    const searchQuery = (q || query).trim();
    if (!searchQuery || loading || !apiUrl) return;
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}?q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || t.searchErr);
      
      setSessions(prev => [...prev, { 
        query: searchQuery, 
        results: data.results || [], 
        metadata: data.metadata || {},
        error: null 
      }]);
    } catch (err) {
      setSessions(prev => [...prev, { query: searchQuery, results: [], metadata: {}, error: err.message }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter') handleSearch();
  };

  if (!configLoaded) return null; // wait for config before rendering

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
              <div className="hero-content-wrapper">
                <div className="hero-image-container">
                  <div className="hero-image-glow"></div>
                  <img src={petheImage} alt="Shree Pethe Kaka" className="hero-image" />
                </div>
                <div className="hero-text-container">
                  <span className="hero-om">🪔</span>
                  <h1 className="hero-title">{t.title}</h1>
                  <p className="hero-sub">{t.subtitle}</p>
                  <div className="hero-bio-card">
                    <p className="hero-bio">{t.bio}</p>
                  </div>
                </div>
              </div>
              
              <div className="hero-search-prompt">
                <p>{t.placeholder}</p>
                <div className="hero-suggestions">
                  {t.suggestions.map(s => (
                    <button key={s} className="suggestion-chip" onClick={() => handleSearch(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Chat thread */}
          {sessions.map((session, si) => {
            // Aggregate all suggested queries from the returned videos
            const allSuggestions = new Set();
            Object.values(session.metadata || {}).forEach(m => {
              if (m.suggested_queries) m.suggested_queries.forEach(sq => allSuggestions.add(sq));
            });
            const topSuggestions = Array.from(allSuggestions).slice(0, 5);

            return (
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
                          key={`${r.video_id}-${r.start_time}-${i}`}
                          result={r}
                          rank={i + 1}
                          isMarathi={lang === 'mr'}
                          metadata={session.metadata?.[r.video_id]}
                          onSearch={handleSearch}
                          style={{ animationDelay: `${i * 0.08}s` }}
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

