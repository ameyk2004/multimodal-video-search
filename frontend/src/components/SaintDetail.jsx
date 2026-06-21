import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import StoryCard from './StoryCard';
import './SaintDetail.css';

import { api } from '../utils/api';

export default function SaintDetail({ allStories }) {
  const { saintId } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('life');
  const heroRef = useRef(null);
  
  const [saint, setSaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const decodedName = decodeURIComponent(saintId);

  useEffect(() => {
    api.getSaintDetails(decodedName)
      .then(data => {
        setSaint(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch saint details:", err);
        setLoading(false);
      });
  }, [decodedName]);

  // Use the API stories, or fallback to frontend passed allStories if API not providing them
  const saintStories = saint?.stories || [];
  const saintMusic = saint?.music || [];

  // Consistent index for placeholder image mapping
  const hashString = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash += str.charCodeAt(i);
    return hash;
  };
  const image = `/assets/placeholders/${['meditating', 'veena', 'books', 'namaste', 'dholak', 'staff'][hashString(decodedName) % 6]}.png`;

  // Parallax effect on scroll
  useEffect(() => {
    const handleScroll = () => {
      if (heroRef.current) {
        const scrollY = window.scrollY;
        // Move background down slowly and scale it slightly
        heroRef.current.style.transform = `translateY(${scrollY * 0.3}px) scale(${1 + scrollY * 0.0005})`;
        heroRef.current.style.opacity = 1 - scrollY * 0.002;
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="saint-detail-page">
      <button className="back-btn" onClick={() => navigate('/saints')}>
        <span>←</span> Back to Saints
      </button>

      {loading ? (
        <div className="loading-spinner" style={{marginTop: '100px', color: 'white', textAlign: 'center'}}>Loading {decodedName}...</div>
      ) : !saint ? (
        <div className="empty-state" style={{marginTop: '100px', color: 'white', textAlign: 'center'}}>Saint not found.</div>
      ) : (
        <>

      {/* Sanctum Hero */}
      <div className="sanctum-hero-container">
        <div className="sanctum-particles"></div>
        <div className="sanctum-hero-bg" ref={heroRef} style={{ backgroundImage: `url(${image})` }}></div>
        <div className="sanctum-hero-overlay"></div>
        
        <div className="sanctum-hero-content">
          <div className="sanctum-portrait-ring">
            <img src={image} alt={saint.name} className="sanctum-portrait" />
          </div>
          <h1 className="sanctum-title">{saint.name}</h1>
          <div className="sanctum-meta">
            <span className="sanctum-tradition">{saint.tradition}</span>
            <span className="sanctum-era">{saint.era}</span>
          </div>
          <p className="sanctum-quote">"{saint.quote}"</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="sanctum-tabs-wrapper">
        <div className="sanctum-tabs">
          <button className={`sanctum-tab ${activeTab === 'life' ? 'active' : ''}`} onClick={() => setActiveTab('life')}>Life & Teachings</button>
          <button className={`sanctum-tab ${activeTab === 'stories' ? 'active' : ''}`} onClick={() => setActiveTab('stories')}>Stories ({saintStories.length})</button>
          <button className={`sanctum-tab ${activeTab === 'bhajans' ? 'active' : ''}`} onClick={() => setActiveTab('bhajans')}>Bhajans</button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="sanctum-content-area">
        {activeTab === 'life' && (
          <div className="sanctum-tab-pane fade-in">
            <h2>Key Teachings</h2>
            <div className="teachings-grid">
              {saint.learnings && saint.learnings.length > 0 ? saint.learnings.map((teaching, i) => (
                <div key={i} className="teaching-card">
                  <div className="teaching-icon">✨</div>
                  <p>{teaching}</p>
                </div>
              )) : (
                <p style={{color: 'rgba(255,255,255,0.7)'}}>No specific teachings documented yet.</p>
              )}
            </div>
            
            <div className="biography-section">
              <h2>Biography</h2>
              <p className="bio-text">
                {saint.fullBio || `Immersion in the stories and teachings of ${saint.name} will reveal the true depth of their spiritual journey.`}
              </p>
            </div>
          </div>
        )}

        {activeTab === 'stories' && (
          <div className="sanctum-tab-pane fade-in">
            <div className="sanctum-stories-list">
              {saintStories.length > 0 ? (
                saintStories.map((story, i) => (
                  <StoryCard key={i} story={story} lang="en" />
                ))
              ) : (
                <div className="empty-state">
                  <p>No specific stories found for {saint.name} yet.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'bhajans' && (
          <div className="sanctum-tab-pane fade-in">
            {saintMusic.length > 0 ? (
              <div className="sanctum-stories-list">
                {saintMusic.map((music, i) => (
                  <div key={i} className="music-item" style={{background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '10px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <div>
                      <h4 style={{margin: '0 0 5px 0'}}>{music.name}</h4>
                      <p style={{margin: '0', fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)'}}>{music.type}</p>
                    </div>
                    <a href={`https://www.youtube.com/watch?v=${music.video_id}&t=${music.start_time_seconds}s`} target="_blank" rel="noopener noreferrer" style={{color: '#ff9a00', textDecoration: 'none'}}>Play →</a>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>Bhajans and musical compositions for {saint.name} will be available soon.</p>
              </div>
            )}
          </div>
        )}
      </div>
      </>
      )}
    </div>
  );
}
