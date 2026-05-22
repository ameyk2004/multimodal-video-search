import React, { useState } from 'react';
import './StoryCard.css';

const StoryCard = ({ story }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const { title, content, video_id, start_time_seconds } = story;

  const thumbnailUrl = `https://img.youtube.com/vi/${video_id}/maxresdefault.jpg`;
  const fallbackThumbnailUrl = `https://img.youtube.com/vi/${video_id}/hqdefault.jpg`;

  const handlePlay = () => {
    setIsPlaying(true);
  };

  const formatTime = (seconds) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="story-card-playable">
      <div className="story-media-section">
        {!isPlaying ? (
          <div className="story-thumbnail-wrapper" onClick={handlePlay}>
            <img 
              src={thumbnailUrl} 
              onError={(e) => { e.target.onerror = null; e.target.src = fallbackThumbnailUrl; }}
              alt={title} 
              className="story-video-thumb" 
            />
            <div className="story-play-overlay">
              <button className="story-play-btn">▶</button>
            </div>
            {start_time_seconds > 0 && (
              <span className="story-thumb-time-badge">
                Start: {formatTime(start_time_seconds)}
              </span>
            )}
          </div>
        ) : (
          <div className="story-video-wrapper">
            <iframe
              src={`https://www.youtube.com/embed/${video_id}?autoplay=1&start=${Math.floor(start_time_seconds || 0)}`}
              title="YouTube video player"
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            ></iframe>
          </div>
        )}
      </div>

      <div className="story-card-content-playable">
        <div className="story-header-playable">
          <h3>{title}</h3>
        </div>
        <div className="story-text-playable">
          <p>{content}</p>
        </div>
      </div>
    </div>
  );
};

export default StoryCard;
