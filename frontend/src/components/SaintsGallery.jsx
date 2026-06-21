import React, { useState, useMemo, useEffect } from 'react';
import SaintCard from './SaintCard';
import { api } from '../utils/api';
import './SaintsGallery.css';

export default function SaintsGallery({ allStories }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [eraFilter, setEraFilter] = useState('All');
  const [saintsData, setSaintsData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSaints()
      .then(data => {
        setSaintsData(data.saints || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch saints:", err);
        setLoading(false);
      });
  }, []);

  const uniqueEras = useMemo(() => {
    const eras = new Set(saintsData.map(s => s.era || 'Unknown Era'));
    return ['All', ...Array.from(eras)];
  }, [saintsData]);

  const filteredSaints = saintsData.filter(s => {
    const era = s.era || 'Unknown Era';
    const tradition = s.tradition || '';
    const matchesSearch = s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          tradition.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesEra = eraFilter === 'All' || era === eraFilter;
    return matchesSearch && matchesEra;
  });

  return (
    <div className="saints-gallery-page">
      {/* Hero Section */}
      <div className="saints-hero">
        <div className="saints-hero-bg">
          <div className="mandala-container">
            {/* SVG Mandala - using CSS rotation */}
            <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" className="rotating-mandala">
              <path fill="rgba(249, 115, 22, 0.1)" d="M42.7,-73.4C56.6,-68.8,70.1,-58.5,79.5,-45.3C88.8,-32.1,94,-16,92.5,-0.8C91,14.4,82.8,28.8,72.6,40.7C62.4,52.6,50.2,62.1,36.5,69.5C22.8,76.9,7.6,82.3,-7.4,85.2C-22.3,88.1,-36.8,88.4,-50,81.8C-63.1,75.3,-74.8,61.9,-82.5,46.7C-90.2,31.5,-93.8,14.5,-90.7,-1.5C-87.6,-17.5,-77.8,-32.5,-66.1,-43.8C-54.4,-55,-40.8,-62.5,-27.3,-67.6C-13.8,-72.7,-0.4,-75.4,14,-75.4C28.4,-75.4,42.8,-72.7,42.7,-73.4Z" transform="translate(100 100)" />
            </svg>
          </div>
        </div>
        
        <div className="saints-hero-content">
          <h1 className="saints-hero-title">Saints & Sages</h1>
          <p className="saints-hero-subtitle">Explore the lives, teachings, and devotional music of the great spiritual masters.</p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="saints-filter-bar">
        <div className="saints-search-wrapper">
          <span className="search-icon">🔍</span>
          <input 
            type="text" 
            className="saints-search-input"
            placeholder="Search by name or tradition..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="saints-era-filters">
          {uniqueEras.map(era => (
            <button 
              key={era} 
              className={`era-pill ${eraFilter === era ? 'active' : ''}`}
              onClick={() => setEraFilter(era)}
            >
              {era}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="saints-grid">
        {loading ? (
          <div className="loading-spinner">Loading Saints...</div>
        ) : filteredSaints.length > 0 ? (
          filteredSaints.map((saint, index) => (
            <SaintCard key={saint.name} saint={saint} index={index} />
          ))
        ) : (
          <div className="no-saints-found">
            <p>No saints found matching your criteria.</p>
            <button onClick={() => {setSearchQuery(''); setEraFilter('All');}} className="reset-saints-btn">Reset Filters</button>
          </div>
        )}
      </div>
    </div>
  );
}
