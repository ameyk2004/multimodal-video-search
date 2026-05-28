import React from 'react';
import './Playlist.css';

// ─── Playlist Definitions ─────────────────────────────────────────────────────
export const PLAYLIST_DEFINITIONS = [
  {
    id: 'kakas-favourites',
    name: 'काकांची आवडती भजने',
    nameEn: "Kaka's Favourites",
    subtitle: 'श्री पेठे काकांनी वारंवार गायलेली भजने',
    icon: '🎵',
    coverImage: '/playlist_kakas.png',
    accentColor: '#FFD700',
    showKakaCount: true, // Show "Nx गायले" badge
  },
  {
    id: 'aarti-sangrah',
    name: 'आरती संग्रह',
    nameEn: 'Aarti Collection',
    subtitle: 'सर्व देवांच्या व संतांच्या आरत्या',
    icon: '🪔',
    coverImage: '/playlist_aarti.png',
    accentColor: '#C850C0',
    showKakaCount: false,
  },
  {
    id: 'namasmarana-mala',
    name: 'नामस्मरण माला',
    nameEn: 'Namasmarana Mala',
    subtitle: 'नाम जप, नामसंकीर्तन व नामस्मरण',
    icon: '📿',
    coverImage: '/playlist_namasmarana.png',
    accentColor: '#00B4D8',
    showKakaCount: false,
  },
  {
    id: 'sadguru-bhajane',
    name: 'सद्गुरू भजने',
    nameEn: 'Sadguru Bhajane',
    subtitle: 'श्री ब्रह्मचैतन्य गोंदवलेकर महाराज',
    icon: '🕊️',
    coverImage: '/playlist_sadguru.png',
    accentColor: '#FF416C',
    showKakaCount: false,
  },
  {
    id: 'tukaram-bhajane',
    name: 'तुकाराम गाथा',
    nameEn: 'Tukaram Gatha',
    subtitle: 'संत तुकाराम महाराज',
    icon: '🍃',
    coverImage: '/playlist_tukaram.png',
    accentColor: '#4CAF50',
    showKakaCount: false,
  },
];

// ─── Filter Logic ─────────────────────────────────────────────────────────────
// Returns { segments, nameCounts? }
export function getPlaylistTracks(playlist, allSegments) {
  switch (playlist.id) {
    case 'kakas-favourites': {
      // All segments in this dataset are sung by Kaka. We just want bhajans sung more than once.
      const bhajans = allSegments.filter(s => s.type === 'bhajan');
      const nameCounts = {};
      bhajans.forEach(s => {
        nameCounts[s.name] = (nameCounts[s.name] || 0) + 1;
      });
      const favNames = new Set(
        Object.keys(nameCounts).filter(k => nameCounts[k] > 1)
      );
      return {
        segments: bhajans.filter(s => favNames.has(s.name)),
        nameCounts,
      };
    }

    case 'aarti-sangrah':
      return { segments: allSegments.filter(s => s.type === 'aarti') };

    case 'namasmarana-mala':
      return {
        segments: allSegments.filter(
          s => s.name?.includes('नाम') || s.type === 'namasmarana'
        ),
      };

    case 'sadguru-bhajane':
      return {
        segments: allSegments.filter(
          s => s.saint === 'श्री ब्रह्मचैतन्य गोंदवलेकर महाराज'
        ),
      };

    case 'tukaram-bhajane':
      return {
        segments: allSegments.filter(
          s => s.saint === 'संत तुकाराम महाराज'
        ),
      };

    default:
      return { segments: [] };
  }
}

// ─── Component ────────────────────────────────────────────────────────────────
export default function PlaylistRow({ segments, onPlaylistSelect }) {
  return (
    <div className="playlist-section">
      <div className="playlist-section-header">
        <span className="playlist-section-badge">✦</span>
        <h2 className="playlist-section-title">संगीत संग्रह</h2>
        <span className="playlist-section-sub">५ याद्या</span>
      </div>

      <div className="playlist-scroll-row">
        {PLAYLIST_DEFINITIONS.map(pl => {
          const { segments: plSegs } = getPlaylistTracks(pl, segments);
          const uniqueCount = new Set(plSegs.map(s => s.name)).size;

          return (
            <div
              key={pl.id}
              className="playlist-chip"
              onClick={() => onPlaylistSelect(pl)}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && onPlaylistSelect(pl)}
              aria-label={`${pl.name} playlist`}
            >
              <div className="playlist-chip-cover">
                <img src={pl.coverImage} alt={pl.name} loading="lazy" />
                <div className="playlist-chip-icon-overlay">{pl.icon}</div>
              </div>
              <div className="playlist-chip-info">
                <div className="playlist-chip-name">{pl.name}</div>
                <div className="playlist-chip-sub">{uniqueCount} भजने</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
