import React, { useState, useEffect, useRef, useCallback } from 'react';
import { usePlayer } from '../context/PlayerContext';
import './MiniPlayer.css';

/* ── Icon helpers ─────────────────────────────────────── */
const IconPrev = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M6 6h2v12H6zm3.5 6 8.5 6V6z"/>
  </svg>
);
const IconNext = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M6 18l8.5-6L6 6v12zm9-12v12h2V6h-2z"/>
  </svg>
);
const IconPlay = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
    <path d="M8 5v14l11-7z"/>
  </svg>
);
const IconPause = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
  </svg>
);
const IconQueue = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/>
  </svg>
);
const IconClose = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
  </svg>
);
const IconChevronDown = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
  </svg>
);
const IconRemove = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
  </svg>
);

/* ── type label map ───────────────────────────────────── */
const TYPE_LABELS = {
  music: '🎵 Music',
  story: '📖 Story',
  video: '🎬 Video',
  result: '🔍 Result',
};

/* ═══════════════════════════════════════════════════════ */
/*  MiniPlayer Component                                   */
/* ═══════════════════════════════════════════════════════ */
export default function MiniPlayer() {
  const {
    nowPlaying,
    queue,
    isExpanded,
    isVisible,
    playNext,
    playPrevious,
    removeFromQueue,
    dismiss,
    toggleExpand,
    history,
  } = usePlayer();

  const [isPlaying, setIsPlaying] = useState(true);
  const [progress, setProgress] = useState(0);
  const iframeRef = useRef(null);
  const progressTimerRef = useRef(null);
  const startedAtRef = useRef(null);

  /* Reset progress + restart simulated timer whenever track changes */
  useEffect(() => {
    if (!nowPlaying) return;
    setIsPlaying(true);
    setProgress(0);
    startedAtRef.current = Date.now();

    clearInterval(progressTimerRef.current);

    // Simulate progress only if we have a known duration
    const durSec = nowPlaying.endSeconds && nowPlaying.endSeconds > nowPlaying.startSeconds
      ? nowPlaying.endSeconds - nowPlaying.startSeconds
      : null;

    if (durSec && durSec > 0) {
      progressTimerRef.current = setInterval(() => {
        const elapsed = (Date.now() - startedAtRef.current) / 1000;
        const pct = Math.min((elapsed / durSec) * 100, 100);
        setProgress(pct);
        if (pct >= 100) {
          clearInterval(progressTimerRef.current);
          // Auto-advance to next in queue
          if (queue.length > 0) playNext();
        }
      }, 1000);
    }

    return () => clearInterval(progressTimerRef.current);
  }, [nowPlaying?.id]);

  /* Pause/resume: send postMessage to YouTube iframe */
  const togglePlay = useCallback((e) => {
    e.stopPropagation();
    if (!iframeRef.current) return;
    const msg = isPlaying ? '{"event":"command","func":"pauseVideo","args":""}' : '{"event":"command","func":"playVideo","args":""}';
    iframeRef.current.contentWindow?.postMessage(msg, '*');
    setIsPlaying(p => !p);
    if (isPlaying) {
      clearInterval(progressTimerRef.current);
    } else {
      startedAtRef.current = Date.now() - ((progress / 100) * ((nowPlaying?.endSeconds || 0) - (nowPlaying?.startSeconds || 0)) * 1000);
    }
  }, [isPlaying, progress, nowPlaying]);

  if (!isVisible || !nowPlaying) return null;

  const formatTime = (seconds) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const getDurationString = (item) => {
    if (!item || !item.endSeconds || !item.startSeconds) return '';
    const diff = item.endSeconds - item.startSeconds;
    return diff > 0 ? ` • ${formatTime(diff)}` : '';
  };

  const embedSrc = `https://www.youtube.com/embed/${nowPlaying.videoId}?start=${nowPlaying.startSeconds}${nowPlaying.endSeconds ? `&end=${nowPlaying.endSeconds}` : ''}&autoplay=1&rel=0&modestbranding=1&enablejsapi=1`;

  return (
    <>
      {/* ── Expanded Modal ── */}
      <div className={`mini-player-expanded-overlay ${isExpanded ? 'open' : 'closed'}`} onClick={toggleExpand}>
        <div className={`mini-player-expanded-panel ${isExpanded ? 'open' : 'closed'}`} onClick={e => e.stopPropagation()}>
            <div style={{ padding: '10px 20px 0' }}>
              <div className="mp-expanded-drag-handle" />
            </div>

            <div className="mp-expanded-header">
              <span className="mp-expanded-title">Now Playing</span>
              <button className="mp-expanded-close" onClick={toggleExpand} aria-label="Close player">
                <IconChevronDown />
              </button>
            </div>

            <div className="mp-expanded-body">
              <div className="mp-expanded-left">
                {/* Iframe */}
                <div className="mp-iframe-container">
                  <iframe
                    ref={iframeRef}
                    src={embedSrc}
                    title={nowPlaying.title}
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>

                {/* Track info */}
                <div className="mp-expanded-now-playing">
                  <p className="mp-expanded-track-title">{nowPlaying.title}</p>
                  <p className="mp-expanded-track-sub">
                    <span className="mini-player-type-badge">{TYPE_LABELS[nowPlaying.type] || nowPlaying.type}</span>
                    {nowPlaying.subtitle}
                    {getDurationString(nowPlaying)}
                  </p>
                </div>

                {/* Controls */}
                <div className="mp-expanded-controls">
                  <button
                    className="mini-ctrl-btn"
                    onClick={(e) => { e.stopPropagation(); playPrevious(); }}
                    title="Previous"
                    disabled={history.length === 0}
                    style={{ opacity: history.length === 0 ? 0.3 : 1 }}
                  >
                    <IconPrev />
                  </button>
                  <button className="mini-ctrl-btn play-pause" onClick={togglePlay} title={isPlaying ? 'Pause' : 'Play'}>
                    {isPlaying ? <IconPause /> : <IconPlay />}
                  </button>
                  <button
                    className="mini-ctrl-btn"
                    onClick={(e) => { e.stopPropagation(); playNext(); }}
                    title="Next"
                    disabled={queue.length === 0}
                    style={{ opacity: queue.length === 0 ? 0.3 : 1 }}
                  >
                    <IconNext />
                  </button>
                </div>
              </div>

              {/* Queue */}
              <div className="mp-queue-panel">
                <p className="mp-queue-label">
                  Next in Queue ({queue.length})
                </p>
                {queue.length === 0 ? (
                  <p className="mp-queue-empty">Queue is empty. Add tracks with the + button.</p>
                ) : (
                  queue.map((item, idx) => (
                    <div key={item.id} className="mp-queue-item">
                      <img src={item.thumb} alt={item.title} className="mp-queue-thumb"
                        onError={e => { e.target.src = `https://img.youtube.com/vi/${item.videoId}/0.jpg`; }}
                      />
                      <div className="mp-queue-item-info">
                        <p className="mp-queue-item-title">{item.title}</p>
                        <p className="mp-queue-item-sub">
                          {item.subtitle}
                          {getDurationString(item)}
                        </p>
                      </div>
                      <button
                        className="mp-queue-remove-btn"
                        onClick={() => removeFromQueue(item.id)}
                        title="Remove from queue"
                      >
                        <IconRemove />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
        </div>
      </div>

      {/* ── Collapsed Mini Bar ── */}
      <div
        className={`mini-player-bar ${isVisible && !isExpanded ? 'visible' : ''}`}
        onClick={toggleExpand}
        role="region"
        aria-label="Now Playing"
      >
        {/* Simulated progress */}
        <div className="mini-player-progress-track" onClick={e => e.stopPropagation()}>
          <div className="mini-player-progress-fill" style={{ width: `${progress}%` }} />
        </div>

        {/* Thumbnail */}
        <img
          src={nowPlaying.thumb}
          alt={nowPlaying.title}
          className="mini-player-thumb"
          onError={e => { e.target.src = `https://img.youtube.com/vi/${nowPlaying.videoId}/0.jpg`; }}
        />

        {/* Info */}
        <div className="mini-player-info">
          <p className="mini-player-title">
            <span className="mini-player-type-badge">{TYPE_LABELS[nowPlaying.type]}</span>
            {nowPlaying.title}
          </p>
          <p className="mini-player-subtitle">{nowPlaying.subtitle}</p>
        </div>

        {/* Controls */}
        <div className="mini-player-controls" onClick={e => e.stopPropagation()}>
          {/* Prev — hide on very small screens via CSS */}
          <button
            className="mini-ctrl-btn prev-btn-mobile-hide"
            onClick={(e) => { e.stopPropagation(); playPrevious(); }}
            title="Previous"
            disabled={history.length === 0}
            style={{ opacity: history.length === 0 ? 0.3 : 1 }}
            aria-label="Previous track"
          >
            <IconPrev />
          </button>

          {/* Play / Pause */}
          <button
            className="mini-ctrl-btn play-pause"
            onClick={togglePlay}
            title={isPlaying ? 'Pause' : 'Play'}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? <IconPause /> : <IconPlay />}
          </button>

          {/* Next */}
          <button
            className="mini-ctrl-btn"
            onClick={(e) => { e.stopPropagation(); playNext(); }}
            title="Next"
            disabled={queue.length === 0}
            style={{ opacity: queue.length === 0 ? 0.3 : 1 }}
            aria-label="Next track"
          >
            <IconNext />
          </button>

          {/* Queue */}
          <button
            className="mini-ctrl-btn queue-btn"
            onClick={(e) => { e.stopPropagation(); toggleExpand(); }}
            title="Show queue"
            aria-label="Show queue"
          >
            <IconQueue />
            {queue.length > 0 && (
              <span className="queue-count-badge">{queue.length > 9 ? '9+' : queue.length}</span>
            )}
          </button>

          {/* Dismiss */}
          <button
            className="mini-ctrl-btn dismiss"
            onClick={(e) => { e.stopPropagation(); dismiss(); }}
            title="Close player"
            aria-label="Close player"
          >
            <IconClose />
          </button>
        </div>

      </div>
    </>
  );
}
