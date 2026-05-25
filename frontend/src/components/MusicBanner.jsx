import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import ramdasImg from '../assets/images/ramdas_swami.png';
import kakaMusicImg from '../assets/images/Pethe_kaka_music.png';
import kaka3Img from '../assets/images/pethe_kaka_3.png';
import './StoriesBanner.css'; // Reuse the same CSS

const MusicBanner = ({ isLoading, totalTracks, filteredTracks }) => {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      const timer = setTimeout(() => setShowContent(true), 300);
      return () => clearTimeout(timer);
    } else {
      setShowContent(false);
    }
  }, [isLoading]);

  return (
    <div className="stories-banner-wrapper">
      <motion.div 
        className="stories-banner-container"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <div className="stories-banner-bg-glow" style={{ background: 'radial-gradient(ellipse at center, rgba(255, 170, 0, 0.15) 0%, transparent 70%)' }}></div>

        <div className="stories-banner-content">
          {/* Left Images */}
          <div className="banner-images-left" style={{ position: 'relative', bottom: '-1.5rem' }}>
            <motion.img 
              src={kakaMusicImg} 
              alt="Shree Pethe Kaka Singing" 
              className="banner-img"
              style={{ marginLeft: '-1.5rem', marginBottom: '-1rem', height: '170px', objectFit: 'contain' }}
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: showContent ? 1 : 0, x: showContent ? 0 : -30 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            />
            <motion.img 
              src={ramdasImg} 
              alt="Samarth Ramdas Swami" 
              className="banner-img"
              style={{ marginBottom: '-1rem', height: '150px', objectFit: 'contain' }}
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: showContent ? 1 : 0, x: showContent ? 0 : -30 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            />
          </div>

          {/* Center Text */}
          <div className="banner-center-text">
            {isLoading ? (
              <div className="banner-loader">
                <div className="energy-ring" style={{ width: 40, height: 40, borderColor: 'rgba(255,170,0,0.3)', borderTopColor: '#FFD700' }}></div>
                <p>Loading Music...</p>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: showContent ? 1 : 0, scale: showContent ? 1 : 0.9 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <h1 className="banner-title">
                  अभंग <span className="banner-title-desktop-only">व आरत्या</span>
                </h1>
                <div className="banner-divider">
                  <span className="star" style={{ color: '#FFD700' }}>✧</span>
                  <span className="line" style={{ background: 'linear-gradient(90deg, transparent, #FFD700, transparent)' }}></span>
                  <span className="star" style={{ color: '#FFD700' }}>✧</span>
                </div>
                <p className="banner-stats">
                  {filteredTracks === totalTracks 
                    ? `Showing all ${totalTracks} tracks`
                    : `Showing ${filteredTracks} of ${totalTracks} tracks`}
                </p>
              </motion.div>
            )}
          </div>

          {/* Right Image */}
          <div className="banner-images-right">
            <motion.img 
              src={kaka3Img} 
              alt="Shree Pethe Kaka" 
              className="banner-img img-kaka"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: showContent ? 1 : 0, x: showContent ? 0 : 30 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default MusicBanner;
