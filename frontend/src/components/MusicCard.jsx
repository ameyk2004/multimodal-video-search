import React, { useState } from 'react';
import { usePlayer, trackToItem } from '../context/PlayerContext';
import './StoryCard.css'; // Reusing the exact same CSS as StoryCard
import './Music.css';
import './MiniPlayer.css';

const MusicCard = ({ track, lang, badgeText }) => {
  const { play, addToQueue } = usePlayer();

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

  const handlePlay = (e) => {
    e.stopPropagation();
    play(trackToItem(track));
  };

  const handleAddToQueue = (e) => {
    e.stopPropagation();
    addToQueue(trackToItem(track));
  };

  return (
    <div className="ultra-music-card" onClick={handlePlay}>
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
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }} onClick={e => e.stopPropagation()}>
              {/* Add to queue */}
              <button
                className="queue-action-btn"
                title={lang === 'mr' ? 'रांगेत जोडा' : 'Add to Queue'}
                onClick={handleAddToQueue}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M14 10H2v2h12v-2zm0-4H2v2h12V6zm4 8v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zM2 16h8v-2H2v2z"/>
                </svg>
              </button>
              {/* Share */}
              <button
                className="share-action-btn"
                title={lang === 'mr' ? 'शेअर करा' : 'Share'}
                onClick={(e) => {
                  e.stopPropagation();
                  const durationText = durationSeconds > 0 ? `\nDuration: ${formatTime(durationSeconds)}` : '';
                  const ytLink = `https://youtu.be/${video_id}?t=${Math.floor(start_time_seconds || 0)}`;
                  const text = `Listen to this abhang: "${displayName}"${durationText}\n\n${ytLink}`;
                  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
                }}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" stroke="currentColor">
                  <circle cx="18" cy="5" r="3"></circle>
                  <circle cx="6" cy="12" r="3"></circle>
                  <circle cx="18" cy="19" r="3"></circle>
                  <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
                  <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
                </svg>
              </button>
            </div>
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
  );
};

export default MusicCard;
