import React, { useState, useEffect, useRef } from 'react';
import { api } from '../utils/api';

export default function AdminPanel() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [passcode, setPasscode] = useState('');
  
  const [videos, setVideos] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedVideoId, setSelectedVideoId] = useState('');
  
  const [videoData, setVideoData] = useState(null);
  const [stories, setStories] = useState([]);
  const [music, setMusic] = useState([]);
  
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

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

  useEffect(() => {
    if (!selectedVideoId) return;

    const loadPlayer = () => {
      if (window.YT && window.YT.Player) {
        if (!playerRef.current) {
          playerRef.current = new window.YT.Player('admin-yt-player', {
            videoId: selectedVideoId,
            playerVars: { enablejsapi: 1, autoplay: 0 },
            events: {
              onReady: () => console.log('YouTube Player Ready')
            }
          });
        } else {
          playerRef.current.loadVideoById(selectedVideoId);
        }
      } else {
        setTimeout(loadPlayer, 500);
      }
    };

    loadPlayer();
  }, [selectedVideoId]);

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
    } catch (err) {
      console.error(err);
      setMessage('Failed to save changes.');
    } finally {
      setLoading(false);
    }
  };

  const seekAndPlay = (seconds) => {
    if (playerRef.current && playerRef.current.seekTo) {
      playerRef.current.seekTo(seconds, true);
      playerRef.current.playVideo();
    }
  };

  const captureTime = (index, field, type) => {
    if (playerRef.current && playerRef.current.getCurrentTime) {
      const currentTime = Math.floor(playerRef.current.getCurrentTime());
      if (type === 'story') {
        handleStoryChange(index, field, currentTime);
      } else {
        handleMusicChange(index, field, currentTime);
      }
    } else {
      alert("Please play the video first so the player is ready.");
    }
  };

  // Filter logic
  const filteredVideos = videos.filter(v => {
    const term = searchTerm.toLowerCase();
    if (!term) return true;
    
    if (v.title?.toLowerCase().includes(term)) return true;
    if (v.video_id?.toLowerCase().includes(term)) return true;
    
    if (v.stories && v.stories.some(s => s.title?.toLowerCase().includes(term) || s.normalized_saint_name?.toLowerCase().includes(term) || s.character_or_saint?.toLowerCase().includes(term))) return true;
    if (v.musical_segments && v.musical_segments.some(m => m.name?.toLowerCase().includes(term) || m.saint?.toLowerCase().includes(term))) return true;
    
    return false;
  });

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
        <div style={{ 
          background: 'var(--surface)', 
          backdropFilter: 'blur(24px)', 
          border: '1px solid var(--glass-border)', 
          padding: '50px 40px', 
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 20px 50px rgba(0,0,0,0.5)',
          maxWidth: '400px',
          width: '100%',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px', filter: 'drop-shadow(0 0 12px rgba(249, 115, 22, 0.6))' }}>🪔</div>
          <h2 style={{ marginBottom: '10px', color: 'var(--text)', fontFamily: 'var(--font-head)' }}>Admin Access</h2>
          <p style={{ marginBottom: '30px', color: 'var(--text-dim)' }}>Please enter the passcode to access the editor.</p>
          <form onSubmit={handleLogin}>
            <input 
              type="password" 
              value={passcode}
              onChange={e => setPasscode(e.target.value)}
              className="premium-search-input"
              placeholder="Passcode"
              style={{ width: '100%', marginBottom: '20px', textAlign: 'center', background: 'rgba(255,255,255,0.05)' }}
            />
            <button type="submit" className="search-btn" style={{ width: '100%', borderRadius: '12px', height: '48px' }}>Login</button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', color: '#fff', width: '100%', maxWidth: '1800px', margin: '0 auto', animation: 'fade-up 0.5s ease both' }}>
      
      {/* 2-Column Desktop Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(250px, 320px) 1fr', gap: '32px', alignItems: 'start' }}>
        
        {/* COL 1: Video List (Left Panel) */}
        <div style={{ position: 'sticky', top: '20px', height: 'calc(100vh - 40px)', display: 'flex', flexDirection: 'column', background: 'var(--bg-mid)', borderRadius: '16px', border: '1px solid var(--glass-border)', overflow: 'hidden' }}>
          <div style={{ padding: '20px', borderBottom: '1px solid var(--glass-border)', background: 'var(--surface)' }}>
            <h1 style={{ color: 'var(--gold-soft)', fontSize: '24px', margin: 0 }}>Timestamp Editor</h1>
            <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: '4px 0 0 0' }}>Select a video to edit</p>
          </div>
          <div style={{ padding: '12px', borderBottom: '1px solid var(--glass-border)' }}>
             <input 
                type="text" 
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="Search ID, Title, Story, Bhajan..."
                className="premium-search-input"
                style={{ width: '100%', padding: '8px 12px', fontSize: '13px', background: 'rgba(0,0,0,0.5)', borderRadius: '8px' }}
             />
          </div>
          <div style={{ overflowY: 'auto', padding: '12px', flex: 1 }}>
            {filteredVideos.length === 0 ? (
              <div style={{ color: 'var(--text-dim)', padding: '10px', textAlign: 'center' }}>No videos match your search</div>
            ) : (
              filteredVideos.map((v, index) => (
                <div 
                  key={v.video_id} 
                  onClick={() => handleVideoSelect(v.video_id)}
                  style={{ 
                    padding: '12px', 
                    cursor: 'pointer', 
                    borderRadius: '8px',
                    marginBottom: '8px',
                    background: selectedVideoId === v.video_id ? 'rgba(249, 115, 22, 0.15)' : 'transparent',
                    border: selectedVideoId === v.video_id ? '1px solid var(--saffron)' : '1px solid transparent',
                    color: selectedVideoId === v.video_id ? '#fff' : 'var(--text-dim)',
                    transition: 'all 0.2s',
                    display: 'flex',
                    gap: '12px',
                    alignItems: 'center'
                  }}
                  onMouseEnter={e => { if(selectedVideoId !== v.video_id) e.currentTarget.style.background = 'rgba(255,255,255,0.05)' }}
                  onMouseLeave={e => { if(selectedVideoId !== v.video_id) e.currentTarget.style.background = 'transparent' }}
                >
                  <span style={{ color: 'var(--saffron)', fontWeight: 'bold', fontSize: '14px' }}>{index + 1}.</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontWeight: '500', fontSize: '14px' }}>{v.title}</div>
                    <div style={{ fontSize: '11px', opacity: 0.6, marginTop: '2px' }}>{v.video_id}</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* COL 2: Player & Forms (Right Panel) */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          
          {!selectedVideoId && (
            <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-dim)', border: '1px dashed var(--glass-border)', borderRadius: '16px', marginTop: '20px' }}>
              Select a video from the list on the left to start editing.
            </div>
          )}

          {selectedVideoId && (
            <>
              {/* Sticky Top Bar: Video + Actions */}
              <div style={{ position: 'sticky', top: '0', zIndex: 50, background: 'var(--bg-deep)', padding: '20px 0', borderBottom: '1px solid var(--glass-border)', display: 'flex', gap: '32px', alignItems: 'flex-start', margin: '-20px -20px 24px -20px' }}>
                <div style={{ paddingLeft: '20px', display: 'flex', gap: '32px', width: '100%', alignItems: 'center', justifyContent: 'space-between', paddingRight: '20px' }}>
                  
                  {/* Small Sticky Video Player */}
                  <div style={{ width: '400px', flexShrink: 0, background: 'var(--bg-mid)', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--glass-border)', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
                    <div style={{ position: 'relative', width: '100%', paddingTop: '56.25%', background: '#000' }}>
                      <div id="admin-yt-player" style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}></div>
                    </div>
                  </div>
                  
                  {/* Action Panel */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'flex-end', flex: 1 }}>
                    <div style={{ textAlign: 'right' }}>
                      <h2 style={{ fontSize: '20px', margin: '0 0 8px 0', color: '#fff' }}>Editing: {videoData?.title || selectedVideoId}</h2>
                      <p style={{ fontSize: '13px', color: 'var(--text-dim)', margin: 0 }}>Use the form below to update timestamps and text content.</p>
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      {message && (
                        <div style={{ 
                          padding: '8px 16px', 
                          background: message.includes('Success') ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
                          color: message.includes('Success') ? '#4ADE80' : '#F87171',
                          border: message.includes('Success') ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)', 
                          borderRadius: '8px', 
                          fontSize: '14px',
                          fontWeight: '500'
                        }}>
                          {message.includes('Success') ? '✓' : '⚠'} {message}
                        </div>
                      )}
                      {loading && <div style={{ color: 'var(--saffron)', fontSize: '14px' }}>Syncing...</div>}
                      <button 
                        onClick={handleSave} 
                        disabled={!selectedVideoId || loading}
                        style={{ 
                          background: 'linear-gradient(135deg, var(--saffron), var(--saffron-dim))',
                          color: '#fff',
                          border: 'none',
                          padding: '0 32px', 
                          borderRadius: '8px', 
                          fontSize: '15px', 
                          fontWeight: '600', 
                          height: '44px', 
                          cursor: (!selectedVideoId || loading) ? 'not-allowed' : 'pointer',
                          opacity: (!selectedVideoId || loading) ? 0.5 : 1,
                          boxShadow: '0 4px 15px rgba(249, 115, 22, 0.4)',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        Save Changes
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Edit Forms Container */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', paddingBottom: '60px' }}>
                
                {/* Stories */}
                <div style={{ background: 'var(--surface)', border: '1px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden' }}>
                  <div style={{ padding: '16px 24px', background: 'rgba(249, 115, 22, 0.08)', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '20px' }}>📖</span>
                    <h3 style={{ color: 'var(--text)', fontSize: '18px', margin: 0 }}>Stories</h3>
                    <span style={{ background: 'var(--saffron)', color: '#fff', padding: '2px 8px', borderRadius: '999px', fontSize: '12px', fontWeight: 'bold' }}>{stories.length}</span>
                  </div>
                  
                  <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {stories.map((s, i) => (
                      <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                        <div style={{ position: 'absolute', top: '-12px', left: '-12px', width: '28px', height: '28px', background: 'var(--bg-mid)', border: '1px solid var(--glass-border)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', color: 'var(--saffron)', fontWeight: 'bold' }}>{i+1}</div>
                        <button 
                          onClick={() => handleDeleteStory(i)} 
                          title="Delete Story"
                          style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px', fontSize: '16px', transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                          onMouseEnter={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'}
                          onMouseLeave={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
                        >
                          🗑️
                        </button>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
                          
                          {/* Metadata Col */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div>
                              <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Title</label>
                              <input type="text" value={s.title || ''} onChange={e => handleStoryChange(i, 'title', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                            </div>
                            <div>
                              <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Saint / Character</label>
                              <input type="text" value={s.normalized_saint_name || s.character_or_saint || ''} onChange={e => handleStoryChange(i, 'normalized_saint_name', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                            </div>
                            <div>
                              <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Moral</label>
                              <input type="text" value={s.moral || ''} onChange={e => handleStoryChange(i, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                            </div>
                          </div>
                        </div>
                        
                        {/* Time Controls (Full Width Bottom) */}
                        <div style={{ marginTop: '24px', background: 'rgba(0,0,0,0.3)', padding: '16px 20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                             <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--saffron)' }}>Timestamps</div>
                             <div style={{ fontSize: '13px', background: 'rgba(255,255,255,0.1)', padding: '4px 10px', borderRadius: '6px', color: 'var(--text-dim)' }}>
                                Duration: <strong style={{ color: '#fff' }}>{getDurationString(s.start_time_seconds, s.end_time_seconds)}</strong>
                             </div>
                          </div>
                          
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              <div>
                                <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Start Time (sec)</label>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <input type="number" value={s.start_time_seconds || 0} onChange={e => handleStoryChange(i, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                  <button onClick={() => captureTime(i, 'start_time_seconds', 'story')} title="Capture current player time" style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                </div>
                              </div>
                              <button onClick={() => seekAndPlay(s.start_time_seconds || 0)} style={{ background: 'var(--saffron)', color: '#fff', border: 'none', padding: '10px 16px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer', width: '100%', fontWeight: 'bold', transition: 'all 0.2s' }}>
                                ▶ Test Start Time
                              </button>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              <div>
                                <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>End Time (sec)</label>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <input type="number" value={s.end_time_seconds || 0} onChange={e => handleStoryChange(i, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                  <button onClick={() => captureTime(i, 'end_time_seconds', 'story')} title="Capture current player time" style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                </div>
                              </div>
                              <button onClick={() => seekAndPlay(s.end_time_seconds || 0)} style={{ background: 'rgba(249, 115, 22, 0.15)', color: 'var(--saffron)', border: '1px solid var(--saffron)', padding: '10px 16px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer', width: '100%', fontWeight: 'bold', transition: 'all 0.2s' }}>
                                ▶ Test End Time
                              </button>
                            </div>
                          </div>
                        </div>
                        
                      </div>
                    ))}
                    {stories.length === 0 && <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '20px 0' }}>No stories attached.</p>}
                    <button 
                      onClick={handleAddStory}
                      style={{ background: 'rgba(249, 115, 22, 0.1)', color: 'var(--saffron)', border: '1px dashed var(--saffron)', padding: '16px', borderRadius: '12px', fontSize: '15px', cursor: 'pointer', width: '100%', fontWeight: '600', transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(249, 115, 22, 0.2)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'rgba(249, 115, 22, 0.1)'}
                    >
                      <span>➕</span> Add New Story
                    </button>
                  </div>
                </div>

                {/* Musical Segments */}
                <div style={{ background: 'var(--surface)', border: '1px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden' }}>
                  <div style={{ padding: '16px 24px', background: 'rgba(251, 191, 36, 0.08)', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '20px' }}>🎵</span>
                    <h3 style={{ color: 'var(--text)', fontSize: '18px', margin: 0 }}>Musical Segments</h3>
                    <span style={{ background: 'var(--gold-soft)', color: '#000', padding: '2px 8px', borderRadius: '999px', fontSize: '12px', fontWeight: 'bold' }}>{music.length}</span>
                  </div>
                  
                  <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {music.map((m, i) => (
                      <div key={i} style={{ background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                        <div style={{ position: 'absolute', top: '-12px', left: '-12px', width: '28px', height: '28px', background: 'var(--bg-mid)', border: '1px solid var(--glass-border)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', color: 'var(--gold-soft)', fontWeight: 'bold' }}>{i+1}</div>
                        <button 
                          onClick={() => handleDeleteMusic(i)} 
                          title="Delete Musical Segment"
                          style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px', fontSize: '16px', transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                          onMouseEnter={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'}
                          onMouseLeave={e => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'}
                        >
                          🗑️
                        </button>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
                          
                          {/* Metadata Col */}
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div>
                              <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Type (e.g., Bhajan, Aarti)</label>
                              <input type="text" value={m.type || ''} onChange={e => handleMusicChange(i, 'type', e.target.value)} placeholder="Bhajan, Aarti, Shloka..." className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid var(--gold-soft)' }} />
                            </div>
                            <div>
                              <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Title</label>
                              <input type="text" value={m.name || ''} onChange={e => handleMusicChange(i, 'name', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                            </div>
                            <div>
                              <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Saint / Author</label>
                              <input type="text" value={m.saint || ''} onChange={e => handleMusicChange(i, 'saint', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                            </div>
                            <div>
                              <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Theme / Moral</label>
                              <input type="text" value={m.moral || ''} onChange={e => handleMusicChange(i, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                            </div>
                          </div>
                        </div>
                        
                        {/* Time Controls */}
                        <div style={{ marginTop: '24px', background: 'rgba(0,0,0,0.3)', padding: '16px 20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                             <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--gold-soft)' }}>Timestamps</div>
                             <div style={{ fontSize: '13px', background: 'rgba(255,255,255,0.1)', padding: '4px 10px', borderRadius: '6px', color: 'var(--text-dim)' }}>
                                Duration: <strong style={{ color: '#fff' }}>{getDurationString(m.start_time_seconds, m.end_time_seconds)}</strong>
                             </div>
                          </div>
                          
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              <div>
                                <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Start Time (sec)</label>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <input type="number" value={m.start_time_seconds || 0} onChange={e => handleMusicChange(i, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                  <button onClick={() => captureTime(i, 'start_time_seconds', 'music')} title="Capture current player time" style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                </div>
                              </div>
                              <button onClick={() => seekAndPlay(m.start_time_seconds || 0)} style={{ background: 'var(--gold-soft)', color: '#000', border: 'none', padding: '10px 16px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer', width: '100%', fontWeight: 'bold', transition: 'all 0.2s' }}>
                                ▶ Test Start Time
                              </button>
                            </div>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                              <div>
                                <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>End Time (sec)</label>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                  <input type="number" value={m.end_time_seconds || 0} onChange={e => handleMusicChange(i, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                  <button onClick={() => captureTime(i, 'end_time_seconds', 'music')} title="Capture current player time" style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                </div>
                              </div>
                              <button onClick={() => seekAndPlay(m.end_time_seconds || 0)} style={{ background: 'rgba(251, 191, 36, 0.15)', color: 'var(--gold-soft)', border: '1px solid var(--gold-soft)', padding: '10px 16px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer', width: '100%', fontWeight: 'bold', transition: 'all 0.2s' }}>
                                ▶ Test End Time
                              </button>
                            </div>
                          </div>
                        </div>
                        
                      </div>
                    ))}
                    {music.length === 0 && <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '20px 0' }}>No musical segments attached.</p>}
                    <button 
                      onClick={handleAddMusic}
                      style={{ background: 'rgba(251, 191, 36, 0.1)', color: 'var(--gold-soft)', border: '1px dashed var(--gold-soft)', padding: '16px', borderRadius: '12px', fontSize: '15px', cursor: 'pointer', width: '100%', fontWeight: '600', transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(251, 191, 36, 0.2)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'rgba(251, 191, 36, 0.1)'}
                    >
                      <span>➕</span> Add New Musical Segment
                    </button>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
        
      </div>
    </div>
  );
}
