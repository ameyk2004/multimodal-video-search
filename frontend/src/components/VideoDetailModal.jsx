import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import './Library.css';

export default function VideoDetailModal({ video, initialTitle, onClose }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [showAllTopics, setShowAllTopics] = useState(false);
  const [showAllQueries, setShowAllQueries] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const fetchDetails = async () => {
      try {
        const data = await api.getVideoDetails(video.video_id);
        if (isMounted) {
          setDetails(data);
          setLoading(false);
        }
      } catch (err) {
        console.error(err);
        if (isMounted) setLoading(false);
      }
    };
    fetchDetails();
    return () => { isMounted = false; };
  }, [video.video_id]);

  if (!video) return null;

  return (
    <div className="library-modal-overlay" onClick={onClose}>
      <div className="library-modal-content" onClick={e => e.stopPropagation()}>
        <button className="library-modal-close" onClick={onClose}>×</button>
        
        <div className="library-modal-video-container">
          <iframe
            src={`https://www.youtube.com/embed/${video.video_id}`}
            title="YouTube video player"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          ></iframe>
        </div>
        
        <div className="library-modal-body">
          <h2 className="library-modal-title">{initialTitle || "प्रवचन"}</h2>
          
          {loading ? (
            <div className="library-modal-loading">
              <div className="energy-ring" style={{ width: '30px', height: '30px' }}/>
              <span>Loading details...</span>
            </div>
          ) : details ? (
            <div className="library-modal-sections">
              
              {/* Topics Section */}
              {details.topics && details.topics.length > 0 && (
                <div className="library-modal-section">
                  <h3>Topics Covered</h3>
                  <div className="library-pill-container">
                    {(showAllTopics ? details.topics : details.topics.slice(0, 5)).map((topic, i) => (
                      <span key={i} className="library-pill topic-pill">{topic}</span>
                    ))}
                  </div>
                  {details.topics.length > 5 && (
                    <button className="library-view-more" onClick={() => setShowAllTopics(!showAllTopics)}>
                      {showAllTopics ? "Show Less Topics" : `View ${details.topics.length - 5} More Topics`}
                    </button>
                  )}
                </div>
              )}

              {/* Queries Section */}
              {details.queries && details.queries.length > 0 && (
                <div className="library-modal-section">
                  <h3>Sample Questions</h3>
                  <div className="library-queries-list">
                    {(showAllQueries ? details.queries : details.queries.slice(0, 5)).map((q, i) => (
                      <div key={i} className="library-query-item">
                        <span className="query-icon">?</span>
                        <p>{q}</p>
                      </div>
                    ))}
                  </div>
                  {details.queries.length > 5 && (
                    <button className="library-view-more" onClick={() => setShowAllQueries(!showAllQueries)}>
                      {showAllQueries ? "Show Less Questions" : `View ${details.queries.length - 5} More Questions`}
                    </button>
                  )}
                </div>
              )}

            </div>
          ) : (
            <p>Failed to load details.</p>
          )}
        </div>
      </div>
    </div>
  );
}
