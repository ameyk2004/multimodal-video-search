import React from 'react';
import { useNavigate } from 'react-router-dom';
import './SaintCard.css';

export default function SaintCard({ saint, index }) {
  const navigate = useNavigate();
  
  // Provide a safe fallback if properties are missing
  const name = saint.name || saint.normalized_saint_name || "Unknown Saint";
  const era = saint.era || "Spiritual Era";
  const tradition = saint.tradition || "Bhakti Tradition";
  const image = saint.imageUrl || `/assets/placeholders/${['meditating', 'veena', 'books', 'namaste', 'dholak', 'staff'][index % 6]}.png`;
  const quote = saint.quote || "Tap to explore teachings and bhajans.";

  return (
    <div 
      className="saint-card" 
      onClick={() => navigate(`/saints/${encodeURIComponent(name)}`)}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      <div className="saint-card-glow-bg"></div>
      <div className="saint-card-image-wrapper">
        <img src={image} alt={name} className="saint-card-image" loading="lazy" />
        <div className="saint-card-image-overlay"></div>
      </div>
      <div className="saint-card-content">
        <div className="saint-card-header">
          <h3 className="saint-card-name">{name}</h3>
          <span className="saint-card-tradition">{tradition}</span>
        </div>
        <div className="saint-card-era">{era}</div>
        <p className="saint-card-quote">"{quote}"</p>
        
        <div className="saint-card-footer">
          <div className="saint-stats">
            <span className="stat-pill"><span className="icon">📖</span> {saint.storyCount || 0}</span>
            <span className="stat-pill"><span className="icon">🎵</span> {saint.musicCount || 0}</span>
          </div>
          <span className="explore-btn">Explore ➔</span>
        </div>
      </div>
    </div>
  );
}
