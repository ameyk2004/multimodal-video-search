import { useState, useRef, useEffect } from 'react';
import ParticleCanvas from './components/ParticleCanvas';
import ResultCard from './components/ResultCard';
import petheImage from './assets/images/pethekaka.png';

const CONTENT = {
  mr: {
    title: 'साधना नंदादीप',
    subtitle: 'डॉ. सुहास पेठे (श्री पेठेकाका) यांच्या शिकवणींचा आणि साहित्याचा AI-आधारित शोध. अभंग, आरत्या, श्लोक आणि चिंतने येथे शोधा.',
    bio: 'डॉ. सुहास पेठे तथा श्री पेठेकाका हे महाराष्ट्रातील सातारा येथे वास्तव्यास असणारे एक तत्त्वज्ञ संत आहेत. माणूस, सृष्टी यांची दु:खे व त्यांचा निरास - हे श्री काकांच्या कार्याचे केंद्रबिंदू असून, आपल्या विविधांगी व्यासंगाचा त्यांनी अगणित व्यक्तींना विनामूल्य लाभ आजन्म करून दिला आहे. या ॲपमध्ये श्री काकांनी संकलित केलेले विविध संतांचे अभंग आणि श्री काकांनी स्वतः लिहिलेले अभंग, आरत्या, श्लोक, विविध नित्यपाठ, चिंतने, ७५ पुस्तके व इतर प्रासंगिक रचनांचा समावेश आहे. या सर्व रचनांना श्री काकांनी अतिशय भावपूर्ण चाली दिल्या असून गेली सुमारे पस्तीस वर्षे जिज्ञासू साधक त्यांचा वैयक्तिक उपासनेसाठी व साधनेकरिता अभ्यासासाठी म्हणून उपयोग करीत आहेत. श्री काकांचे हे नि:स्वार्थकार्य शांतपणे तेवणाऱ्या "नंदादीपा"प्रमाणे अविरत चालू असून त्या प्रकाशात आजवर अनेक साधकांचे जीवनपथ उजळून निघाले आहेत.',
    placeholder: 'मराठी किंवा इंग्रजीत प्रश्न विचारा...',
    suggestions: ['ध्यान मार्ग', 'अभंग', 'सृष्टीची दुःखे', 'आरती', 'ज्ञानेश्वरी'],
    loading: 'शोधत आहे...',
    found: 'ज्ञानाचे मोती सापडले',
    searchErr: 'शोध अयशस्वी',
    tryThese: 'हे प्रश्न विचारून पहा:'
  },
  en: {
    title: 'Sadhana Nandadeep',
    subtitle: 'AI-powered search through the teachings, abhangs, and spiritual literature of Dr. Suhas Pethe (Shree Pethe Kaka).',
    bio: 'Dr. Suhas Pethe, also known as Shree Pethe Kaka, is a philosopher saint residing in Satara, Maharashtra. The sorrows of human beings and nature, and their eradication, are the focal points of Shree Kaka\'s work. Through his multifaceted studies, he has provided invaluable benefits to countless individuals for free throughout his life. This app includes various Abhangs of saints compiled by Shree Kaka, as well as Abhangs, Aartis, Shlokas, daily prayers, meditations, 75 books, and other occasional compositions written by Shree Kaka himself. Shree Kaka has composed extremely soulful tunes for all these works, and for the last 35 years, curious seekers have been using them for personal worship and spiritual practice. This selfless work of Shree Kaka continues uninterrupted like a quietly burning "Nandadeep" (lamp), and its light has illuminated the life paths of many seekers to date.',
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
  const [currentTab, setCurrentTab] = useState('search'); // 'search' or 'stories'
  const [query, setQuery] = useState('');
  const [sessions, setSessions] = useState([]); // [{query, results, metadata, error}]
  const [loading, setLoading] = useState(false);
  const [apiUrl, setApiUrl] = useState(import.meta.env.VITE_API_URL);
  const [configLoaded, setConfigLoaded] = useState(false);
  
  const [allStories, setAllStories] = useState([]);
  const [storiesLoading, setStoriesLoading] = useState(false);
  const [hasFetchedStories, setHasFetchedStories] = useState(false);
  const [storySearchQuery, setStorySearchQuery] = useState('');
  
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

  useEffect(() => {
    if (currentTab === 'stories' && !hasFetchedStories) {
      setHasFetchedStories(true); // Ensure we don't infinitely retry if it fails
      setStoriesLoading(true);
      const baseUrl = apiUrl.replace(/\/search$/, '');
      fetch(`${baseUrl}/stories`)
        .then(res => res.json())
        .then(data => {
          if (data.stories) setAllStories(data.stories);
        })
        .catch(err => console.error("Failed to fetch stories:", err))
        .finally(() => setStoriesLoading(false));
    }
  }, [currentTab, apiUrl, hasFetchedStories]);
  const handleSearch = async (q) => {
    const searchQuery = (q || query).trim();
    if (!searchQuery || loading || !apiUrl) return;
    setQuery('');
    setLoading(true);
    setCurrentTab('search');

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

  const filteredStories = allStories.filter(s => 
    (s.title || '').toLowerCase().includes(storySearchQuery.toLowerCase()) || 
    (s.content || '').toLowerCase().includes(storySearchQuery.toLowerCase())
  );

  return (
    <>
      <div className="bg-gradient" />
      <ParticleCanvas />

      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="logo-nav-group">
            <a className="logo" href="#" onClick={(e) => { e.preventDefault(); setCurrentTab('search'); }}>
              <span className="logo-icon">🪔</span>
              <span className="logo-text">{lang === 'mr' ? 'साधना नंदादीप' : 'Sadhana Nandadeep'}</span>
            </a>
            <nav className="desktop-nav">
              <button 
                className={`nav-link ${currentTab === 'search' ? 'active' : ''}`}
                onClick={() => setCurrentTab('search')}
              >
                {lang === 'mr' ? 'ज्ञानकोश' : 'Search'}
              </button>
              <button 
                className={`nav-link ${currentTab === 'stories' ? 'active' : ''}`}
                onClick={() => setCurrentTab('stories')}
              >
                {lang === 'mr' ? 'कथा व गोष्टी' : 'Stories'}
              </button>
            </nav>
          </div>
          <div className="header-controls">
            <button className="lang-toggle" onClick={() => setLang(l => l === 'mr' ? 'en' : 'mr')}>
              {lang === 'mr' ? 'English' : 'मराठी'}
            </button>
          </div>
        </header>

        {/* Main content */}
        <main className="main">
          {currentTab === 'stories' && (
            <div className="stories-page">
              <div className="stories-header">
                <h2>{lang === 'mr' ? 'अध्यात्मिक गोष्टी व कथा' : 'Spiritual Stories & Tales'}</h2>
                <input 
                  type="text" 
                  className="story-search-input"
                  placeholder={lang === 'mr' ? 'कथा शोधा...' : 'Search stories...'}
                  value={storySearchQuery}
                  onChange={(e) => setStorySearchQuery(e.target.value)}
                />
              </div>
              
              {storiesLoading ? (
                <div className="loading-wrapper">
                  <div className="energy-ring" />
                  <span className="loading-text">{lang === 'mr' ? 'कथा लोड होत आहेत...' : 'Loading stories...'}</span>
                </div>
              ) : (
                <div className="stories-grid">
                  {filteredStories.length === 0 ? (
                    <p className="no-results">{lang === 'mr' ? 'कोणतीही कथा आढळली नाही.' : 'No stories found.'}</p>
                  ) : (
                    filteredStories.map((story, i) => (
                      <div key={i} className="story-card">
                        <h3 className="story-card-title">{story.title}</h3>
                        <p className="story-card-content">{story.content}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {currentTab === 'search' && sessions.length === 0 && !loading && (
            <div className="hero">
              <div className="hero-top">
                <span className="hero-om">🪔</span>
                <h1 className="hero-title">{t.title}</h1>
                <p className="hero-sub">{t.subtitle}</p>
                
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

              <div className="hero-about">
                <div className="hero-image-container">
                  <div className="hero-image-glow"></div>
                  <img src={petheImage} alt="Shree Pethe Kaka" className="hero-image" />
                </div>
                <div className="hero-bio-card">
                  <p className="hero-bio">{t.bio}</p>
                </div>
              </div>
            </div>
          )}

          {/* Chat thread */}
          {currentTab === 'search' && sessions.map((session, si) => {
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
          {currentTab === 'search' && loading && (
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
        {currentTab === 'search' && (
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
        )}
      </div>
    </>
  );
}

