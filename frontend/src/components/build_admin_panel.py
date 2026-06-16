import os

code = """import React, { useState, useEffect, useRef, useMemo } from 'react';
import { api } from '../utils/api';

export default function AdminPanel() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [passcode, setPasscode] = useState('');
  
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  const [viewMode, setViewMode] = useState('by_video'); // 'by_video' or 'by_saint'

  // ====== BY VIDEO STATE ======
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVideoId, setSelectedVideoId] = useState('');
  const [videoData, setVideoData] = useState(null);
  const [stories, setStories] = useState([]);
  const [music, setMusic] = useState([]);

  // ====== BY SAINT STATE ======
  const [saintSearchTerm, setSaintSearchTerm] = useState('');
  const [selectedSaint, setSelectedSaint] = useState(null);
  const [modifiedVideoIds, setModifiedVideoIds] = useState(new Set());
  const [currentPlayingVideoId, setCurrentPlayingVideoId] = useState('');
  const [saintSortBy, setSaintSortBy] = useState('alphabetical');

  // YouTube Player Ref
  const playerRef = useRef(null);
  const PASSCODE = 'admin123';

  useEffect(() => {
    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }
  }, []);

  const activePlayerVideoId = viewMode === 'by_video' ? selectedVideoId : currentPlayingVideoId;

  useEffect(() => {
    if (!activePlayerVideoId) return;

    const loadPlayer = () => {
      if (window.YT && window.YT.Player) {
        if (!playerRef.current) {
          playerRef.current = new window.YT.Player('admin-yt-player', {
            videoId: activePlayerVideoId,
            playerVars: { enablejsapi: 1, autoplay: 0 },
            events: {
              onReady: () => console.log('YouTube Player Ready')
            }
          });
        } else {
          playerRef.current.loadVideoById(activePlayerVideoId);
        }
      } else {
        setTimeout(loadPlayer, 500);
      }
    };

    loadPlayer();
  }, [activePlayerVideoId]);

  const handleLogin = (e) => {
    e.preventDefault();
    if (passcode === PASSCODE) {
      setIsAuthenticated(true);
      fetchVideos();
    } else {
      alert('Incorrect passcode');
    }
  };

  const fetchVideos = async () => {
    try {
      setLoading(true);
      const res = await api.getAdminVideos();
      setVideos(res.videos || []);
    } catch (err) {
      console.error(err);
      setMessage('Failed to load videos.');
    } finally {
      setLoading(false);
    }
  };

  // ==========================================
  //         BY VIDEO LOGIC (Original)
  // ==========================================
  const loadVideoDetails = async (videoId) => {
    if (!videoId) {
      setVideoData(null);
      setStories([]);
      setMusic([]);
      return;
    }
    
    try {
      setLoading(true);
      setMessage('');
      const data = await api.getAdminVideoDetails(videoId);
      setVideoData(data);
      setStories(data.stories || []);
      setMusic(data.musical_segments || []);
    } catch (err) {
      console.error(err);
      setMessage('Failed to load video details.');
    } finally {
      setLoading(false);
    }
  };

  const handleVideoSelect = (vId) => {
    if (vId === selectedVideoId) return;
    setSelectedVideoId(vId);
    loadVideoDetails(vId);
  };

  const handleStoryChange = (index, field, value) => {
    const updated = [...stories];
    updated[index] = { ...updated[index], [field]: value };
    if (field === 'start_time_seconds' || field === 'end_time_seconds') {
      updated[index][field] = Number(value);
    }
    setStories(updated);
  };

  const handleMusicChange = (index, field, value) => {
    const updated = [...music];
    updated[index] = { ...updated[index], [field]: value };
    if (field === 'start_time_seconds' || field === 'end_time_seconds') {
      updated[index][field] = Number(value);
    }
    setMusic(updated);
  };

  const handleDeleteStory = (index) => {
    if (window.confirm('Are you sure you want to delete this story?')) {
      const updated = [...stories];
      updated.splice(index, 1);
      setStories(updated);
    }
  };

  const handleDeleteMusic = (index) => {
    if (window.confirm('Are you sure you want to delete this musical segment?')) {
      const updated = [...music];
      updated.splice(index, 1);
      setMusic(updated);
    }
  };

  const handleAddStory = () => {
    setStories([...stories, { title: '', normalized_saint_name: '', start_time_seconds: 0, end_time_seconds: 0, moral: '' }]);
  };

  const handleAddMusic = () => {
    setMusic([...music, { name: '', saint: '', type: 'Bhajan', start_time_seconds: 0, end_time_seconds: 0, moral: '' }]);
  };

  const handleSave = async () => {
    try {
      setLoading(true);
      setMessage('Saving...');
      await api.updateAdminVideo(selectedVideoId, { stories, musical_segments: music });
      setMessage('Successfully saved!');
      setTimeout(() => setMessage(''), 3000);
      fetchVideos(); // Refresh global videos list to keep Saint view up to date
    } catch (err) {
      console.error(err);
      setMessage('Failed to save changes.');
    } finally {
      setLoading(false);
    }
  };

  const filteredVideos = videos.filter(v => {
    const term = searchTerm.toLowerCase();
    if (!term) return true;
    if (v.title?.toLowerCase().includes(term)) return true;
    if (v.video_id?.toLowerCase().includes(term)) return true;
    if (v.stories && v.stories.some(s => s.title?.toLowerCase().includes(term) || s.normalized_saint_name?.toLowerCase().includes(term) || s.character_or_saint?.toLowerCase().includes(term))) return true;
    if (v.musical_segments && v.musical_segments.some(m => m.name?.toLowerCase().includes(term) || m.saint?.toLowerCase().includes(term))) return true;
    return false;
  });


  // ==========================================
  //         BY SAINT LOGIC (New)
  // ==========================================

  const groupedSaintsData = useMemo(() => {
    const groups = {}; // { saintName: { stories: [], music: [] } }
    videos.forEach((v, vIndex) => {
      (v.stories || []).forEach((s, sIndex) => {
        const saint = s.normalized_saint_name || s.character_or_saint || 'Unknown';
        if (!groups[saint]) groups[saint] = { stories: [], music: [] };
        groups[saint].stories.push({ ...s, video_id: v.video_id, vIndex, sIndex, video_title: v.title });
      });
      (v.musical_segments || []).forEach((m, mIndex) => {
        const saint = m.saint || 'Unknown';
        if (!groups[saint]) groups[saint] = { stories: [], music: [] };
        groups[saint].music.push({ ...m, video_id: v.video_id, vIndex, mIndex, video_title: v.title });
      });
    });
    
    const arr = Object.keys(groups).map(k => ({
      saint: k,
      stories: groups[k].stories,
      music: groups[k].music,
      totalItems: groups[k].stories.length + groups[k].music.length,
      totalMusic: groups[k].music.length
    }));

    if (saintSortBy === 'most_music') arr.sort((a,b) => b.totalMusic - a.totalMusic);
    else if (saintSortBy === 'most_total') arr.sort((a,b) => b.totalItems - a.totalItems);
    else arr.sort((a,b) => a.saint.localeCompare(b.saint));

    return arr;
  }, [videos, saintSortBy]);

  const filteredSaints = groupedSaintsData.filter(s => s.saint.toLowerCase().includes(saintSearchTerm.toLowerCase()));

  const handleSaintSelection = (saintName) => {
    setSelectedSaint(saintName);
  };

  const selectedSaintData = useMemo(() => {
    return groupedSaintsData.find(s => s.saint === selectedSaint);
  }, [groupedSaintsData, selectedSaint]);

  // Updating the master 'videos' state directly
  const handleSaintItemChange = (vIndex, arrayName, itemIndex, field, value) => {
    const newVideos = [...videos];
    const video = { ...newVideos[vIndex] };
    const arr = [...(video[arrayName] || [])];
    arr[itemIndex] = { ...arr[itemIndex], [field]: (field.includes('time') ? Number(value) : value) };
    video[arrayName] = arr;
    newVideos[vIndex] = video;
    setVideos(newVideos);
    setModifiedVideoIds(new Set(modifiedVideoIds).add(video.video_id));
  };

  const handleSaintItemDelete = (vIndex, arrayName, itemIndex) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      const newVideos = [...videos];
      const video = { ...newVideos[vIndex] };
      const arr = [...(video[arrayName] || [])];
      arr.splice(itemIndex, 1);
      video[arrayName] = arr;
      newVideos[vIndex] = video;
      setVideos(newVideos);
      setModifiedVideoIds(new Set(modifiedVideoIds).add(video.video_id));
    }
  };

  const handleSaintSaveAll = async () => {
    try {
      setLoading(true);
      setMessage('Saving modified videos...');
      const promises = Array.from(modifiedVideoIds).map(vid => {
        const v = videos.find(x => x.video_id === vid);
        return api.updateAdminVideo(vid, { stories: v.stories, musical_segments: v.musical_segments });
      });
      await Promise.all(promises);
      setModifiedVideoIds(new Set());
      setMessage('Successfully saved all changes!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error(err);
      setMessage('Failed to save changes.');
    } finally {
      setLoading(false);
    }
  };


  // ==========================================
  //                COMMON
  // ==========================================
  const seekAndPlay = (seconds, videoId = null) => {
    if (videoId && currentPlayingVideoId !== videoId && viewMode === 'by_saint') {
      setCurrentPlayingVideoId(videoId);
      setTimeout(() => {
        if (playerRef.current && playerRef.current.seekTo) {
          playerRef.current.seekTo(seconds, true);
          playerRef.current.playVideo();
        }
      }, 800); // give time to load
    } else {
      if (playerRef.current && playerRef.current.seekTo) {
        playerRef.current.seekTo(seconds, true);
        playerRef.current.playVideo();
      }
    }
  };

  const captureTimeCommon = (type, updateFn) => {
    if (playerRef.current && playerRef.current.getCurrentTime) {
      const currentTime = Math.floor(playerRef.current.getCurrentTime());
      updateFn(currentTime);
    } else {
      alert("Please play the video first so the player is ready.");
    }
  };

  const getDurationString = (start, end) => {
    const duration = Math.max(0, Math.round((end || 0) - (start || 0)));
    if (duration === 0) return "0 secs";
    const mins = Math.floor(duration / 60);
    const secs = duration % 60;
    if (mins > 0) return `${mins} mins ${secs} secs`;
    return `${secs} secs`;
  };


  if (!isAuthenticated) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div style={{ background: 'var(--surface)', backdropFilter: 'blur(24px)', border: '1px solid var(--glass-border)', padding: '50px 40px', borderRadius: 'var(--radius-lg)', boxShadow: '0 20px 50px rgba(0,0,0,0.5)', maxWidth: '400px', width: '100%', textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '20px', filter: 'drop-shadow(0 0 12px rgba(249, 115, 22, 0.6))' }}>🪔</div>
          <h2 style={{ marginBottom: '10px', color: 'var(--text)', fontFamily: 'var(--font-head)' }}>Admin Access</h2>
          <form onSubmit={handleLogin}>
            <input type="password" value={passcode} onChange={e => setPasscode(e.target.value)} className="premium-search-input" placeholder="Passcode" style={{ width: '100%', marginBottom: '20px', textAlign: 'center', background: 'rgba(255,255,255,0.05)' }} />
            <button type="submit" className="search-btn" style={{ width: '100%', borderRadius: '12px', height: '48px' }}>Login</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', color: '#fff', width: '100%', maxWidth: '1800px', margin: '0 auto', animation: 'fade-up 0.5s ease both' }}>
      
      {/* Top Toggle Bar */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.4)', borderRadius: '12px', border: '1px solid var(--glass-border)', padding: '4px' }}>
          <button 
            onClick={() => setViewMode('by_video')}
            style={{ padding: '10px 24px', borderRadius: '8px', border: 'none', background: viewMode === 'by_video' ? 'var(--saffron)' : 'transparent', color: viewMode === 'by_video' ? '#fff' : 'var(--text-dim)', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s' }}
          >By Video</button>
          <button 
            onClick={() => setViewMode('by_saint')}
            style={{ padding: '10px 24px', borderRadius: '8px', border: 'none', background: viewMode === 'by_saint' ? 'var(--saffron)' : 'transparent', color: viewMode === 'by_saint' ? '#fff' : 'var(--text-dim)', fontWeight: 'bold', cursor: 'pointer', transition: 'all 0.2s' }}
          >By Saint</button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(250px, 320px) 1fr', gap: '32px', alignItems: 'start' }}>
        
        {/* ========================================================================= */}
        {/*                              LEFT PANEL                                   */}
        {/* ========================================================================= */}
        <div style={{ position: 'sticky', top: '20px', height: 'calc(100vh - 40px)', display: 'flex', flexDirection: 'column', background: 'var(--bg-mid)', borderRadius: '16px', border: '1px solid var(--glass-border)', overflow: 'hidden' }}>
          
          {viewMode === 'by_video' ? (
            <>
              <div style={{ padding: '20px', borderBottom: '1px solid var(--glass-border)', background: 'var(--surface)' }}>
                <h1 style={{ color: 'var(--gold-soft)', fontSize: '24px', margin: 0 }}>Timestamp Editor</h1>
                <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: '4px 0 0 0' }}>Select a video to edit</p>
              </div>
              <div style={{ padding: '12px', borderBottom: '1px solid var(--glass-border)' }}>
                 <input type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Search ID, Title..." className="premium-search-input" style={{ width: '100%', padding: '8px 12px', fontSize: '13px', background: 'rgba(0,0,0,0.5)', borderRadius: '8px' }} />
              </div>
              <div style={{ overflowY: 'auto', padding: '12px', flex: 1 }}>
                {filteredVideos.map((v, index) => (
                  <div key={v.video_id} onClick={() => handleVideoSelect(v.video_id)} style={{ padding: '12px', cursor: 'pointer', borderRadius: '8px', marginBottom: '8px', background: selectedVideoId === v.video_id ? 'rgba(249, 115, 22, 0.15)' : 'transparent', border: selectedVideoId === v.video_id ? '1px solid var(--saffron)' : '1px solid transparent', color: selectedVideoId === v.video_id ? '#fff' : 'var(--text-dim)'}}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: '500', fontSize: '14px' }}>{v.title}</div>
                    <div style={{ fontSize: '11px', opacity: 0.6, marginTop: '2px' }}>{v.video_id}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              <div style={{ padding: '20px', borderBottom: '1px solid var(--glass-border)', background: 'var(--surface)' }}>
                <h1 style={{ color: 'var(--gold-soft)', fontSize: '24px', margin: 0 }}>Saint Editor</h1>
                <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: '4px 0 0 0' }}>Select a saint to edit</p>
              </div>
              <div style={{ padding: '12px', borderBottom: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                 <input type="text" value={saintSearchTerm} onChange={e => setSaintSearchTerm(e.target.value)} placeholder="Search Saint..." className="premium-search-input" style={{ width: '100%', padding: '8px 12px', fontSize: '13px', background: 'rgba(0,0,0,0.5)', borderRadius: '8px' }} />
                 <select value={saintSortBy} onChange={e => setSaintSortBy(e.target.value)} style={{ background: 'rgba(0,0,0,0.5)', color: 'var(--text-dim)', border: '1px solid var(--glass-border)', padding: '6px', borderRadius: '8px', fontSize: '12px' }}>
                    <option value="alphabetical">Sort Alphabetical</option>
                    <option value="most_music">Most Music</option>
                    <option value="most_total">Most Total Items</option>
                 </select>
              </div>
              <div style={{ overflowY: 'auto', padding: '12px', flex: 1 }}>
                {filteredSaints.map((s, index) => (
                  <div key={s.saint} onClick={() => handleSaintSelection(s.saint)} style={{ padding: '12px', cursor: 'pointer', borderRadius: '8px', marginBottom: '8px', background: selectedSaint === s.saint ? 'rgba(251, 191, 36, 0.15)' : 'transparent', border: selectedSaint === s.saint ? '1px solid var(--gold-soft)' : '1px solid transparent', color: selectedSaint === s.saint ? '#fff' : 'var(--text-dim)'}}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: '600', fontSize: '15px' }}>{s.saint}</div>
                    <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '4px', display: 'flex', gap: '8px' }}>
                      <span style={{ color: 'var(--saffron)' }}>📖 {s.stories.length}</span>
                      <span style={{ color: 'var(--gold-soft)' }}>🎵 {s.music.length}</span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

        </div>

        {/* ========================================================================= */}
        {/*                              RIGHT PANEL                                  */}
        {/* ========================================================================= */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>

          {/* Sticky Player Bar */}
          <div style={{ position: 'sticky', top: '0', zIndex: 50, background: 'var(--bg-deep)', padding: '20px 0', borderBottom: '1px solid var(--glass-border)', display: 'flex', gap: '32px', alignItems: 'flex-start', margin: '-20px -20px 24px -20px' }}>
            <div style={{ paddingLeft: '20px', display: 'flex', gap: '32px', width: '100%', alignItems: 'center', justifyContent: 'space-between', paddingRight: '20px' }}>
              <div style={{ width: '400px', flexShrink: 0, background: 'var(--bg-mid)', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--glass-border)', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
                <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%', background: '#000' }}>
                  <div id="admin-yt-player" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}></div>
                </div>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'flex-end', flex: 1 }}>
                <div style={{ textAlign: 'right' }}>
                  <h2 style={{ fontSize: '20px', margin: '0 0 8px 0', color: '#fff' }}>
                    {viewMode === 'by_video' ? `Editing: ${videoData?.title || selectedVideoId || 'None'}` : `Editing Saint: ${selectedSaint || 'None'}`}
                  </h2>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  {message && <div style={{ color: '#4ADE80', background: 'rgba(34, 197, 94, 0.1)', padding: '8px 16px', borderRadius: '8px' }}>{message}</div>}
                  {loading && <div style={{ color: 'var(--saffron)' }}>Syncing...</div>}
                  
                  {viewMode === 'by_video' ? (
                    <button onClick={handleSave} disabled={!selectedVideoId || loading} className="search-btn" style={{ padding: '0 32px', borderRadius: '8px', width: 'auto' }}>
                      Save Video
                    </button>
                  ) : (
                    <button onClick={handleSaintSaveAll} disabled={modifiedVideoIds.size === 0 || loading} className="search-btn" style={{ padding: '0 32px', borderRadius: '8px', width: 'auto', background: modifiedVideoIds.size > 0 ? 'var(--gold-soft)' : 'rgba(255,255,255,0.1)', color: '#000' }}>
                      Save {modifiedVideoIds.size} Modified Videos
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>


          {/* ----------------- BY VIDEO EDIT FORMS ----------------- */}
          {viewMode === 'by_video' && selectedVideoId && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', paddingBottom: '60px' }}>
              
              {/* Stories */}
              <div style={{ background: 'var(--surface)', border: '1px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden' }}>
                <div style={{ padding: '16px 24px', background: 'rgba(249, 115, 22, 0.08)', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <h3 style={{ color: 'var(--text)', fontSize: '18px', margin: 0 }}>📖 Stories ({stories.length})</h3>
                </div>
                <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {stories.map((s, i) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                      <button onClick={() => handleDeleteStory(i)} style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px' }}>🗑️</button>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '40px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                          <div><label>Title</label><input value={s.title || ''} onChange={e => handleStoryChange(i, 'title', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                          <div><label>Saint</label><input value={s.normalized_saint_name || s.character_or_saint || ''} onChange={e => handleStoryChange(i, 'normalized_saint_name', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                        </div>
                        <div><label>Moral</label><input value={s.moral || ''} onChange={e => handleStoryChange(i, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px' }}>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <input type="number" value={s.start_time_seconds || 0} onChange={e => handleStoryChange(i, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                            <button onClick={() => captureTimeCommon('story', (t) => handleStoryChange(i, 'start_time_seconds', t))}>⏱️</button>
                            <button onClick={() => seekAndPlay(s.start_time_seconds || 0)} style={{ background: 'var(--saffron)', color: '#fff', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                          </div>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <input type="number" value={s.end_time_seconds || 0} onChange={e => handleStoryChange(i, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                            <button onClick={() => captureTimeCommon('story', (t) => handleStoryChange(i, 'end_time_seconds', t))}>⏱️</button>
                            <button onClick={() => seekAndPlay(s.end_time_seconds || 0)} style={{ background: 'var(--saffron)', color: '#fff', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  <button onClick={handleAddStory} style={{ background: 'rgba(249, 115, 22, 0.1)', color: 'var(--saffron)', border: '1px dashed var(--saffron)', padding: '16px', borderRadius: '12px', cursor: 'pointer' }}>➕ Add Story</button>
                </div>
              </div>

              {/* Music */}
              <div style={{ background: 'var(--surface)', border: '1px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden' }}>
                <div style={{ padding: '16px 24px', background: 'rgba(251, 191, 36, 0.08)', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <h3 style={{ color: 'var(--text)', fontSize: '18px', margin: 0 }}>🎵 Music ({music.length})</h3>
                </div>
                <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {music.map((m, i) => (
                    <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                      <button onClick={() => handleDeleteMusic(i)} style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px' }}>🗑️</button>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '40px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                          <div><label>Title</label><input value={m.name || ''} onChange={e => handleMusicChange(i, 'name', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                          <div><label>Saint</label><input value={m.saint || ''} onChange={e => handleMusicChange(i, 'saint', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                           <div><label>Type</label><input value={m.type || ''} onChange={e => handleMusicChange(i, 'type', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                           <div><label>Moral</label><input value={m.moral || ''} onChange={e => handleMusicChange(i, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px' }}>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <input type="number" value={m.start_time_seconds || 0} onChange={e => handleMusicChange(i, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                            <button onClick={() => captureTimeCommon('music', (t) => handleMusicChange(i, 'start_time_seconds', t))}>⏱️</button>
                            <button onClick={() => seekAndPlay(m.start_time_seconds || 0)} style={{ background: 'var(--gold-soft)', color: '#000', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                          </div>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <input type="number" value={m.end_time_seconds || 0} onChange={e => handleMusicChange(i, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                            <button onClick={() => captureTimeCommon('music', (t) => handleMusicChange(i, 'end_time_seconds', t))}>⏱️</button>
                            <button onClick={() => seekAndPlay(m.end_time_seconds || 0)} style={{ background: 'var(--gold-soft)', color: '#000', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  <button onClick={handleAddMusic} style={{ background: 'rgba(251, 191, 36, 0.1)', color: 'var(--gold-soft)', border: '1px dashed var(--gold-soft)', padding: '16px', borderRadius: '12px', cursor: 'pointer' }}>➕ Add Music</button>
                </div>
              </div>
            </div>
          )}


          {/* ----------------- BY SAINT EDIT FORMS ----------------- */}
          {viewMode === 'by_saint' && selectedSaintData && (
             <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', paddingBottom: '60px' }}>
                
                {/* Stories */}
                {selectedSaintData.stories.length > 0 && (
                  <div style={{ background: 'var(--surface)', border: '1px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden' }}>
                    <div style={{ padding: '16px 24px', background: 'rgba(249, 115, 22, 0.08)', borderBottom: '1px solid var(--glass-border)' }}>
                      <h3 style={{ color: 'var(--text)', fontSize: '18px', margin: 0 }}>📖 Stories ({selectedSaintData.stories.length})</h3>
                    </div>
                    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      {selectedSaintData.stories.map((s, i) => (
                        <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                          <button onClick={() => handleSaintItemDelete(s.vIndex, 'stories', s.sIndex)} style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px' }}>🗑️</button>
                          
                          <div style={{ marginBottom: '16px', color: 'var(--text-dim)', fontSize: '13px' }}>
                            Video: <strong>{s.video_title}</strong> <span style={{ opacity: 0.5 }}>({s.video_id})</span>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '40px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                              <div><label>Title</label><input value={s.title || ''} onChange={e => handleSaintItemChange(s.vIndex, 'stories', s.sIndex, 'title', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                              <div><label>Saint</label><input value={s.normalized_saint_name || s.character_or_saint || ''} onChange={e => handleSaintItemChange(s.vIndex, 'stories', s.sIndex, 'normalized_saint_name', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                            </div>
                            <div><label>Moral</label><input value={s.moral || ''} onChange={e => handleSaintItemChange(s.vIndex, 'stories', s.sIndex, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px' }}>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <input type="number" value={s.start_time_seconds || 0} onChange={e => handleSaintItemChange(s.vIndex, 'stories', s.sIndex, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                                <button onClick={() => captureTimeCommon('story', (t) => handleSaintItemChange(s.vIndex, 'stories', s.sIndex, 'start_time_seconds', t))}>⏱️</button>
                                <button onClick={() => seekAndPlay(s.start_time_seconds || 0, s.video_id)} style={{ background: 'var(--saffron)', color: '#fff', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                              </div>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <input type="number" value={s.end_time_seconds || 0} onChange={e => handleSaintItemChange(s.vIndex, 'stories', s.sIndex, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                                <button onClick={() => captureTimeCommon('story', (t) => handleSaintItemChange(s.vIndex, 'stories', s.sIndex, 'end_time_seconds', t))}>⏱️</button>
                                <button onClick={() => seekAndPlay(s.end_time_seconds || 0, s.video_id)} style={{ background: 'var(--saffron)', color: '#fff', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Music */}
                {selectedSaintData.music.length > 0 && (
                  <div style={{ background: 'var(--surface)', border: '1px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden' }}>
                    <div style={{ padding: '16px 24px', background: 'rgba(251, 191, 36, 0.08)', borderBottom: '1px solid var(--glass-border)' }}>
                      <h3 style={{ color: 'var(--text)', fontSize: '18px', margin: 0 }}>🎵 Music ({selectedSaintData.music.length})</h3>
                    </div>
                    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                      {selectedSaintData.music.map((m, i) => (
                        <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                          <button onClick={() => handleSaintItemDelete(m.vIndex, 'musical_segments', m.mIndex)} style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px' }}>🗑️</button>
                          
                          <div style={{ marginBottom: '16px', color: 'var(--text-dim)', fontSize: '13px' }}>
                            Video: <strong>{m.video_title}</strong> <span style={{ opacity: 0.5 }}>({m.video_id})</span>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '40px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                              <div><label>Title</label><input value={m.name || ''} onChange={e => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'name', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                              <div><label>Saint</label><input value={m.saint || ''} onChange={e => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'saint', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                              <div><label>Type</label><input value={m.type || ''} onChange={e => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'type', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                              <div><label>Moral</label><input value={m.moral || ''} onChange={e => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} /></div>
                            </div>
                            
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px' }}>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <input type="number" value={m.start_time_seconds || 0} onChange={e => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                                <button onClick={() => captureTimeCommon('music', (t) => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'start_time_seconds', t))}>⏱️</button>
                                <button onClick={() => seekAndPlay(m.start_time_seconds || 0, m.video_id)} style={{ background: 'var(--gold-soft)', color: '#000', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                              </div>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <input type="number" value={m.end_time_seconds || 0} onChange={e => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100px' }} />
                                <button onClick={() => captureTimeCommon('music', (t) => handleSaintItemChange(m.vIndex, 'musical_segments', m.mIndex, 'end_time_seconds', t))}>⏱️</button>
                                <button onClick={() => seekAndPlay(m.end_time_seconds || 0, m.video_id)} style={{ background: 'var(--gold-soft)', color: '#000', border: 'none', borderRadius: '8px', padding: '0 12px' }}>▶</button>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

             </div>
          )}
          
        </div>
      </div>
    </div>
  );
}
"""

with open('AdminPanel.jsx', 'w') as f:
    f.write(code)

