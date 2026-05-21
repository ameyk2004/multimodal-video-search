/** Format seconds into M:SS */
export function formatTime(seconds) {
  const s = Math.floor(seconds);
  const m = Math.floor(s / 60);
  const ss = String(s % 60).padStart(2, '0');
  return `${m}:${ss}`;
}

/** Build YouTube embed URL with autoplay at timestamp */
export function ytEmbedUrl(videoId, startSeconds) {
  const t = Math.floor(startSeconds);
  return `https://www.youtube.com/embed/${videoId}?start=${t}&autoplay=1&rel=0&modestbranding=1`;
}

/** Build YouTube watch URL with timestamp */
export function ytWatchUrl(videoId, startSeconds) {
  const t = Math.floor(startSeconds);
  return `https://www.youtube.com/watch?v=${videoId}&t=${t}s`;
}

/** YouTube thumbnail */
export function ytThumb(videoId) {
  return `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`;
}
