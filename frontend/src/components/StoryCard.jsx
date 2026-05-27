import React, { useState, useEffect, useRef } from 'react';
import './StoryCard.css';

const StoryModal = ({ story, onClose, lang }) => {
  const [iframeLoaded, setIframeLoaded] = useState(false);
  const { video_id, start_time_seconds, title, title_english, moral, character_or_saint, normalized_saint_name, normalized_saint_name_english, associated_topics, exact_start_text } = story;

  const displayTitle = lang === 'en' && title_english ? title_english : title;
  const displaySaint = lang === 'en' && normalized_saint_name_english ? normalized_saint_name_english : (normalized_saint_name || character_or_saint);

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

  const [thumbSrc, setThumbSrc] = useState(story.thumbnail_url || `https://img.youtube.com/vi/${video_id}/hqdefault.jpg`);

  return (
    <div className="story-modal-overlay" onClick={onClose}>
      <div className="story-modal-content" onClick={e => e.stopPropagation()}>
        <button className="story-modal-close" onClick={onClose}>×</button>
        
        <div className="story-modal-video">
          {!iframeLoaded && (
            <div className="video-loading-placeholder" style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#000', overflow: 'hidden' }}>
              <img 
                src={thumbSrc} 
                alt="Loading..." 
                style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scale(1.35)', position: 'absolute' }} 
                onError={() => {
                  if (thumbSrc.includes('hqdefault')) setThumbSrc(`https://img.youtube.com/vi/${video_id}/mqdefault.jpg`);
                  else if (thumbSrc.includes('mqdefault')) setThumbSrc(`https://img.youtube.com/vi/${video_id}/0.jpg`);
                }}
              />
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
            <h2 className="story-card-title" style={{ fontSize: '32px', marginBottom: '12px' }}>{displayTitle}</h2>
            {displaySaint && <span className="saint-tag">{displaySaint}</span>}
            
            {associated_topics && associated_topics.length > 0 && (
              <div className="story-card-topics" style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {associated_topics.map((t, i) => <span key={i} className="story-topic-tag">{t}</span>)}
              </div>
            )}
            
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

const StoryCard = ({ story, autoOpen, lang }) => {
  const [isModalOpen, setIsModalOpen] = useState(autoOpen || false);
  const [isExpanded, setIsExpanded] = useState(false);
  const cardRef = useRef(null);

  useEffect(() => {
    if (autoOpen) {
      setIsModalOpen(true);
      if (cardRef.current) {
        setTimeout(() => {
          cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 500); // Wait for page transition
      }
    }
  }, [autoOpen]);
  const { 
    title,
    title_english, 
    moral, 
    character_or_saint, 
    normalized_saint_name,
    normalized_saint_name_english,
    associated_topics,
    exact_start_text,
    video_id, 
    start_time_seconds,
    thumbnail_url
  } = story;

  const displayTitle = lang === 'en' && title_english ? title_english : title;
  const displaySaint = lang === 'en' && normalized_saint_name_english ? normalized_saint_name_english : (normalized_saint_name || character_or_saint);

  const [thumbSrc, setThumbSrc] = useState(thumbnail_url || `https://img.youtube.com/vi/${video_id}/hqdefault.jpg`);

  const formatTime = (seconds) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <>
      <div className="premium-story-card" onClick={() => setIsModalOpen(true)} ref={cardRef}>
        <div className="story-card-left">
          <img 
            src={thumbSrc} 
            onError={() => {
              if (thumbSrc.includes('hqdefault')) setThumbSrc(`https://img.youtube.com/vi/${video_id}/mqdefault.jpg`);
              else if (thumbSrc.includes('mqdefault')) setThumbSrc(`https://img.youtube.com/vi/${video_id}/0.jpg`);
            }}
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
              {displaySaint && <span className="saint-tag">{displaySaint}</span>}
              {start_time_seconds > 0 && (
                <span className="time-tag">Starts at {formatTime(start_time_seconds)}</span>
              )}
            </div>
            
            {associated_topics && associated_topics.length > 0 && (
              <div className="story-card-topics" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '4px' }}>
                {associated_topics.map((t, i) => <span key={i} className="story-topic-tag">{t}</span>)}
              </div>
            )}
            
            <div className="story-card-actions" onClick={(e) => e.stopPropagation()}>
              <button className="btn-inline-play" onClick={() => setIsModalOpen(true)}>
                ▶ Play Story
              </button>
            </div>
          </div>
          
          <h3 className="story-card-title">{displayTitle}</h3>
          
          {moral && (
            <div className="story-card-moral">
              <div className={isExpanded ? "" : "clamped-text-2"}>
                {moral}
              </div>
              <button 
                className="view-more-btn-text" 
                onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }}
                style={{ background: 'none', border: 'none', color: 'var(--saffron)', fontSize: '14px', cursor: 'pointer', padding: '4px 0 0', fontWeight: '500' }}
              >
                {isExpanded ? "View Less" : "Read More"}
              </button>
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
        <StoryModal story={story} onClose={() => setIsModalOpen(false)} lang={lang} />
      )}
    </>
  );
};

export default StoryCard;
