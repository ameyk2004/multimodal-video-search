import { useState } from 'react';
import { formatTime, ytEmbedUrl, ytThumb } from '../utils';

export default function ResultCard({ result, rank, style, isMarathi }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTextExpanded, setIsTextExpanded] = useState(false);
  
  const { video_id, start_time, marathi_raw, score } = result;
  
  const timeLabel = formatTime(start_time);
  const pct = Math.round(score * 100);

  // Auto-expand text when video is playing
  const showFullText = isPlaying || isTextExpanded;

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
          <span className="relevance-badge">
            <span className="sparkle">✧</span> {isMarathi ? `सुसंगतता: ${pct}%` : `Relevance: ${pct}%`}
          </span>
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
