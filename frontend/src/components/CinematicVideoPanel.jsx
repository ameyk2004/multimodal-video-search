import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import './CinematicVideoPanel.css';

const CinematicVideoPanel = ({ videoSummary, initialTitle, onClose }) => {
  const [details, setDetails] = useState(null);
  const [topics, setTopics] = useState([]);
  const [questions, setQuestions] = useState([]);
  
  const [loadingDetails, setLoadingDetails] = useState(true);
  const [loadingTopics, setLoadingTopics] = useState(true);
  const [loadingQuestions, setLoadingQuestions] = useState(true);

  const videoId = videoSummary.video_id;

  useEffect(() => {
    // Progressive Data Loading
    
    // 1. Fetch Details (Stories)
    api.getVideoDetails(videoId)
      .then(res => setDetails(res))
      .catch(err => console.error("Failed to load video details:", err))
      .finally(() => setLoadingDetails(false));
      
    // 2. Fetch Topics
    api.getVideoTopics(videoId)
      .then(res => setTopics(res.topics || []))
      .catch(err => console.error("Failed to load topics:", err))
      .finally(() => setLoadingTopics(false));
      
    // 3. Fetch Questions
    api.getVideoQuestions(videoId)
      .then(res => setQuestions(res.questions || []))
      .catch(err => console.error("Failed to load questions:", err))
      .finally(() => setLoadingQuestions(false));
      
  }, [videoId]);

  const embedUrl = `https://www.youtube.com/embed/${videoId}?autoplay=1&modestbranding=1&rel=0`;

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
            <div className="knowledge-panel-content">
              
              <section className="knowledge-section">
                <h2>Key Topics</h2>
                {loadingTopics ? (
                  <div className="knowledge-loading">Loading topics...</div>
                ) : (
                  <div className="knowledge-tags">
                    {topics.map((t, i) => (
                      <span key={i} className="knowledge-tag topic-tag">{t}</span>
                    ))}
                    {topics.length === 0 && <span className="knowledge-empty">No topics found.</span>}
                  </div>
                )}
              </section>

              <section className="knowledge-section">
                <h2>Questions You Can Ask</h2>
                {loadingQuestions ? (
                  <div className="knowledge-loading">Loading questions...</div>
                ) : (
                  <ul className="knowledge-query-list">
                    {questions.map((q, i) => (
                      <li key={i} className="knowledge-query-item">{q}</li>
                    ))}
                    {questions.length === 0 && <span className="knowledge-empty">No queries found.</span>}
                  </ul>
                )}
              </section>

              <section className="knowledge-section">
                <h2>Featured Stories</h2>
                {loadingDetails ? (
                  <div className="knowledge-loading">Loading stories...</div>
                ) : (
                  <div className="knowledge-story-list">
                    {details && details.stories && details.stories.length > 0 ? (
                      details.stories.map((story, i) => (
                        <div key={i} className="knowledge-story-card">
                          <h3>{story.title}</h3>
                          {story.moral && <p className="story-moral">"{story.moral}"</p>}
                        </div>
                      ))
                    ) : (
                      <span className="knowledge-empty">No stories available.</span>
                    )}
                  </div>
                )}
              </section>

            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default CinematicVideoPanel;
