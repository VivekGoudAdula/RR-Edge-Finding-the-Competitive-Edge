import React, { useState, useEffect, useRef } from 'react';

interface PlayerAvatarProps {
  playerId: number;
  playerName: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  isTop10?: boolean;
}

// Global cache of validated image URLs to prevent re-probing or avatar flashing
const validatedUrlCache = new Map<string, string>();
const failedPlayerCache = new Set<string>();

// Canonical Top 20 player mapping for instantaneous lookup and preloading
const TOP_PLAYERS: Array<{ id: number; slug: string }> = [
  { id: 6281, slug: 'abhishek-sharma' },
  { id: 4856, slug: 'benjamin-sears' },
  { id: 143, slug: 'dinesh-karthik' },
  { id: 39657, slug: 'eshan-malinga' },
  { id: 838, slug: 'glenn-maxwell' },
  { id: 4260, slug: 'heinrich-klaasen' },
  { id: 2933, slug: 'jasprit-bumrah' },
  { id: 8661, slug: 'matheesha-pathirana' },
  { id: 27960, slug: 'mayank-yadav' },
  { id: 2490, slug: 'mohammad-nawaz' },
  { id: 3125, slug: 'nicholas-pooran' },
  { id: 7967, slug: 'noor-ahmad' },
  { id: 5553, slug: 'phil-salt' },
  { id: 305, slug: 'ravichandran-ashwin' },
  { id: 781, slug: 'sunil-narine' },
  { id: 1699, slug: 'suryakumar-yadav' },
  { id: 6396, slug: 'tim-david' },
  { id: 50284, slug: 'vaibhav-sooryavanshi' },
  { id: 4900, slug: 'wanindu-hasaranga' },
  { id: 6819, slug: 'yashasvi-jaiswal' },
];

// Initialize and preload canonical player images
if (typeof window !== 'undefined') {
  TOP_PLAYERS.forEach(({ id, slug }) => {
    const webpUrl = `/players/${slug}.webp`;
    validatedUrlCache.set(slug, webpUrl);
    validatedUrlCache.set(String(id), webpUrl);
    validatedUrlCache.set(`${id}_${slug}`, webpUrl);

    const img = new Image();
    img.src = webpUrl;
    img.onload = () => {
      validatedUrlCache.set(slug, webpUrl);
      validatedUrlCache.set(String(id), webpUrl);
      validatedUrlCache.set(`${id}_${slug}`, webpUrl);
    };
  });
}

/**
 * Clean and normalize player name into URL-safe slug.
 */
function toSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export const PlayerAvatar: React.FC<PlayerAvatarProps> = ({
  playerId,
  playerName,
  size = 'sm',
  className = '',
  isTop10 = false,
}) => {
  const slug = toSlug(playerName);
  const cacheKey = `${playerId}_${slug}`;

  // Prioritize existing validated cache or predefined top player entry
  const cachedUrl =
    validatedUrlCache.get(cacheKey) ||
    validatedUrlCache.get(slug) ||
    validatedUrlCache.get(String(playerId));

  // Candidate image URLs prioritized for ultra-fast loading (WebP 15-20KB first, then PNG)
  const candidateUrls = [
    `/players/${slug}.webp`,
    `/players/${playerId}.webp`,
    `/players/${slug}.png`,
    `/players/${playerId}.png`,
    `/players/${slug}.jpg`,
    `/players/${playerId}.jpg`,
  ];

  const isPreFailed = failedPlayerCache.has(cacheKey);

  const [currentSrc, setCurrentSrc] = useState<string | null>(
    cachedUrl || (isPreFailed ? null : candidateUrls[0])
  );
  const [candidateIndex, setCandidateIndex] = useState<number>(
    cachedUrl ? candidateUrls.indexOf(cachedUrl) : 0
  );
  const [isFailed, setIsFailed] = useState<boolean>(isPreFailed);

  const indexRef = useRef(candidateIndex);
  indexRef.current = candidateIndex;
  const imgRef = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    const valid =
      validatedUrlCache.get(cacheKey) ||
      validatedUrlCache.get(slug) ||
      validatedUrlCache.get(String(playerId));

    if (valid) {
      setCurrentSrc(valid);
      setIsFailed(false);
      return;
    }
    if (failedPlayerCache.has(cacheKey)) {
      setIsFailed(true);
      setCurrentSrc(null);
      return;
    }

    setCandidateIndex(0);
    indexRef.current = 0;
    setCurrentSrc(candidateUrls[0]);
    setIsFailed(false);
  }, [playerId, slug]);

  const handleImageLoad = () => {
    if (currentSrc) {
      validatedUrlCache.set(cacheKey, currentSrc);
      validatedUrlCache.set(slug, currentSrc);
      validatedUrlCache.set(String(playerId), currentSrc);
    }
    setIsFailed(false);
  };

  const handleImageError = () => {
    const nextIndex = indexRef.current + 1;
    if (nextIndex < candidateUrls.length) {
      indexRef.current = nextIndex;
      setCandidateIndex(nextIndex);
      setCurrentSrc(candidateUrls[nextIndex]);
    } else {
      failedPlayerCache.add(cacheKey);
      setIsFailed(true);
      setCurrentSrc(null);
    }
  };

  // Immediate check if naturalWidth already loaded from cache
  useEffect(() => {
    if (imgRef.current && imgRef.current.complete && imgRef.current.naturalWidth > 0) {
      handleImageLoad();
    }
  }, [currentSrc]);

  // Compute initials fallback
  const initials = playerName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase();

  // Size styling maps
  const sizeClasses = {
    sm: 'w-10 h-10 text-xs',
    md: 'w-12 h-12 text-sm',
    lg: 'w-14 h-14 text-base font-bold',
    xl: 'w-16 h-16 text-lg font-black',
  };

  const selectedSizeClass = sizeClasses[size] || sizeClasses.sm;

  return (
    <div
      className={`relative rounded-full overflow-hidden shrink-0 flex items-center justify-center font-bold select-none bg-gradient-to-br from-rr-navy to-slate-800 text-white ${selectedSizeClass} ${
        isTop10 ? 'ring-2 ring-amber-400 shadow-sm' : 'ring-1 ring-slate-200'
      } ${className}`}
    >
      {/* Background Initials (immediate zero-latency fallback) */}
      <span className="tracking-wider">{initials}</span>

      {/* Foreground Image (loads eagerly, instantly covers placeholder) */}
      {!isFailed && currentSrc && (
        <img
          ref={imgRef}
          src={currentSrc}
          alt={playerName}
          loading="eager"
          decoding="async"
          onLoad={handleImageLoad}
          onError={handleImageError}
          className="absolute inset-0 w-full h-full object-cover"
        />
      )}
    </div>
  );
};
