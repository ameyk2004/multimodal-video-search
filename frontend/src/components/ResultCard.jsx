import { useState } from 'react';
import { formatTime, ytThumb } from '../utils';
import BookResultCard from './BookResultCard';
import { usePlayer, resultToItem } from '../context/PlayerContext';
import './MiniPlayer.css';

export default function ResultCard({ result, rank, style, isMarathi, query, onSearch, playingVideoId, setPlayingVideoId }) {
  const [isTextExpanded, setIsTextExpanded] = useState(false);
  const { play, addToQueue } = usePlayer();

  const { video_id, start_time, marathi_raw, score } = result;
  const currentId = `${video_id}-${start_time}`;
  const isPlaying = playingVideoId === currentId;
  const setIsPlaying = (play) => {
    if (setPlayingVideoId) {
      setPlayingVideoId(play ? currentId : null);
    }
  };

  const timeLabel = formatTime(start_time);
  const pct = Math.round(score * 100);

  const showFullText = isTextExpanded || result.type === 'book';
  const lang = isMarathi ? 'mr' : 'en';

  const handlePlayClick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    play(resultToItem(result, query));
  };

  const handleAddToQueue = (e) => {
    e.preventDefault();
    e.stopPropagation();
    addToQueue(resultToItem(result, query));
  };

  if (result.type === 'book') {
    return <BookResultCard result={result} isMarathi={isMarathi} style={style} query={query} />;
  }

  return (
    <div className={`result-card ${isPlaying ? 'expanded' : 'collapsed'}`} style={style}>

      {/* Media Section */}
      <div className="media-section">
        {/* Use <button> so mobile first-tap fires click immediately (no ghost hover) */}
        <button
          className="thumbnail-wrapper"
          onClick={handlePlayClick}
          style={{ display: 'block', width: '100%', border: 'none', background: 'none', cursor: 'pointer', position: 'relative' }}
          aria-label={`Play video at ${timeLabel}`}
        >
          <img
            src={ytThumb(video_id)}
            alt="Video Thumbnail"
            className="video-thumb"
            loading="lazy"
            onError={(e) => {
              if (e.target.src.includes('mqdefault')) {
                e.target.src = `https://img.youtube.com/vi/${video_id}/0.jpg`;
              }
            }}
          />
          <div className="play-overlay">
            <span className="play-btn">▶</span>
          </div>
          <div className="thumb-time-badge">{timeLabel}</div>
        </button>
      </div>

      {/* Content Section */}
      <div className="card-content">
        <div className="card-header">
          <div className="relevance-group" style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <span className="relevance-badge">
              <span className="sparkle">✧</span> {isMarathi ? `सुसंगतता: ${pct}%` : `Relevance: ${pct}%`}
            </span>
            {/* Queue button */}
            <button
              className="queue-action-btn"
              title={isMarathi ? 'रांगेत जोडा' : 'Add to Queue'}
              onClick={handleAddToQueue}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M14 10H2v2h12v-2zm0-4H2v2h12V6zm4 8v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zM2 16h8v-2H2v2z"/>
              </svg>
            </button>
            {/* Share button */}
            <button
              className="share-action-btn"
              title={isMarathi ? 'शेअर करा' : 'Share'}
              onClick={(e) => {
                e.stopPropagation();
                const ytLink = `https://youtu.be/${video_id}?t=${Math.floor(start_time)}`;
                const text = `Check out this answer to "${query}":\n\n${ytLink}`;
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

        <div className="text-content">
          <div className={`marathi-text ${!showFullText ? 'clamped-text' : ''}`}>
            {marathi_raw}
          </div>

          {!showFullText && (
            <button className="view-more-btn" onClick={() => setIsTextExpanded(true)}>
              {isMarathi ? 'अधिक वाचा ▼' : 'View More ▼'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
