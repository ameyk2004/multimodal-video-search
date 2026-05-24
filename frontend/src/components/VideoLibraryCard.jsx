import React, { useState, useEffect } from 'react';
import './Library.css';

export default function VideoLibraryCard({ video, onClick }) {
  const [youtubeTitle, setYoutubeTitle] = useState('');
  
  useEffect(() => {
    // Fetch real title dynamically using OEmbed
    const fetchTitle = async () => {
      try {
        const res = await fetch(`https://noembed.com/embed?url=https://www.youtube.com/watch?v=${video.video_id}`);
        const data = await res.json();
        if (data.title) {
          setYoutubeTitle(data.title);
        } else {
          setYoutubeTitle(`प्रवचन ${video.video_id}`);
        }
      } catch (err) {
        setYoutubeTitle(`प्रवचन ${video.video_id}`);
      }
    };
    fetchTitle();
  }, [video.video_id]);

  return (
    <div className="video-library-card" onClick={() => onClick(youtubeTitle)}>
      <div className="library-card-thumb-container">
        <img 
          src={`https://img.youtube.com/vi/${video.video_id}/hqdefault.jpg`} 
          onError={(e) => { 
            const currentSrc = e.target.src;
            if (currentSrc.includes('hqdefault')) {
              e.target.src = `https://img.youtube.com/vi/${video.video_id}/mqdefault.jpg`;
            } else if (currentSrc.includes('mqdefault')) {
              e.target.src = `https://img.youtube.com/vi/${video.video_id}/0.jpg`;
            }
          }}
          alt={youtubeTitle} 
          className="library-card-thumb" 
        />
        <div className="library-card-overlay">
          <div className="library-card-content">
            <h3 className="library-card-title">{youtubeTitle || 'Loading...'}</h3>
            <div className="library-card-meta">
              <span>{video.topic_count} Topics</span>
              <span className="meta-dot">•</span>
              <span>{video.query_count} Questions</span>
            </div>
          </div>
          <div className="play-overlay">
            <div className="play-icon">▶</div>
          </div>
        </div>
      </div>
    </div>
  );
}
