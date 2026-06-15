import re

with open('AdminPanel.jsx', 'r') as f:
    content = f.read()

# 1. Add useMemo
content = content.replace(
    "import React, { useState, useEffect, useRef } from 'react';",
    "import React, { useState, useEffect, useRef, useMemo } from 'react';"
)

# 2. Add sortBy state near other states
state_injection = """  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [sortBy, setSortBy] = useState('alphabetical');"""
content = content.replace(
    "  const [loading, setLoading] = useState(false);\n  const [message, setMessage] = useState('');",
    state_injection
)

# 3. Add groupedData useMemo before the return statement
grouped_data_code = """
  // Grouping Logic
  const groupedData = useMemo(() => {
    const groups = {};
    
    stories.forEach((s, index) => {
      const saint = s.normalized_saint_name || s.character_or_saint || 'Unknown';
      if (!groups[saint]) groups[saint] = { stories: [], music: [] };
      groups[saint].stories.push({ ...s, originalIndex: index });
    });

    music.forEach((m, index) => {
      const saint = m.saint || 'Unknown';
      if (!groups[saint]) groups[saint] = { stories: [], music: [] };
      groups[saint].music.push({ ...m, originalIndex: index });
    });

    const groupsArray = Object.keys(groups).map(name => ({
      saint: name,
      stories: groups[name].stories,
      music: groups[name].music,
      totalItems: groups[name].stories.length + groups[name].music.length,
      totalMusic: groups[name].music.length
    }));

    if (sortBy === 'most_music') {
      groupsArray.sort((a, b) => b.totalMusic - a.totalMusic);
    } else if (sortBy === 'most_total') {
      groupsArray.sort((a, b) => b.totalItems - a.totalItems);
    } else {
      groupsArray.sort((a, b) => a.saint.localeCompare(b.saint));
    }

    return groupsArray;
  }, [stories, music, sortBy]);

  const getDurationString = (start, end) => {"""
content = content.replace(
    "  const getDurationString = (start, end) => {",
    grouped_data_code
)

# 4. Modify handleAddStory and handleAddMusic to accept saint name
add_functions = """  const handleAddStory = (saintName = '') => {
    setStories([...stories, { title: '', normalized_saint_name: saintName !== 'Unknown' ? saintName : '', start_time_seconds: 0, end_time_seconds: 0, moral: '' }]);
  };

  const handleAddMusic = (saintName = '') => {
    setMusic([...music, { name: '', saint: saintName !== 'Unknown' ? saintName : '', type: 'Bhajan', start_time_seconds: 0, end_time_seconds: 0, moral: '' }]);
  };"""
content = re.sub(
    r"  const handleAddStory = \(\) => \{.*?\};[\s\n]*const handleAddMusic = \(\) => \{.*?\};",
    add_functions,
    content,
    flags=re.DOTALL
)

# 5. Replace UI Forms Container
ui_start = content.find("{/* Edit Forms Container */}")
ui_end = content.find("</>", ui_start)

replacement_ui = """{/* Edit Forms Container */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', paddingBottom: '60px' }}>
                
                {/* Sort Controls */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', alignItems: 'center' }}>
                  <label style={{ color: 'var(--text-dim)', fontSize: '14px' }}>Sort By:</label>
                  <select 
                    value={sortBy} 
                    onChange={e => setSortBy(e.target.value)}
                    style={{ background: 'rgba(0,0,0,0.5)', color: '#fff', border: '1px solid var(--glass-border)', padding: '8px 16px', borderRadius: '8px', fontSize: '14px', outline: 'none' }}
                  >
                    <option value="alphabetical">Alphabetical</option>
                    <option value="most_music">Most Music Segments</option>
                    <option value="most_total">Most Total Items</option>
                  </select>
                </div>

                {groupedData.map((group, groupIdx) => (
                  <div key={groupIdx} style={{ background: 'var(--surface)', border: '1px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden' }}>
                    <div style={{ padding: '16px 24px', background: 'rgba(255, 255, 255, 0.05)', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{ fontSize: '24px' }}>🕉️</span>
                        <h3 style={{ color: 'var(--text)', fontSize: '20px', margin: 0 }}>{group.saint}</h3>
                      </div>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <span style={{ background: 'rgba(249, 115, 22, 0.2)', color: 'var(--saffron)', padding: '4px 10px', borderRadius: '999px', fontSize: '12px', fontWeight: 'bold' }}>📖 {group.stories.length} Stories</span>
                        <span style={{ background: 'rgba(251, 191, 36, 0.2)', color: 'var(--gold-soft)', padding: '4px 10px', borderRadius: '999px', fontSize: '12px', fontWeight: 'bold' }}>🎵 {group.music.length} Music</span>
                      </div>
                    </div>
                    
                    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
                      
                      {/* Group Stories */}
                      {group.stories.length > 0 && (
                        <div>
                          <h4 style={{ color: 'var(--saffron)', marginBottom: '16px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}><span>📖</span> Stories</h4>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {group.stories.map((s) => {
                              const i = s.originalIndex;
                              return (
                                <div key={`story-${i}`} style={{ background: 'rgba(255,255,255,0.02)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                                  <button onClick={() => handleDeleteStory(i)} title="Delete Story" style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px', fontSize: '16px', transition: 'all 0.2s' }}>🗑️</button>
                                  
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '40px' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                      <div>
                                        <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Title</label>
                                        <input type="text" value={s.title || ''} onChange={e => handleStoryChange(i, 'title', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                      </div>
                                      <div>
                                        <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Saint / Character</label>
                                        <input type="text" value={s.normalized_saint_name || s.character_or_saint || ''} onChange={e => handleStoryChange(i, 'normalized_saint_name', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                      </div>
                                    </div>
                                    <div>
                                      <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Moral</label>
                                      <input type="text" value={s.moral || ''} onChange={e => handleStoryChange(i, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                    </div>
                                    
                                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                          <input type="number" value={s.start_time_seconds || 0} onChange={e => handleStoryChange(i, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                          <button onClick={() => captureTime(i, 'start_time_seconds', 'story')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                        </div>
                                        <button onClick={() => seekAndPlay(s.start_time_seconds || 0)} style={{ background: 'var(--saffron)', color: '#fff', border: 'none', padding: '8px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}>▶ Test Start Time</button>
                                      </div>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                          <input type="number" value={s.end_time_seconds || 0} onChange={e => handleStoryChange(i, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                          <button onClick={() => captureTime(i, 'end_time_seconds', 'story')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                        </div>
                                        <button onClick={() => seekAndPlay(s.end_time_seconds || 0)} style={{ background: 'rgba(249, 115, 22, 0.15)', color: 'var(--saffron)', border: '1px solid var(--saffron)', padding: '8px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}>▶ Test End Time</button>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Group Music */}
                      {group.music.length > 0 && (
                        <div>
                          <h4 style={{ color: 'var(--gold-soft)', marginBottom: '16px', fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}><span>🎵</span> Musical Segments</h4>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {group.music.map((m) => {
                              const i = m.originalIndex;
                              return (
                                <div key={`music-${i}`} style={{ background: 'rgba(255,255,255,0.02)', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', position: 'relative' }}>
                                  <button onClick={() => handleDeleteMusic(i)} title="Delete Musical Segment" style={{ position: 'absolute', top: '12px', right: '12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#F87171', borderRadius: '8px', cursor: 'pointer', padding: '6px', fontSize: '16px', transition: 'all 0.2s' }}>🗑️</button>
                                  
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '40px' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                      <div>
                                        <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Type</label>
                                        <input type="text" value={m.type || ''} onChange={e => handleMusicChange(i, 'type', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px', border: '1px solid var(--gold-soft)' }} />
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
                                        <label style={{ fontSize: '12px', color: 'var(--text-dim)', marginBottom: '6px', display: 'block' }}>Moral</label>
                                        <input type="text" value={m.moral || ''} onChange={e => handleMusicChange(i, 'moral', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                      </div>
                                    </div>
                                    
                                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                          <input type="number" value={m.start_time_seconds || 0} onChange={e => handleMusicChange(i, 'start_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                          <button onClick={() => captureTime(i, 'start_time_seconds', 'music')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                        </div>
                                        <button onClick={() => seekAndPlay(m.start_time_seconds || 0)} style={{ background: 'var(--gold-soft)', color: '#000', border: 'none', padding: '8px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}>▶ Test Start Time</button>
                                      </div>
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                          <input type="number" value={m.end_time_seconds || 0} onChange={e => handleMusicChange(i, 'end_time_seconds', e.target.value)} className="premium-search-input" style={{ width: '100%', padding: '10px 14px', fontSize: '14px', background: 'rgba(0,0,0,0.4)', borderRadius: '8px' }} />
                                          <button onClick={() => captureTime(i, 'end_time_seconds', 'music')} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '0 12px', color: '#fff', cursor: 'pointer', fontSize: '16px' }}>⏱️</button>
                                        </div>
                                        <button onClick={() => seekAndPlay(m.end_time_seconds || 0)} style={{ background: 'rgba(251, 191, 36, 0.15)', color: 'var(--gold-soft)', border: '1px solid var(--gold-soft)', padding: '8px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}>▶ Test End Time</button>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Add Buttons for this group */}
                      <div style={{ display: 'flex', gap: '16px' }}>
                        <button onClick={() => handleAddStory(group.saint)} style={{ flex: 1, background: 'rgba(249, 115, 22, 0.1)', color: 'var(--saffron)', border: '1px dashed var(--saffron)', padding: '12px', borderRadius: '8px', fontSize: '14px', cursor: 'pointer', fontWeight: '600' }}>
                          ➕ Add Story here
                        </button>
                        <button onClick={() => handleAddMusic(group.saint)} style={{ flex: 1, background: 'rgba(251, 191, 36, 0.1)', color: 'var(--gold-soft)', border: '1px dashed var(--gold-soft)', padding: '12px', borderRadius: '8px', fontSize: '14px', cursor: 'pointer', fontWeight: '600' }}>
                          ➕ Add Music here
                        </button>
                      </div>

                    </div>
                  </div>
                ))}
                
                {/* Global Add Buttons */}
                <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
                  <button onClick={() => handleAddStory()} style={{ flex: 1, background: 'rgba(255, 255, 255, 0.05)', color: '#fff', border: '1px solid var(--glass-border)', padding: '16px', borderRadius: '12px', fontSize: '15px', cursor: 'pointer', fontWeight: '600' }}>
                    ➕ Add New Story (Unknown Saint)
                  </button>
                  <button onClick={() => handleAddMusic()} style={{ flex: 1, background: 'rgba(255, 255, 255, 0.05)', color: '#fff', border: '1px solid var(--glass-border)', padding: '16px', borderRadius: '12px', fontSize: '15px', cursor: 'pointer', fontWeight: '600' }}>
                    ➕ Add New Music Segment (Unknown Saint)
                  </button>
                </div>
              </div>
            </>"""

content = content[:ui_start] + replacement_ui + "\n" + content[ui_end:]

with open('AdminPanel.jsx', 'w') as f:
    f.write(content)
