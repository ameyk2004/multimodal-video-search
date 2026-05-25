import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import './CinematicVideoPanel.css';

const CinematicVideoPanel = ({ videoSummary, initialTitle, onClose, onSearch, onStoryClick }) => {
  const [details, setDetails] = useState(null);
  const [topics, setTopics] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [practices, setPractices] = useState([]);
  const [verses, setVerses] = useState([]);

  const [loading, setLoading] = useState(true);

  const videoId = videoSummary.video_id;

  const [showAllTopics, setShowAllTopics] = useState(false);
  const [showAllQuestions, setShowAllQuestions] = useState(false);
  const [showAllStories, setShowAllStories] = useState(false);
  const [showAllPractices, setShowAllPractices] = useState(false);
  const [showAllVerses, setShowAllVerses] = useState(false);
  
  const [activeTab, setActiveTab] = useState('topics');

  useEffect(() => {
    setLoading(true);
    api.getVideoDetails(videoId)
      .then(res => {
        setDetails(res);
        setTopics(res.topics || []);
        setQuestions(res.queries || []);
        setPractices(res.practices || []);
        setVerses(res.verses || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load video details:", err);
        setLoading(false);
      });
  }, [videoId]);

  const embedUrl = `https://www.youtube.com/embed/${videoId}?autoplay=1&modestbranding=1&rel=0`;

  const displayedTopics = showAllTopics ? topics : topics.slice(0, 5);
  const displayedQuestions = showAllQuestions ? questions : questions.slice(0, 5);
  const displayedStories = details?.stories ? (showAllStories ? details.stories : details.stories.slice(0, 5)) : [];
  const displayedPractices = showAllPractices ? practices : practices.slice(0, 5);
  const displayedVerses = showAllVerses ? verses : verses.slice(0, 5);

  return (
    <div className="cinematic-overlay" onClick={onClose}>
      <div className="cinematic-panel-container" onClick={e => e.stopPropagation()}>
        <button className="cinematic-close-btn" onClick={onClose}>×</button>
        <div className="cinematic-layout">
          {/* LEFT: Immersive Player */}
          <div className="cinematic-player-section">
            <div className="cinematic-player-wrapper">
              <iframe
                src={embedUrl}
                title="YouTube Video Player"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="cinematic-iframe"
              ></iframe>
            </div>
            <div className="cinematic-player-info">
              <h1 className="cinematic-title">{initialTitle || `Discourse ${videoId}`}</h1>
              <p className="cinematic-meta-sub">
                {videoSummary.topic_count} Topics Covered • {videoSummary.query_count} Questions
              </p>
            </div>
          </div>

          {/* RIGHT: Scrollable Knowledge Panel */}
          <div className="cinematic-knowledge-panel">
            <div className="knowledge-tabs">
              <button className={`k-tab ${activeTab === 'topics' ? 'active' : ''}`} onClick={() => setActiveTab('topics')}>Topics & Queries</button>
              <button className={`k-tab ${activeTab === 'practices' ? 'active' : ''}`} onClick={() => setActiveTab('practices')}>Action Items</button>
              <button className={`k-tab ${activeTab === 'verses' ? 'active' : ''}`} onClick={() => setActiveTab('verses')}>Verses</button>
              <button className={`k-tab ${activeTab === 'stories' ? 'active' : ''}`} onClick={() => setActiveTab('stories')}>Stories</button>
            </div>
            
            <div className="knowledge-panel-content">
              {loading ? (
                <div className="knowledge-loading">Loading teachings...</div>
              ) : (
                <>
                  {activeTab === 'topics' && (
                    <>
                      <section className="knowledge-section">
                        <h2>Key Topics</h2>
                        <div className="knowledge-tags">
                          {displayedTopics.map((t, i) => (
                            <span key={i} className="knowledge-tag topic-tag">{t}</span>
                          ))}
                          {topics.length > 5 && (
                            <button className="view-more-btn" onClick={() => setShowAllTopics(!showAllTopics)}>
                              {showAllTopics ? "View Less" : "View More"}
                            </button>
                          )}
                          {topics.length === 0 && <span className="knowledge-empty">No topics found.</span>}
                        </div>
                      </section>

                      <section className="knowledge-section">
                        <h2>Questions You Can Ask</h2>
                        <ul className="knowledge-query-list">
                          {displayedQuestions.map((q, i) => (
                            <li 
                              key={i} 
                              className={`knowledge-query-item ${onSearch ? 'clickable' : ''}`}
                              onClick={() => { if (onSearch) onSearch(q); }}
                            >
                              {q}
                            </li>
                          ))}
                          {questions.length > 5 && (
                            <button className="view-more-btn" onClick={() => setShowAllQuestions(!showAllQuestions)} style={{ marginTop: '10px' }}>
                              {showAllQuestions ? "View Less" : "View More"}
                            </button>
                          )}
                          {questions.length === 0 && <span className="knowledge-empty">No queries found.</span>}
                        </ul>
                      </section>
                    </>
                  )}

                  {activeTab === 'practices' && (
                    <section className="knowledge-section">
                      <h2>Actionable Practices (साधना/आचरण)</h2>
                      <ul className="knowledge-practice-list">
                        {displayedPractices.map((p, i) => (
                          <li key={i} className="knowledge-practice-item">{p}</li>
                        ))}
                        {practices.length > 5 && (
                          <button className="view-more-btn" onClick={() => setShowAllPractices(!showAllPractices)} style={{ marginTop: '10px' }}>
                            {showAllPractices ? "View Less" : "View More"}
                          </button>
                        )}
                        {practices.length === 0 && <span className="knowledge-empty">No actionable practices found.</span>}
                      </ul>
                    </section>
                  )}

                  {activeTab === 'verses' && (
                    <section className="knowledge-section">
                      <h2>Quoted Verses (श्लोक/अभंग)</h2>
                      <div className="knowledge-verse-list">
                        {displayedVerses.map((v, i) => (
                          <div key={i} className="knowledge-verse-card">
                            <p className="verse-text">{v.verse_text}</p>
                            {v.source_or_author && <span className="verse-source">— {v.source_or_author}</span>}
                          </div>
                        ))}
                        {verses.length > 5 && (
                          <button className="view-more-btn" onClick={() => setShowAllVerses(!showAllVerses)} style={{ marginTop: '10px' }}>
                            {showAllVerses ? "View Less" : "View More"}
                          </button>
                        )}
                        {verses.length === 0 && <span className="knowledge-empty">No quoted verses found.</span>}
                      </div>
                    </section>
                  )}

                  {activeTab === 'stories' && (
                    <section className="knowledge-section">
                      <h2>Featured Stories</h2>
                      <div className="knowledge-story-list">
                        {displayedStories.length > 0 ? (
                          <>
                            {displayedStories.map((story, i) => (
                              <div 
                                key={i} 
                                className="knowledge-story-card"
                                onClick={() => { if (onStoryClick) onStoryClick(story); }}
                                style={{ cursor: onStoryClick ? 'pointer' : 'default', transition: 'background 0.2s', '&:hover': { background: 'rgba(255,255,255,0.05)' } }}
                              >
                                <h3 style={{ color: onStoryClick ? 'var(--saffron)' : 'inherit' }}>{story.title}</h3>
                                {story.moral && <p className="story-moral">"{story.moral}"</p>}
                              </div>
                            ))}
                            {details.stories.length > 5 && (
                              <button className="view-more-btn" onClick={() => setShowAllStories(!showAllStories)} style={{ alignSelf: 'flex-start' }}>
                                {showAllStories ? "View Less" : "View More"}
                              </button>
                            )}
                          </>
                        ) : (
                          <span className="knowledge-empty">No stories available.</span>
                        )}
                      </div>
                    </section>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CinematicVideoPanel;
