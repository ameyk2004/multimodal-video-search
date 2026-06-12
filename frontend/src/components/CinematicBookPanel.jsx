import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import './CinematicVideoPanel.css'; // Reuse cinematic layout CSS

const CinematicBookPanel = ({ bookSummary, initialTitle, onClose, onSearch, lang }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('summary');
  const [imageError, setImageError] = useState(false);
  const [entered, setEntered] = useState(false);

  const bookId = bookSummary.video_id;
  const initialTitleStr = initialTitle || bookSummary.title || "साहित्य";
  const coverUrl = `/books/${initialTitleStr}.jpg`;

  useEffect(() => {
    // Trigger entrance animation after mount
    requestAnimationFrame(() => {
      requestAnimationFrame(() => setEntered(true));
    });
  }, []);

  useEffect(() => {
    setLoading(true);
    api.getBookDetails(bookId)
      .then(res => {
        setDetails(res);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load book details:", err);
        setLoading(false);
      });
  }, [bookId]);

  return (
    <div className={`cinematic-overlay book-panel-entrance ${entered ? 'entered' : ''}`} onClick={onClose}>
      <div className={`cinematic-panel-container book-panel-container ${entered ? 'panel-entered' : ''}`} onClick={e => e.stopPropagation()}>
        <button className="cinematic-close-btn" onClick={onClose}>×</button>
        <div className="cinematic-layout book-layout">
          
          {/* LEFT: Book Cover / Info Display */}
          <div className="cinematic-player-section book-cover-section">
            <div className="cinematic-book-large-cover" style={!imageError ? { padding: 0, height: '100%', width: '100%' } : {}}>
              {!imageError && (
                <img 
                  src={coverUrl} 
                  alt={initialTitleStr} 
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                  onError={() => setImageError(true)}
                />
              )}
              {imageError && (
                <>
                  <span className="book-large-icon">📖</span>
                  <h1 className="cinematic-title">{initialTitleStr}</h1>
                  <p className="book-author-large">{details?.author || bookSummary.author || "अज्ञात"}</p>
                </>
              )}
            </div>
            <div className="cinematic-player-info book-meta-info">
               {details?.mood && <span className="book-mood-badge">{details.mood}</span>}
               {details?.structure_type && <span className="book-structure-badge">{details.structure_type.replace('_', ' ')}</span>}
            </div>
          </div>

          {/* RIGHT: Scrollable Knowledge Panel */}
          <div className="cinematic-knowledge-panel">
            <div className="knowledge-tabs">
              <button className={`k-tab ${activeTab === 'summary' ? 'active' : ''}`} onClick={() => setActiveTab('summary')}>Summary & Learnings</button>
              <button className={`k-tab ${activeTab === 'index' ? 'active' : ''}`} onClick={() => setActiveTab('index')}>Index</button>
              <button className={`k-tab ${activeTab === 'questions' ? 'active' : ''}`} onClick={() => setActiveTab('questions')}>Questions</button>
              <button className={`k-tab ${activeTab === 'topics' ? 'active' : ''}`} onClick={() => setActiveTab('topics')}>Topics</button>
            </div>
            
            <div className="knowledge-panel-content">
              {loading ? (
                <div className="knowledge-loading">Loading book details...</div>
              ) : (
                <>
                  {activeTab === 'summary' && (
                    <>
                      <section className="knowledge-section">
                        <h2>सारांश (Summary)</h2>
                        <p className="book-summary-text">{details?.summary || "No summary available."}</p>
                      </section>

                      {details?.for_whom && (
                        <section className="knowledge-section">
                          <h2>कोणासाठी उपयुक्त? (For Whom)</h2>
                          <p className="book-for-whom-text">{details.for_whom}</p>
                        </section>
                      )}

                      <section className="knowledge-section">
                        <h2>महत्त्वाच्या शिकवणी (Key Learnings)</h2>
                        <ul className="knowledge-practice-list">
                          {details?.key_learnings?.map((k, i) => (
                            <li key={i} className="knowledge-practice-item">{k}</li>
                          ))}
                          {(!details?.key_learnings || details.key_learnings.length === 0) && (
                            <span className="knowledge-empty">No key learnings found.</span>
                          )}
                        </ul>
                      </section>
                      
                      <section className="knowledge-section" style={{ marginTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '15px' }}>
                        <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.95rem' }}>
                          <strong>लेखक/संकलक:</strong> {details?.author || bookSummary.author || "अज्ञात"}
                        </p>
                      </section>
                    </>
                  )}

                  {activeTab === 'index' && (
                    <section className="knowledge-section">
                      <h2>Index</h2>
                      <p className="questions-helper">विशिष्ट अध्यायावर जाण्यासाठी खालीलपैकी एकावर क्लिक करा.</p>
                      <ul className="book-index-list">
                        {details?.table_of_contents?.map((item, i) => (
                          <li 
                            key={i} 
                            className="book-index-item clickable"
                            onClick={() => { 
                              if (onSearch) {
                                onSearch({
                                  type: 'fetch_page',
                                  bookName: bookSummary.title || initialTitleStr,
                                  pageNumber: item.page,
                                  chapterTitle: item.title
                                });
                              }
                            }}
                          >
                            <span className="book-index-title">{item.title}</span>
                            <span className="book-index-page">पान {item.page}</span>
                          </li>
                        ))}
                        {(!details?.table_of_contents || details.table_of_contents.length === 0) && (
                          <span className="knowledge-empty">या पुस्तकाची अनुक्रमणिका उपलब्ध नाही.</span>
                        )}
                      </ul>
                    </section>
                  )}

                  {activeTab === 'questions' && (
                    <section className="knowledge-section">
                      <h2>Questions You Can Ask</h2>
                      <p className="questions-helper">या पुस्तकातून तुम्हाला पडणारे संभाव्य प्रश्न (क्लिक करा)</p>
                      <ul className="knowledge-query-list">
                        {details?.questions?.map((q, i) => (
                          <li 
                            key={i} 
                            className={`knowledge-query-item ${onSearch ? 'clickable' : ''} ${i===0 ? 'primary-query' : ''}`}
                            onClick={() => { if (onSearch) onSearch(q); }}
                          >
                            {i===0 && <span className="primary-badge">★</span>} {q}
                          </li>
                        ))}
                        {(!details?.questions || details.questions.length === 0) && (
                          <span className="knowledge-empty">No questions found.</span>
                        )}
                      </ul>
                    </section>
                  )}

                  {activeTab === 'topics' && (
                    <section className="knowledge-section">
                      <h2>Key Topics</h2>
                      <div className="knowledge-tags">
                        {details?.topics?.map((t, i) => (
                          <span key={i} className="knowledge-tag topic-tag">{t}</span>
                        ))}
                        {(!details?.topics || details.topics.length === 0) && (
                          <span className="knowledge-empty">No topics found.</span>
                        )}
                      </div>
                    </section>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CinematicBookPanel;
