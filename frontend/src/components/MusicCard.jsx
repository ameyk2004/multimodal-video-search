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
            src={`https://www.youtube.com/embed/${video_id}?autoplay=1&start=${Math.floor(start_time_seconds || 0)}${track.end_time_seconds > start_time_seconds ? `&end=${Math.ceil(track.end_time_seconds)}` : ''}`}
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

const MusicCard = ({ track, lang, badgeText }) => {
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
    end_time_seconds,
  } = track;

  const durationSeconds = end_time_seconds > start_time_seconds ? end_time_seconds - start_time_seconds : 0;

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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 className="ultra-music-title" style={{ margin: 0 }}>{displayName}</h3>
              <button 
                className="share-action-btn" 
                title={lang === 'mr' ? 'शेअर करा' : 'Share'}
                onClick={(e) => {
                  e.stopPropagation();
                  const ytLink = `https://youtu.be/${video_id}?t=${Math.floor(start_time_seconds || 0)}`;
                  const text = `Listen to this abhang: "${displayName}"\n\n${ytLink}`;
                  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="18" cy="5" r="3"></circle>
                  <circle cx="6" cy="12" r="3"></circle>
                  <circle cx="18" cy="19" r="3"></circle>
                  <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                  <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                </svg>
              </button>
            </div>
            
            <div className="ultra-music-meta" style={{ marginTop: '8px' }}>
              {displaySaint && <span className="ultra-pill">{displaySaint}</span>}
              <span className="ultra-pill highlight" style={{ textTransform: 'capitalize' }}>{type}</span>
              {start_time_seconds > 0 && (
                <span className="ultra-pill" style={{ opacity: 0.8, borderColor: 'transparent', background: 'transparent', padding: '0' }}>Starts at {formatTime(start_time_seconds)}</span>
              )}
              {durationSeconds > 0 && (
                <span className="ultra-pill" style={{ background: 'rgba(255, 170, 0, 0.2)', color: 'var(--saffron)', borderColor: 'var(--saffron)', fontWeight: 'bold' }}>
                  Duration: {formatTime(durationSeconds)}
                </span>
              )}
              {badgeText && (
                <span className="ultra-pill" style={{ background: 'linear-gradient(135deg, #FFD700, #FFA500)', color: '#000', fontWeight: 'bold', border: 'none', boxShadow: '0 2px 10px rgba(255,170,0,0.3)', padding: '4px 12px' }}>
                  {badgeText}
                </span>
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
