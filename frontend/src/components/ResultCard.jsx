import { useState } from 'react';
import { formatTime, ytEmbedUrl, ytThumb } from '../utils';
import BookResultCard from './BookResultCard';

export default function ResultCard({ result, rank, style, isMarathi, query, onSearch, playingVideoId, setPlayingVideoId }) {
  const [isTextExpanded, setIsTextExpanded] = useState(false);
  
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

  // Auto-expand text when video is playing
  const showFullText = isPlaying || isTextExpanded || result.type === 'book';

  const lang = isMarathi ? 'mr' : 'en';

  if (result.type === 'book') {
    return <BookResultCard result={result} isMarathi={isMarathi} style={style} query={query} />;
  }

  return (
    <div className={`result-card ${isPlaying ? 'expanded' : 'collapsed'}`} style={style}>
      
      {/* Media Section */}
      <div className="media-section">
        {!isPlaying ? (
          <div className="thumbnail-wrapper" onClick={() => setIsPlaying(true)}>
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
              <button className="play-btn">▶</button>
            </div>
            <div className="thumb-time-badge">{timeLabel}</div>
          </div>
        ) : (
          <div className="video-wrapper">
            <iframe
              src={ytEmbedUrl(video_id, start_time)}
              title={`Video ${video_id}`}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          </div>
        )}
      </div>

      {/* Content Section */}
      <div className="card-content">
        <div className="card-header">
          <div className="relevance-group" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span className="relevance-badge">
              <span className="sparkle">✧</span> {isMarathi ? `सुसंगतता: ${pct}%` : `Relevance: ${pct}%`}
            </span>
            <button 
              className="share-action-btn" 
              title={isMarathi ? 'शेअर करा' : 'Share'}
              onClick={(e) => {
                e.stopPropagation();
                const ytLink = `https://youtu.be/${video_id}?t=${start_time}`;
                const text = `Check out this answer to "${query}":\n\n${ytLink}`;
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
          {isPlaying && (
            <button className="close-video-btn" onClick={() => setIsPlaying(false)}>
              ✕ {isMarathi ? 'बंद करा' : 'Close Player'}
            </button>
          )}
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
