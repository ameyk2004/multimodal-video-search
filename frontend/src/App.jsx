import { useState, useRef, useEffect, useMemo } from 'react';
import { Routes, Route, NavLink, useNavigate, useLocation } from 'react-router-dom';
import ParticleCanvas from './components/ParticleCanvas';
import ResultCard from './components/ResultCard';
import StoryCard from './components/StoryCard';
import VideoLibraryCard from './components/VideoLibraryCard';
import CinematicVideoPanel from './components/CinematicVideoPanel';
import HomePage from './components/HomePage';
import SearchPage from './components/SearchPage';
import StoriesBanner from './components/StoriesBanner';
import MusicPage from './components/MusicPage';
import { api } from './utils/api';

const CONTENT = {
  mr: {
    title: 'साधननंदादीप',
    subtitle: 'डॉ. सुहास पेठे (श्री पेठेकाका) यांच्या शिकवणींचा आणि साहित्याचा AI-आधारित शोध. अभंग, आरत्या, श्लोक आणि चिंतने येथे शोधा.',
    bio: 'डॉ. सुहास पेठे तथा श्री पेठेकाका हे महाराष्ट्रातील सातारा येथे वास्तव्यास असणारे एक तत्त्वज्ञ संत आहेत. माणूस, सृष्टी यांची दु:खे व त्यांचा निरास - हे श्री काकांच्या कार्याचे केंद्रबिंदू असून, आपल्या विविधांगी व्यासंगाचा त्यांनी अगणित व्यक्तींना विनामूल्य लाभ आजन्म करून दिला आहे. या ॲपमध्ये श्री काकांनी संकलित केलेले विविध संतांचे अभंग आणि श्री काकांनी स्वतः लिहिलेले अभंग, आरत्या, श्लोक, विविध नित्यपाठ, चिंतने, ७५ पुस्तके व इतर प्रासंगिक रचनांचा समावेश आहे. या सर्व रचनांना श्री काकांनी अतिशय भावपूर्ण चाली दिल्या असून गेली सुमारे पस्तीस वर्षे जिज्ञासू साधक त्यांचा वैयक्तिक उपासनेसाठी व साधनेकरिता अभ्यासासाठी म्हणून उपयोग करीत आहेत. श्री काकांचे हे नि:स्वार्थकार्य शांतपणे तेवणाऱ्या "नंदादीपा"प्रमाणे अविरत चालू असून त्या प्रकाशात आजवर अनेक साधकांचे जीवनपथ उजळून निघाले आहेत.',
    placeholder: 'मराठी किंवा इंग्रजीत प्रश्न विचारा...',
    suggestions: ['ध्यान मार्ग', 'अभंग', 'सृष्टीची दुःखे', 'आरती', 'ज्ञानेश्वरी'],
    loading: 'शोधत आहे...',
    found: 'ज्ञानाचे मोती सापडले',
    searchErr: 'शोध अयशस्वी',
    tryThese: 'हे प्रश्न विचारून पहा:',
    searchTab: 'ज्ञानकोश',
    storiesTab: 'कथा व गोष्टी',
    libraryTab: 'अध्यात्मिक संग्रह',
    musicTab: 'अभंग व आरत्या',
    storiesTitle: 'अध्यात्मिक गोष्टी व कथा',
    searchStories: 'कथा शोधा...',
    loadingStories: 'कथा व संग्रह लोड होत आहेत...',
    noStories: 'कोणतीही कथा आढळली नाही.',
    libraryTitle: 'प्रवचने आणि शिकवण',
    librarySub: 'या संग्रहात उपलब्ध असलेली प्रवचने, त्यांचे विषय आणि विचारण्यासाठी योग्य प्रश्न',
    videoLabel: 'प्रवचन विभाग',
    topicsLabel: 'शिकवणीचे विषय:',
    queriesLabel: 'साधकांचे संभाव्य प्रश्न:',
  },
  en: {
    title: 'Sadhananandadeep',
    subtitle: 'AI-powered search through the teachings, abhangs, and spiritual literature of Dr. Suhas Pethe (Shree Pethe Kaka).',
    bio: 'Dr. Suhas Pethe, also known as Shree Pethe Kaka, is a philosopher saint residing in Satara, Maharashtra. The sorrows of human beings and nature, and their eradication, are the focal points of Shree Kaka\'s work. Through his multifaceted studies, he has provided invaluable benefits to countless individuals for free throughout his life. This app includes various Abhangs of saints compiled by Shree Kaka, as well as Abhangs, Aartis, Shlokas, daily prayers, meditations, 75 books, and other occasional compositions written by Shree Kaka himself. Shree Kaka has composed extremely soulful tunes for all these works, and for the last 35 years, curious seekers have been using them for personal worship and spiritual practice. This selfless work of Shree Kaka continues uninterrupted like a quietly burning "Nandadeep" (lamp), and its light has illuminated the life paths of many seekers to date.',
    placeholder: 'Ask your question in English or Marathi...',
    suggestions: ['Meditation path', 'Abhangs', 'Sorrows of life', 'Arati', 'Dnyaneshwari'],
    loading: 'Searching wisdom...',
    found: 'teachings found',
    searchErr: 'Search failed',
    tryThese: 'Suggested Queries:',
    searchTab: 'Search',
    storiesTab: 'Stories',
    libraryTab: 'Spiritual Library',
    musicTab: 'Music & Aartis',
    storiesTitle: 'Spiritual Stories & Tales',
    searchStories: 'Search stories...',
    loadingStories: 'Loading stories & library...',
    noStories: 'No stories found.',
    libraryTitle: 'Discourses & Teachings',
    librarySub: 'Explore the available spiritual discourses, the topics they cover, and suggested questions for seekers.',
    videoLabel: 'Discourse Segment',
    topicsLabel: 'Topics Covered:',
    queriesLabel: 'Suggested Queries for Seekers:',
  }
};

export default function App() {
  const [lang, setLang] = useState('mr');
  const [query, setQuery] = useState('');
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  
  const [allStories, setAllStories] = useState([]);
  const [allVideos, setAllVideos] = useState([]);
  const [dataLoading, setDataLoading] = useState(false);
  const [hasFetchedData, setHasFetchedData] = useState(false);
  const [storySearchQuery, setStorySearchQuery] = useState('');

  const _STORY_TOPICS = useMemo(() => {
    const topics = new Set();
    allStories.forEach(s => {
      if (s.associated_topics) s.associated_topics.forEach(t => topics.add(t));
    });
    return Array.from(topics).sort();
  }, [allStories]);

  const _STORY_SAINTS = useMemo(() => {
    const saints = new Set();
    allStories.forEach(s => {
      if (s.normalized_saint_name) saints.add(s.normalized_saint_name);
      else if (s.character_or_saint) saints.add(s.character_or_saint);
    });
    return Array.from(saints).sort();
  }, [allStories]);

  const _LIBRARY_TOPICS = useMemo(() => {
    const topics = new Set();
    allVideos.forEach(v => {
      if (v.key_topics) v.key_topics.forEach(t => topics.add(t));
      if (v.topics) v.topics.forEach(t => topics.add(t));
    });
    return Array.from(topics).sort();
  }, [allVideos]);
  const uniqueLibraryTopics = useMemo(() => ['सर्व', ..._LIBRARY_TOPICS], [_LIBRARY_TOPICS]);

  const [topicFilter, setTopicFilter] = useState('सर्व');
  const [saintFilter, setSaintFilter] = useState('सर्व');
  const [libraryActiveFilter, setLibraryActiveFilter] = useState('सर्व');
  const [isListening, setIsListening] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedVideoTitle, setSelectedVideoTitle] = useState('');

  const startVoiceSearch = async (setQueryState) => {
    if (!window.isSecureContext) {
      alert('Microphone access is blocked! Mobile browsers require a secure HTTPS connection for voice search. Since you are likely testing on your local network (HTTP), you must either use your live CloudFront URL, or use a tunneling tool (like ngrok) to get a temporary HTTPS URL for testing.');
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Your browser does not support voice search.');
      return;
    }

    // iOS Safari Bug Fix: Manually request microphone permission first to force the OS prompt.
    // If we just call recognition.start(), Safari sometimes silently blocks it with 'service-not-allowed'.
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Stop the tracks immediately so we don't hold the mic unnecessarily. 
        // SpeechRecognition will grab its own stream now that permission is granted.
        stream.getTracks().forEach(track => track.stop());
      }
    } catch (err) {
      console.error("Microphone permission denied manually:", err);
      alert('Microphone permission is required for voice search. Please click "Allow" when the browser asks for microphone access, or check your browser settings.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = lang === 'mr' ? 'mr-IN' : 'en-US';
    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQueryState(transcript);
    };
    recognition.onerror = (e) => {
      console.error("Speech error", e);
      if (e.error === 'not-allowed') {
        alert('Microphone permission denied. Please allow microphone access in your browser or device settings.');
      } else if (e.error === 'aborted') {
        console.warn('Voice search aborted by user or browser.');
      } else if (e.error === 'network') {
        alert('Voice search error: network. Make sure you have a stable internet connection. On iOS, you may need to enable Dictation in your keyboard settings.');
      } else if (e.error === 'no-speech') {
        alert('No speech was detected. Please try again and speak closer to the microphone.');
      } else if (e.error === 'service-not-allowed') {
        alert('Voice search is blocked by your device settings. On Android, ensure the "Google" app is enabled. On iPhone, you must use Safari (not Chrome) and have Dictation enabled in Keyboard settings.');
      } else {
        alert(`Voice search error: ${e.error}.`);
      }
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    recognition.start();
  };
  
  const bottomRef = useRef(null);
  const latestSessionRef = useRef(null);
  const inputRef = useRef(null);
  
  const navigate = useNavigate();
  const location = useLocation();

  const t = CONTENT[lang];

  useEffect(() => {
    api.getConfig().catch(console.error);
  }, []);



  // Fetch stories and library data once
  useEffect(() => {
    if (!hasFetchedData) {
      setHasFetchedData(true);
      setDataLoading(true);
      
      Promise.all([
        api.getStories().catch(e => { console.error(e); return { stories: [] }; }),
        api.getVideos().catch(e => { console.error(e); return { videos: [] }; })
      ])
      .then(([storiesData, videosData]) => {
        if (storiesData.stories) setAllStories(storiesData.stories);
        if (videosData.videos) setAllVideos(videosData.videos);
      })
      .finally(() => setDataLoading(false));
    }
  }, [hasFetchedData]);

  const handleSearch = async (q) => {
    const searchQuery = (q || query).trim();
    if (!searchQuery || loading) return;
    setQuery('');
    setLoading(true);
    navigate('/search');

    try {
      const data = await api.search(searchQuery);
      
      setSessions(prev => [...prev, { 
        query: data.translated_query && data.translated_query !== searchQuery ? `${searchQuery} (${data.translated_query})` : searchQuery, 
        results: data.results || [], 
        metadata: data.metadata || {},
        error: null 
      }]);
    } catch (err) {
      setSessions(prev => [...prev, { query: searchQuery, results: [], metadata: {}, error: err.message }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const filteredStories = allStories.filter(s => {
    const textToSearch = (
      s.title + ' ' + 
      (s.moral || '') + ' ' + 
      (s.character_or_saint || '') + ' ' + 
      (s.normalized_saint_name || '') + ' ' + 
      (s.associated_topics?.join(' ') || '')
    ).toLowerCase();
    
    const queryMatch = textToSearch.includes(storySearchQuery.toLowerCase());
    
    const topicMatch = topicFilter === 'सर्व' ? true : (s.associated_topics && s.associated_topics.includes(topicFilter));
    const saintMatch = saintFilter === 'सर्व' ? true : (s.normalized_saint_name === saintFilter || s.character_or_saint === saintFilter);
    
    return queryMatch && topicMatch && saintMatch;
  });

  return (
    <>
      <div className="bg-gradient" />
      <ParticleCanvas />
      <div className="app">
        <header className="header">
          <div className="logo-nav-group">
            <NavLink to="/" className="logo">
              <span className="logo-icon">🪔</span>
              <span className="logo-text">{lang === 'mr' ? 'साधननंदादीप' : 'Sadhananandadeep'}</span>
            </NavLink>
            <nav className="desktop-nav">
              <NavLink to="/" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
                {t.searchTab}
              </NavLink>
              <NavLink to="/stories" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
                {t.storiesTab}
              </NavLink>
              <NavLink to="/music" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
                {t.musicTab}
              </NavLink>
              <NavLink to="/library" className={({isActive}) => `nav-link ${isActive ? 'active' : ''}`}>
                {t.libraryTab}
              </NavLink>
            </nav>
          </div>
          <div className="header-controls">
            <button className="lang-toggle" onClick={() => setLang(l => l === 'mr' ? 'en' : 'mr')}>
              {lang === 'mr' ? 'English' : 'मराठी'}
            </button>
          </div>
        </header>

        <main className="main">
          <Routes>
            <Route path="/stories" element={
              <div className="stories-page">
                <StoriesBanner 
                  isLoading={dataLoading} 
                  totalStories={allStories.length} 
                  filteredStories={filteredStories.length} 
                />
                
                <div className="premium-search-container">
                  <div className="premium-search-box">
                    <span className="premium-search-icon">🔍</span>
                    <input 
                      type="text" 
                      className="premium-search-input"
                      placeholder="कथा, शिकवण किंवा संत शोधा..."
                      value={storySearchQuery}
                      onChange={(e) => setStorySearchQuery(e.target.value)}
                    />
                    <button 
                      onClick={() => startVoiceSearch(setStorySearchQuery)} 
                      className={`icon-btn ${isListening ? 'listening' : ''}`}
                      title="Voice Search"
                    >
                      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                        <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                      </svg>
                    </button>
                    <button 
                      className="icon-btn"
                      onClick={() => setShowMobileFilters(true)}
                      title="Open Filters"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="4" y1="21" x2="4" y2="14"></line>
                        <line x1="4" y1="10" x2="4" y2="3"></line>
                        <line x1="12" y1="21" x2="12" y2="12"></line>
                        <line x1="12" y1="8" x2="12" y2="3"></line>
                        <line x1="20" y1="21" x2="20" y2="16"></line>
                        <line x1="20" y1="12" x2="20" y2="3"></line>
                        <line x1="1" y1="14" x2="7" y2="14"></line>
                        <line x1="9" y1="8" x2="15" y2="8"></line>
                        <line x1="17" y1="16" x2="23" y2="16"></line>
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Filter Drawer */}
                {showMobileFilters && (
                  <div className="filter-drawer-overlay" onClick={() => setShowMobileFilters(false)}>
                    <div className="filter-drawer open" onClick={e => e.stopPropagation()}>
                      <div className="filter-drawer-header">
                        <h3>Filters</h3>
                        <button className="close-drawer-btn" onClick={() => setShowMobileFilters(false)}>✕</button>
                      </div>
                      <div className="filter-drawer-content">
                        <div className="filter-group">
                          <label>Topic (विषय)</label>
                          <select 
                            className="premium-select"
                            value={topicFilter} 
                            onChange={(e) => setTopicFilter(e.target.value)}
                          >
                            <option value="सर्व">All Topics (सर्व)</option>
                            {_STORY_TOPICS.map(topic => (
                              <option key={topic} value={topic}>{topic}</option>
                            ))}
                          </select>
                        </div>
                        
                        <div className="filter-group">
                          <label>Saint / Character (संत)</label>
                          <select 
                            className="premium-select"
                            value={saintFilter} 
                            onChange={(e) => setSaintFilter(e.target.value)}
                          >
                            <option value="सर्व">All Saints (सर्व)</option>
                            {_STORY_SAINTS.map(saint => (
                              <option key={saint} value={saint}>{saint}</option>
                            ))}
                          </select>
                        </div>
                        
                        <div className="filter-actions">
                          <button 
                            className="filter-reset-btn" 
                            onClick={() => { setTopicFilter('सर्व'); setSaintFilter('सर्व'); setStorySearchQuery(''); }}
                          >
                            Reset All
                          </button>
                          <button 
                            className="filter-apply-btn" 
                            onClick={() => setShowMobileFilters(false)}
                          >
                            View {filteredStories.length} Results
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {dataLoading ? (
                  <div className="loading-wrapper">
                    <div className="energy-ring" />
                    <span className="loading-text">{t.loadingStories}</span>
                  </div>
                ) : (
                  <div className="stories-list" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {filteredStories.length === 0 ? (
                      <p className="no-results" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
                        {t.noStories}
                      </p>
                    ) : (
                      filteredStories.map((story, i) => (
                        <StoryCard 
                          key={`${story.video_id}-${i}`} 
                          story={story} 
                          autoOpen={location.state?.openStoryTitle === story.title}
                        />
                      ))
                    )}
                  </div>
                )}
              </div>
            } />

            <Route path="/library" element={
              <div className="library-page">
                {/* Immersive Top Discovery Area */}
                <div className="library-top-discovery">
                  <div className="library-search-container">
                    <span className="library-search-icon">🔍</span>
                    <input 
                      type="text" 
                      className="library-premium-search" 
                      placeholder="प्रवचन, विषय, प्रश्न किंवा शिकवण शोधा..." 
                    />
                  </div>
                  
                  <div className="library-category-pills">
                    {uniqueLibraryTopics.map(cat => (
                      <button 
                        key={cat} 
                        className={`library-pill-premium ${libraryActiveFilter === cat ? 'active' : ''}`}
                        onClick={() => setLibraryActiveFilter(cat)}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>
                
                {dataLoading ? (
                  <div className="loading-wrapper">
                    <div className="energy-ring" />
                    <span className="loading-text">Loading Library...</span>
                  </div>
                ) : (
                  <>
                    {/* Simple Grid of all videos from /videos */}
                    <div className="library-shelves-container" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '24px', padding: '20px 0' }}>
                      {allVideos.filter(v => {
                        if (libraryActiveFilter === 'सर्व') return true;
                        return (v.topics && v.topics.includes(libraryActiveFilter)) || (v.key_topics && v.key_topics.includes(libraryActiveFilter));
                      }).map((v, i) => (
                        <VideoLibraryCard 
                          key={`${v.video_id}-${i}`} 
                          video={v} 
                          onClick={(title) => {
                            setSelectedVideo(v);
                            setSelectedVideoTitle(title || "Teaching Module");
                          }} 
                        />
                      ))}
                    </div>
                  </>
                )}
                
                {selectedVideo && (
                  <CinematicVideoPanel 
                    videoSummary={selectedVideo} 
                    initialTitle={selectedVideoTitle}
                    onClose={() => setSelectedVideo(null)} 
                    onSearch={(q) => {
                      setSelectedVideo(null);
                      handleSearch(q);
                    }}
                    onStoryClick={(story) => {
                      setSelectedVideo(null);
                      navigate('/stories', { state: { openStoryTitle: story.title } });
                    }}
                  />
                )}
              </div>
            } />

            <Route path="/music" element={<MusicPage lang={lang} />} />

            <Route path="/" element={<HomePage t={t} lang={lang} allVideos={allVideos} onSearch={handleSearch} />} />
            
            <Route path="/search" element={
              <SearchPage 
                lang={lang} 
                t={t} 
                query={query} 
                setQuery={setQuery} 
                sessions={sessions} 
                setSessions={setSessions} 
                loading={loading} 
                setLoading={setLoading}
                isListening={isListening} 
                setIsListening={setIsListening}
                handleSearch={handleSearch} 
                startVoiceSearch={startVoiceSearch}
                bottomRef={bottomRef} 
                latestSessionRef={latestSessionRef} 
                inputRef={inputRef}
              />
            } />
          </Routes>
        </main>
      </div>
    </>
  );
}

