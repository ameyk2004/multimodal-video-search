import { createContext, useContext, useState, useCallback, useRef } from 'react';

const PlayerContext = createContext(null);

/**
 * Shape of a media item:
 * {
 *   id: string,           // unique id e.g. `${video_id}-${start}`
 *   videoId: string,      // YouTube video ID
 *   startSeconds: number,
 *   endSeconds: number | null,
 *   title: string,
 *   subtitle: string,     // saint / author / query
 *   thumb: string,        // thumbnail URL
 *   type: 'music' | 'story' | 'video' | 'result',
 * }
 */

export function PlayerProvider({ children }) {
  const [nowPlaying, setNowPlaying] = useState(null);
  const [queue, setQueue] = useState([]);
  const [history, setHistory] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isVisible, setIsVisible] = useState(false);

  // play: start a new track immediately, push current to history
  const play = useCallback((item) => {
    if (!item) return;

    // If the item being played is already in the queue, remove it from the queue so it doesn't play twice
    setQueue(prev => prev.filter(q => q.id !== item.id));

    setNowPlaying(prev => {
      if (prev && prev.id !== item.id) setHistory(h => [prev, ...h].slice(0, 20));
      return item;
    });
    setIsVisible(true);
    setIsExpanded(true);
  }, []);

  // addToQueue: add to end of queue
  const addToQueue = useCallback((item) => {
    if (!item) return;
    setQueue(prev => {
      // don't duplicate
      if (prev.some(q => q.id === item.id)) return prev;
      return [...prev, item];
    });
    setIsVisible(true);
    // If nothing is playing, start it immediately
    setNowPlaying(prev => {
      if (!prev) return item;
      return prev;
    });
  }, []);

  // playNext: advance to next queue item
  const playNext = useCallback(() => {
    setQueue(prev => {
      if (prev.length === 0) return prev;
      const [next, ...rest] = prev;
      setNowPlaying(current => {
        if (current) setHistory(h => [current, ...h].slice(0, 20));
        return next;
      });
      return rest;
    });
  }, []);

  // playPrevious: go back in history
  const playPrevious = useCallback(() => {
    setHistory(prev => {
      if (prev.length === 0) return prev;
      const [last, ...rest] = prev;
      setNowPlaying(current => {
        if (current) setQueue(q => [current, ...q]);
        return last;
      });
      return rest;
    });
  }, []);

  // removeFromQueue: remove a specific item by id
  const removeFromQueue = useCallback((id) => {
    setQueue(prev => prev.filter(item => item.id !== id));
  }, []);

  // clearQueue
  const clearQueue = useCallback(() => setQueue([]), []);

  // dismiss: hide the player entirely
  const dismiss = useCallback(() => {
    setNowPlaying(null);
    setQueue([]);
    setIsVisible(false);
    setIsExpanded(false);
  }, []);

  const toggleExpand = useCallback(() => setIsExpanded(e => !e), []);

  const value = {
    nowPlaying,
    queue,
    history,
    isExpanded,
    isVisible,
    play,
    addToQueue,
    playNext,
    playPrevious,
    removeFromQueue,
    clearQueue,
    dismiss,
    toggleExpand,
  };

  return (
    <PlayerContext.Provider value={value}>
      {children}
    </PlayerContext.Provider>
  );
}

export function usePlayer() {
  const ctx = useContext(PlayerContext);
  if (!ctx) throw new Error('usePlayer must be used within PlayerProvider');
  return ctx;
}

/** Helpers to normalize each content type into a player item */
export function trackToItem(track) {
  return {
    id: `${track.video_id}-${track.start_time_seconds}`,
    videoId: track.video_id,
    startSeconds: Math.floor(track.start_time_seconds || 0),
    endSeconds: track.end_time_seconds > track.start_time_seconds ? Math.ceil(track.end_time_seconds) : null,
    title: track.name || track.name_english || 'Untitled',
    subtitle: track.saint || track.saint_english || track.type || '',
    thumb: `https://img.youtube.com/vi/${track.video_id}/mqdefault.jpg`,
    type: 'music',
  };
}

export function storyToItem(story) {
  return {
    id: `${story.video_id}-${story.start_time_seconds}`,
    videoId: story.video_id,
    startSeconds: Math.floor(story.start_time_seconds || 0),
    endSeconds: story.end_time_seconds > story.start_time_seconds ? Math.ceil(story.end_time_seconds) : null,
    title: story.title || story.title_english || 'Untitled Story',
    subtitle: story.normalized_saint_name || story.character_or_saint || '',
    thumb: story.thumbnail_url || `https://img.youtube.com/vi/${story.video_id}/mqdefault.jpg`,
    type: 'story',
  };
}

export function resultToItem(result, query) {
  return {
    id: `${result.video_id}-${result.start_time}`,
    videoId: result.video_id,
    startSeconds: Math.floor(result.start_time || 0),
    endSeconds: null,
    title: query || 'Search Result',
    subtitle: result.marathi_raw ? result.marathi_raw.substring(0, 60) + '…' : '',
    thumb: `https://img.youtube.com/vi/${result.video_id}/mqdefault.jpg`,
    type: 'result',
  };
}
