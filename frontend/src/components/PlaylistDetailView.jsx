import React, { useState, useMemo } from 'react';
import MusicCard from './MusicCard';
import { getPlaylistTracks } from './PlaylistRow';
import './Playlist.css';

// ─── Helpers ──────────────────────────────────────────────────────────────────
const formatTime = (seconds) => {
  if (!seconds && seconds !== 0) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

// Marathi digit conversion for the count badge
const toMarathiDigits = (n) =>
  String(n).replace(/\d/g, d => '०१२३४५६७८९'[d]);

// ─── Alternate Recording Row ───────────────────────────────────────────────────
function AltRecordingRow({ track, lang }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [thumbSrc, setThumbSrc] = useState(
    `https://img.youtube.com/vi/${track.video_id}/mqdefault.jpg`
  );
  const displayName =
    lang === 'en' && track.name_english ? track.name_english : track.name;

  const toggle = () => setIsPlaying(p => !p);

  return (
    <div>
      <div
        className={`alt-recording-row${isPlaying ? ' playing' : ''}`}
        onClick={toggle}
        role="button"
        tabIndex={0}
        onKeyDown={e => e.key === 'Enter' && toggle()}
        aria-label={`Play alternate recording of ${displayName}`}
      >
        <div className="alt-thumb-wrapper">
          <img
            src={thumbSrc}
            alt={displayName}
            className="alt-thumb"
            loading="lazy"
            onError={() => {
              if (thumbSrc.includes('mqdefault'))
                setThumbSrc(`https://img.youtube.com/vi/${track.video_id}/0.jpg`);
            }}
          />
          <span className="alt-thumb-time">
            {formatTime(track.start_time_seconds)}
          </span>
        </div>

        <div className="alt-recording-info">
          <div className="alt-recording-label">
            अन्य ध्वनिमुद्रण • {formatTime(track.start_time_seconds)} पासून
          </div>
          <div className="alt-recording-name">{displayName}</div>
        </div>

        <button
          className={`alt-play-btn${isPlaying ? ' playing' : ''}`}
          aria-label={isPlaying ? 'Stop' : 'Play'}
          onClick={e => { e.stopPropagation(); toggle(); }}
        >
          {isPlaying ? '■' : '▶'}
        </button>
      </div>

      {isPlaying && (
        <div className="alt-inline-player">
          <iframe
            src={`https://www.youtube.com/embed/${track.video_id}?autoplay=1&start=${Math.floor(
              track.start_time_seconds || 0
            )}`}
            title={displayName}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      )}
    </div>
  );
}

// ─── Single Bhajan Group (primary card + sleek badge + optional alt recordings) ─────────────────
function BhajanGroup({ uniqueName, versions, nameCounts, playlist, lang }) {
  const [expanded, setExpanded] = useState(false);
  const primary = versions[0];
  const alts = versions.slice(1);
  const hasAlts = alts.length > 0;
  const singCount = playlist.showKakaCount && nameCounts ? nameCounts[uniqueName] : null;

  let badgeText = null;
  if (singCount && singCount > 1) {
    badgeText = `🎵 ${toMarathiDigits(singCount)} वेळा गायले`;
  } else if (versions.length > 1) {
    badgeText = `🎵 ${toMarathiDigits(versions.length)} ध्वनिमुद्रण`;
  }

  return (
    <div className="playlist-bhajan-group">
      <MusicCard track={primary} lang={lang} badgeText={badgeText} />

      {/* "Other Recordings" elegant expander */}
      {hasAlts && (
        <>
          <div
            className="other-recordings-toggle"
            onClick={() => setExpanded(e => !e)}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && setExpanded(x => !x)}
            aria-expanded={expanded}
            style={{ marginTop: '8px', marginBottom: '8px', justifyContent: 'center' }}
          >
            <span className="other-recordings-dot" />
            <span className="other-recordings-text">
              {expanded ? '▲ इतर ध्वनिमुद्रण लपवा' : `▼ ${toMarathiDigits(alts.length)} इतर ध्वनिमुद्रण पहा`}
            </span>
            <span className="other-recordings-dot" />
          </div>

          {expanded && (
            <div className="alt-recordings-list">
              {alts.map((track, i) => (
                <AltRecordingRow
                  key={`${track.video_id}-${track.start_time_seconds}-${i}`}
                  track={track}
                  lang={lang}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Main Playlist Detail View ────────────────────────────────────────────────
export default function PlaylistDetailView({
  playlist,
  segments,
  lang,
  onBack,
}) {
  const { segments: plSegs, nameCounts } = useMemo(
    () => getPlaylistTracks(playlist, segments),
    [playlist, segments]
  );

  // Deduplicate: group by name, preserving order of first occurrence
  const groups = useMemo(() => {
    const map = new Map();
    plSegs.forEach(seg => {
      if (!map.has(seg.name)) map.set(seg.name, []);
      map.get(seg.name).push(seg);
    });

    // For Kaka's favourites, sort by sing count descending
    const entries = Array.from(map.entries());
    if (playlist.showKakaCount && nameCounts) {
      entries.sort(
        ([a], [b]) => (nameCounts[b] || 0) - (nameCounts[a] || 0)
      );
    }
    return entries;
  }, [plSegs, playlist, nameCounts]);

  const totalUnique = groups.length;
  const totalVersions = plSegs.length;

  return (
    <div className="playlist-detail-view">
      {/* ── Header ── */}
      <div 
        className="playlist-detail-header-premium"
        style={{ background: `linear-gradient(to bottom, ${playlist.accentColor}40, transparent)` }}
      >
        <button
          className="playlist-close-x-btn"
          onClick={onBack}
          aria-label="Close playlist"
        >
          ✕
        </button>

        <div className="playlist-detail-cover" style={{ boxShadow: `0 12px 32px ${playlist.accentColor}40` }}>
          <img src={playlist.coverImage} alt={playlist.name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>

        <div className="playlist-detail-info">
          <div className="playlist-detail-title">
            {playlist.name}
          </div>
          <div className="playlist-detail-sub" style={{ fontSize: '1.05rem', color: 'rgba(255,255,255,0.8)', marginBottom: '16px' }}>
            {playlist.subtitle}
          </div>
          <div className="playlist-detail-pills">
            <span className="playlist-detail-pill" style={{ background: 'rgba(255,255,255,0.1)', borderColor: 'rgba(255,255,255,0.2)', color: '#fff' }}>
              {totalUnique} अनोखी भजने
            </span>
            {totalVersions > totalUnique && (
              <span className="playlist-detail-pill" style={{ background: 'rgba(255,255,255,0.1)', borderColor: 'rgba(255,255,255,0.2)', color: '#fff' }}>
                {totalVersions} एकूण ध्वनिमुद्रण
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Track List ── */}
      <div>
        {groups.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              padding: '60px 20px',
              color: 'var(--text-dim)',
              fontSize: '1rem',
            }}
          >
            कोणतीही भजने आढळली नाहीत.
          </div>
        ) : (
          groups.map(([name, versions]) => (
            <BhajanGroup
              key={name}
              uniqueName={name}
              versions={versions}
              nameCounts={nameCounts}
              playlist={playlist}
              lang={lang}
            />
          ))
        )}
      </div>
    </div>
  );
}
