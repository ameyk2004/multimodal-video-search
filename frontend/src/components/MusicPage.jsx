import React, { useState, useEffect, useMemo } from 'react';
import { api } from '../utils/api';
import MusicCard from './MusicCard';
import MusicBanner from './MusicBanner';
import './Music.css';

export default function MusicPage({ lang }) {
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('सर्व');
  const [saintFilter, setSaintFilter] = useState('सर्व');
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  
  // Player State
  const [playingTrack, setPlayingTrack] = useState(null);

  useEffect(() => {
    api.getMusic()
      .then(data => {
        if (data.segments) {
          setSegments(data.segments);
        }
      })
      .catch(err => {
        console.error("Failed to load music", err);
        setError("Failed to load music library.");
      })
      .finally(() => setLoading(false));
  }, []);

  // Unique lists for dropdowns
  const uniqueTypes = useMemo(() => {
    const types = new Set(segments.map(s => s.type));
    return Array.from(types).sort();
  }, [segments]);

  const uniqueSaints = useMemo(() => {
    const saints = new Set(segments.map(s => s.saint).filter(Boolean));
    return Array.from(saints).sort();
  }, [segments]);

  // Filtered segments
  const filteredSegments = useMemo(() => {
    return segments.filter(s => {
      if (typeFilter !== 'सर्व' && s.type !== typeFilter) return false;
      if (saintFilter !== 'सर्व' && s.saint !== saintFilter) return false;
      
      if (searchQuery.trim()) {
        const textToSearch = `${s.name} ${s.saint || ''} ${s.exact_start_text || ''}`.toLowerCase();
        if (!textToSearch.includes(searchQuery.toLowerCase())) {
          return false;
        }
      }
      
      return true;
    });
  }, [segments, typeFilter, saintFilter, searchQuery]);

  const handlePlay = (track) => {
    if (playingTrack && playingTrack.video_id === track.video_id && playingTrack.start_time_seconds === track.start_time_seconds) {
      setPlayingTrack(null); // Pause if clicking the same track
    } else {
      setPlayingTrack(track);
    }
  };

  return (
    <div className="stories-page">
      <MusicBanner 
        isLoading={loading} 
        totalTracks={segments.length} 
        filteredTracks={filteredSegments.length} 
      />

      <div className="premium-search-container">
        <div className="premium-search-box">
          <span className="premium-search-icon">🔍</span>
          <input 
            type="text" 
            className="premium-search-input"
            placeholder={lang === 'mr' ? "अभंग, आरती, संत शोधा..." : "Search abhang, aarti, saint..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button 
            className="icon-btn"
            onClick={() => setShowMobileFilters(true)}
            title="Open Filters"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="4" y1="21" x2="4" y2="14"></line>
              <line x1="4" y1="10" x2="4" y2="3"></line>
              <line x1="12" y1="21" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12" y2="3"></line>
              <line x1="20" y1="21" x2="20" y2="16"></line>
              <line x1="20" y1="12" x2="20" y2="3"></line>
              <line x1="1" y1="14" x2="7" y2="14"></line>
              <line x1="9" y1="8" x2="15" y2="8"></line>
              <line x1="17" y1="16" x2="23" y2="16"></line>
            </svg>
          </button>
        </div>
      </div>

      {showMobileFilters && (
        <div className="filter-drawer-overlay" onClick={() => setShowMobileFilters(false)}>
          <div className="filter-drawer open" onClick={e => e.stopPropagation()}>
            <div className="filter-drawer-header">
              <h3>Filters</h3>
              <button className="close-drawer-btn" onClick={() => setShowMobileFilters(false)}>✕</button>
            </div>
            <div className="filter-drawer-content">
              <div className="filter-group">
                <label>Type (प्रकार)</label>
                <select 
                  className="premium-select"
                  value={typeFilter} 
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <option value="सर्व">All Types (सर्व)</option>
                  {uniqueTypes.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-group">
                <label>Saint / Character (संत)</label>
                <select 
                  className="premium-select"
                  value={saintFilter} 
                  onChange={(e) => setSaintFilter(e.target.value)}
                >
                  <option value="सर्व">All Saints (सर्व)</option>
                  {uniqueSaints.map(saint => (
                    <option key={saint} value={saint}>{saint}</option>
                  ))}
                </select>
              </div>
              
              <div className="filter-actions">
                <button 
                  className="filter-reset-btn" 
                  onClick={() => { setTypeFilter('सर्व'); setSaintFilter('सर्व'); setSearchQuery(''); }}
                >
                  Reset All
                </button>
                <button 
                  className="filter-apply-btn" 
                  onClick={() => setShowMobileFilters(false)}
                >
                  View {filteredSegments.length} Results
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading-wrapper">
          <div className="energy-ring" />
          <span className="loading-text">Loading Music...</span>
        </div>
      ) : error ? (
        <div className="no-results" style={{ textAlign: 'center', color: '#ff4444' }}>{error}</div>
      ) : (
        <div className="stories-list" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {filteredSegments.length === 0 ? (
            <p className="no-results" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)' }}>
              No tracks found for the selected filters.
            </p>
          ) : (
            filteredSegments.map((track, i) => (
              <MusicCard 
                key={`${track.video_id}-${track.start_time_seconds}-${i}`}
                track={track}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}
