import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import maharajImg from '../assets/images/image-removebg-preview.png';
import tukaramImg from '../assets/images/tukaram.png';
import kakaImg from '../assets/images/pethe_kaka_1-removebg-preview.png';
import './StoriesBanner.css';

const StoriesBanner = ({ isLoading, totalStories, filteredStories }) => {
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    // Artificial delay to show proper loading animation if desired, 
    // or just sync with parent's isLoading
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
        {/* Background Ambient Glow */}
        <div className="stories-banner-bg-glow"></div>

        <div className="stories-banner-content">
          {/* Left Images (Maharaj & Tukaram) */}
          <div className="banner-images-left">
            <motion.img 
              src={maharajImg} 
              alt="Shree Swami Samarth" 
              className="banner-img img-maharaj"
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: showContent ? 1 : 0, x: showContent ? 0 : -30 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            />
            <motion.img 
              src={tukaramImg} 
              alt="Sant Tukaram" 
              className="banner-img img-tukaram"
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: showContent ? 1 : 0, x: showContent ? 0 : -30 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            />
          </div>

          {/* Center Text */}
          <div className="banner-center-text">
            {isLoading ? (
              <div className="banner-loader">
                <div className="energy-ring" style={{ width: 40, height: 40 }}></div>
                <p>Loading Stories...</p>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: showContent ? 1 : 0, scale: showContent ? 1 : 0.9 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <h1 className="banner-title">
                  अध्यात्मिक गोष्टी <span className="banner-title-desktop-only">व कथा</span>
                </h1>
                <div className="banner-divider">
                  <span className="star">✧</span>
                  <span className="line"></span>
                  <span className="star">✧</span>
                </div>
                <p className="banner-stats">
                  {filteredStories === totalStories 
                    ? `Showing all ${totalStories} stories`
                    : `Showing ${filteredStories} of ${totalStories} stories`}
                </p>
              </motion.div>
            )}
          </div>

          {/* Right Image (Pethe Kaka) */}
          <div className="banner-images-right">
            <motion.img 
              src={kakaImg} 
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

export default StoriesBanner;
