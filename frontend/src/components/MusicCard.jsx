import React, { useState, useEffect, useRef } from 'react';
import './StoryCard.css'; // Reusing the exact same CSS as StoryCard
import './Music.css';

const MusicModal = ({ track, onClose, lang }) => {
  const [iframeLoaded, setIframeLoaded] = useState(false);
  const { video_id, start_time_seconds, name, name_english, type, saint, saint_english, exact_start_text } = track;

  const displayName = lang === 'en' && name_english ? name_english : name;
  const displaySaint = lang === 'en' && saint_english ? saint_english : saint;

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

  const [thumbSrc, setThumbSrc] = useState(`https://img.youtube.com/vi/${video_id}/hqdefault.jpg`);

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
            <h2 className="story-card-title" style={{ fontSize: '32px', marginBottom: '12px' }}>{displayName}</h2>
            {displaySaint && <span className="saint-tag">{displaySaint}</span>}
            <span className="story-topic-tag" style={{ marginLeft: '12px', textTransform: 'capitalize' }}>{type}</span>
          </div>

          {exact_start_text && (
            <div className="story-modal-info-right">
              <div className="modal-section-title">Lyrics / Excerpt</div>
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

const MusicCard = ({ track, lang }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  const { 
    name, 
    name_english,
    type,
    saint,
    saint_english,
    exact_start_text,
    video_id, 
    start_time_seconds,
  } = track;

  const displayName = lang === 'en' && name_english ? name_english : name;
  const displaySaint = lang === 'en' && saint_english ? saint_english : saint;

  const [thumbSrc, setThumbSrc] = useState(`https://img.youtube.com/vi/${video_id}/hqdefault.jpg`);

  const formatTime = (seconds) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <>
      <div className="ultra-music-card" onClick={() => setIsModalOpen(true)}>
        <div className="ultra-music-content">
          <div className="ultra-music-art-wrapper">
            <img 
              src={thumbSrc} 
              onError={() => {
                if (thumbSrc.includes('hqdefault')) setThumbSrc(`https://img.youtube.com/vi/${video_id}/mqdefault.jpg`);
                else if (thumbSrc.includes('mqdefault')) setThumbSrc(`https://img.youtube.com/vi/${video_id}/0.jpg`);
              }}
              alt={name} 
              className="ultra-music-art" 
            />
            <div className="ultra-play-overlay">
              <div className="ultra-play-button">▶</div>
            </div>
          </div>

          <div className="ultra-music-info">
            <h3 className="ultra-music-title">{displayName}</h3>
            
            <div className="ultra-music-meta">
              {displaySaint && <span className="ultra-pill">{displaySaint}</span>}
              <span className="ultra-pill highlight" style={{ textTransform: 'capitalize' }}>{type}</span>
              {start_time_seconds > 0 && (
                <span className="ultra-pill" style={{ opacity: 0.8, borderColor: 'transparent', background: 'transparent', padding: '0' }}>Starts at {formatTime(start_time_seconds)}</span>
              )}
            </div>
            
            {exact_start_text && (
              <div className="ultra-lyrics">
                "{exact_start_text}..."
              </div>
            )}
          </div>
        </div>
      </div>

      {isModalOpen && (
        <MusicModal track={track} onClose={() => setIsModalOpen(false)} lang={lang} />
      )}
    </>
  );
};

export default MusicCard;
