import React, { useState, useEffect } from 'react';
import './StoryCard.css';

const StoryModal = ({ story, onClose }) => {
  const [iframeLoaded, setIframeLoaded] = useState(false);
  const { video_id, start_time_seconds, title, moral, character_or_saint, exact_start_text } = story;

  // Prevent background scrolling when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      document.body.style.overflow = 'auto';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const fallbackThumbnailUrl = `https://img.youtube.com/vi/${video_id}/mqdefault.jpg`;
  const thumbUrl = story.thumbnail_url || fallbackThumbnailUrl;

  return (
    <div className="story-modal-overlay" onClick={onClose}>
      <div className="story-modal-content" onClick={e => e.stopPropagation()}>
        <button className="story-modal-close" onClick={onClose}>×</button>
        
        <div className="story-modal-video">
          {!iframeLoaded && (
            <div className="video-loading-placeholder" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#000', overflow: 'hidden' }}>
              <img src={thumbUrl} alt="Loading..." style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.35)', position: 'absolute' }} />
              <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)' }}></div>
              <div className="energy-ring" style={{ position: 'relative', zIndex: 2, marginBottom: '16px' }}></div>
              <span style={{ position: 'relative', zIndex: 2, color: '#fff', fontSize: '18px', fontWeight: 600, letterSpacing: '0.5px' }}>व्हिडिओ लोड होत आहे...</span>
            </div>
          )}
          <iframe
            src={`https://www.youtube.com/embed/${video_id}?autoplay=1&start=${Math.floor(start_time_seconds || 0)}`}
            title="YouTube video player"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            onLoad={() => setIframeLoaded(true)}
            style={{ opacity: iframeLoaded ? 1 : 0, transition: 'opacity 0.5s ease', width: '100%', height: '100%', position: 'absolute', inset: 0 }}
          ></iframe>
        </div>

        <div className="story-modal-info">
          <div className="story-modal-info-left">
            <h2 className="story-card-title" style={{ fontSize: '32px', marginBottom: '12px' }}>{title}</h2>
            {character_or_saint && <span className="saint-tag">{character_or_saint}</span>}
            
            {moral && (
              <div style={{ marginTop: '24px' }}>
                <div className="modal-section-title">Teaching / Moral</div>
                <div className="story-card-moral" style={{ fontSize: '20px', margin: 0 }}>
                  {moral}
                </div>
              </div>
            )}
          </div>

          {exact_start_text && (
            <div className="story-modal-info-right">
              <div className="modal-section-title">Transcript Excerpt</div>
              <div className="modal-content-text">
                "{exact_start_text}..."
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const StoryCard = ({ story }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { 
    title, 
    moral, 
    character_or_saint, 
    exact_start_text,
    video_id, 
    start_time_seconds,
    thumbnail_url
  } = story;

  const fallbackThumbnailUrl = `https://img.youtube.com/vi/${video_id}/hqdefault.jpg`;
  const thumbUrl = thumbnail_url || fallbackThumbnailUrl;

  const formatTime = (seconds) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <>
      <div className="premium-story-card" onClick={() => setIsModalOpen(true)}>
        <div className="story-card-left">
          <img 
            src={thumbUrl} 
            onError={(e) => { e.target.onerror = null; e.target.src = fallbackThumbnailUrl; }}
            alt={title} 
            className="story-card-thumb" 
          />
          <div className="story-card-overlay"></div>
          <div className="story-card-play-hover">
            <div className="story-card-play-btn">▶</div>
          </div>
        </div>

        <div className="story-card-center">
          <div className="story-card-top-row">
            <div className="story-card-meta">
              {character_or_saint && <span className="saint-tag">{character_or_saint}</span>}
              {start_time_seconds > 0 && (
                <span className="time-tag">Starts at {formatTime(start_time_seconds)}</span>
              )}
            </div>
            
            <div className="story-card-actions" onClick={(e) => e.stopPropagation()}>
              <button className="btn-inline-play" onClick={() => setIsModalOpen(true)}>
                ▶ Play Story
              </button>
            </div>
          </div>
          
          <h3 className="story-card-title">{title}</h3>
          
          {moral && (
            <div className="story-card-moral">
              {moral}
            </div>
          )}
          
          {exact_start_text && (
            <div className="story-card-preview">
              "{exact_start_text}..."
            </div>
          )}
        </div>
      </div>

      {isModalOpen && (
        <StoryModal story={story} onClose={() => setIsModalOpen(false)} />
      )}
    </>
  );
};

export default StoryCard;
