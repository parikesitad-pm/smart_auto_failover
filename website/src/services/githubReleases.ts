import {
  PlatformId,
  GitHubRelease,
  GitHubAsset,
  PlatformReleaseInfo,
  ResolvedRelease,
} from '../types/releases';

const REPO_OWNER = 'parikesitad-pm';
const REPO_NAME = 'smart_auto_failover';
const API_URL = `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases`;
const FALLBACK_RELEASES_URL = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases`;
const CACHE_KEY = 'autofailover_release_cache_v8';

// Immediately purge stale legacy cache keys
if (typeof window !== 'undefined') {
  try {
    localStorage.removeItem('autofailover_release_cache');
    localStorage.removeItem('autofailover_release_cache_v2');
    localStorage.removeItem('autofailover_release_cache_v3');
    localStorage.removeItem('autofailover_release_cache_v4');
    localStorage.removeItem('autofailover_release_cache_v5');
    localStorage.removeItem('autofailover_release_cache_v6');
    localStorage.removeItem('autofailover_release_cache_v7');
  } catch {
    // ignore
  }
}

export interface ParsedReleaseVersion {
  major: number;
  minor: number;
  patch: number;
  preview: number;
  isPrerelease: boolean;
  raw: string;
}

export function parseReleaseTag(tag: string): ParsedReleaseVersion | null {
  if (!tag) return null;
  const clean = tag.trim();
  // Filter out any web-only or non-desktop releases
  if (clean.startsWith('web-')) return null;

  // Match: v3.0.0, 3.0.0, v3.0.0-preview.20, 3.0.0-preview.9
  const match = clean.match(/^v?(\d+)\.(\d+)\.(\d+)(?:-preview\.(\d+))?$/i);
  if (!match) return null;

  return {
    major: parseInt(match[1], 10),
    minor: parseInt(match[2], 10),
    patch: parseInt(match[3], 10),
    preview: match[4] !== undefined ? parseInt(match[4], 10) : 0,
    isPrerelease: match[4] !== undefined,
    raw: clean,
  };
}

export function compareReleaseVersions(
  a: ParsedReleaseVersion,
  b: ParsedReleaseVersion
): number {
  if (a.major !== b.major) return a.major - b.major;
  if (a.minor !== b.minor) return a.minor - b.minor;
  if (a.patch !== b.patch) return a.patch - b.patch;

  // For same major.minor.patch:
  // Stable releases rank higher than prereleases
  if (!a.isPrerelease && b.isPrerelease) return 1;
  if (a.isPrerelease && !b.isPrerelease) return -1;

  // Numeric preview comparison (e.g. preview.20 > preview.18 > preview.9)
  return a.preview - b.preview;
}

export function detectUserPlatform(): PlatformId {
  if (typeof window === 'undefined') return 'linux';
  const ua = navigator.userAgent.toLowerCase();
  const plat = (navigator.platform || '').toLowerCase();

  if (plat.includes('win') || ua.includes('windows')) {
    return 'windows';
  }
  if (plat.includes('mac') || ua.includes('macintosh')) {
    return 'macos-arm64';
  }
  return 'linux';
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export async function fetchLiveReleases(
  detected: PlatformId
): Promise<ResolvedRelease | null> {
  try {
    // Bust browser HTTP cache with timestamp parameter
    const url = `${API_URL}?per_page=30&_nocache=${Date.now()}`;
    const res = await fetch(url, {
      headers: {
        Accept: 'application/vnd.github.v3+json',
      },
    });

    if (res.ok) {
      const releases: GitHubRelease[] = await res.json();
      const resolved = resolveReleaseFromList(releases, detected);
      if (resolved) {
        try {
          localStorage.setItem(
            CACHE_KEY,
            JSON.stringify({ timestamp: Date.now(), data: resolved })
          );
        } catch {
          // ignore cache write errors
        }
        return resolved;
      }
    }
  } catch (err) {
    console.warn('Failed to fetch live GitHub releases:', err);
  }
  return null;
}

/**
 * Stale-While-Revalidate pattern:
 * Returns cached or fallback data quickly, while always requesting the latest
 * live release from the GitHub API and notifying onUpdate if a newer release arrives.
 */
export async function getLatestAutoFailoverRelease(
  onUpdate?: (fresh: ResolvedRelease) => void
): Promise<ResolvedRelease> {
  const detected = detectUserPlatform();
  const fallback = createFallbackRelease(detected);

  // 1. Read cached release
  let cachedRelease: ResolvedRelease | null = null;
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (cached) {
      const parsed = JSON.parse(cached);
      if (parsed && parsed.data) {
        cachedRelease = parsed.data;
      }
    }
  } catch {
    // ignore cache read errors
  }

  // 2. Always trigger background live fetch
  const livePromise = fetchLiveReleases(detected).then((fresh) => {
    if (fresh) {
      // Check if fresh is newer than what we had
      if (onUpdate) {
        onUpdate(fresh);
      }
      return fresh;
    }
    return cachedRelease || fallback;
  });

  // If we have a cached release that is at least as new as our fallback, present it immediately
  if (cachedRelease) {
    const pCached = parseReleaseTag(cachedRelease.tagName);
    const pFallback = parseReleaseTag(fallback.tagName);
    if (
      pCached &&
      pFallback &&
      compareReleaseVersions(pCached, pFallback) >= 0
    ) {
      // Background promise will still revalidate and call onUpdate if even newer
      return cachedRelease;
    }
  }

  // Otherwise, wait directly for live network fetch to guarantee fresh version
  const fresh = await livePromise;
  return fresh || fallback;
}

export function resolveSingleRelease(
  selected: GitHubRelease,
  detected: PlatformId
): ResolvedRelease {
  const channel: 'STABLE' | 'BETA' | 'PREVIEW' = selected.tag_name.includes('preview.26')
    ? 'BETA'
    : selected.prerelease
      ? 'PREVIEW'
      : 'STABLE';
  const assets: GitHubAsset[] = selected.assets || [];

  // Find Checksums asset
  const checksumsAsset = assets.find((a) =>
    a.name.toLowerCase().includes('sha256')
  );

  // Match platform assets
  const winAsset = assets.find(
    (a) =>
      (a.name.toLowerCase().includes('windows') || a.name.endsWith('.exe')) &&
      a.name.endsWith('.zip')
  );

  const linuxAsset = assets.find(
    (a) =>
      a.name.toLowerCase().includes('linux') &&
      (a.name.endsWith('.tar.gz') || a.name.endsWith('.tgz'))
  );

  const macArmAsset = assets.find(
    (a) =>
      a.name.toLowerCase().includes('macos') &&
      a.name.toLowerCase().includes('arm64') &&
      a.name.endsWith('.dmg')
  );

  const macX64Asset = assets.find(
    (a) =>
      a.name.toLowerCase().includes('macos') &&
      a.name.toLowerCase().includes('x64') &&
      a.name.endsWith('.dmg')
  );

  const ver = selected.tag_name.replace(/^v/, '');
  const displayVer =
    channel === 'BETA'
      ? `AutoFailover 3.0 Beta (${ver})`
      : `AutoFailover ${ver}`;

  const platforms: Record<PlatformId, PlatformReleaseInfo> = {
    windows: {
      platformId: 'windows',
      platformName: 'Windows',
      arch: 'x64 (Windows 10 / 11)',
      available: Boolean(winAsset),
      version: displayVer,
      channel,
      assetName: winAsset?.name || `AutoFailover-${ver}-Windows-x64.zip`,
      downloadUrl:
        winAsset?.browser_download_url ||
        `${FALLBACK_RELEASES_URL}/tag/${selected.tag_name}`,
      sizeFormatted: winAsset ? formatBytes(winAsset.size) : undefined,
      validationStatus:
        channel === 'BETA' ? 'Beta Release Ready' : 'Release Ready',
      isRecommended: detected === 'windows',
      description:
        'Native PowerShell NetTCPIP HAL. Clean zero-linger socket teardown.',
    },
    linux: {
      platformId: 'linux',
      platformName: 'Linux',
      arch: 'x86_64 / glibc 2.31+',
      available: Boolean(linuxAsset),
      version: displayVer,
      channel,
      assetName: linuxAsset?.name || `AutoFailover-${ver}-Linux-x86_64.tar.gz`,
      downloadUrl:
        linuxAsset?.browser_download_url ||
        `${FALLBACK_RELEASES_URL}/tag/${selected.tag_name}`,
      sizeFormatted: linuxAsset ? formatBytes(linuxAsset.size) : undefined,
      validationStatus: 'Real-Host Validated',
      isRecommended: detected === 'linux',
      description:
        'Native Linux Netlink & sysfs prober. Verified on physical workstation.',
    },
    'macos-arm64': {
      platformId: 'macos-arm64',
      platformName: 'macOS Apple Silicon',
      arch: 'arm64 (M1/M2/M3/M4)',
      available: Boolean(macArmAsset),
      version: displayVer,
      channel,
      assetName: macArmAsset?.name || `AutoFailover-${ver}-macOS-arm64.dmg`,
      downloadUrl:
        macArmAsset?.browser_download_url ||
        `${FALLBACK_RELEASES_URL}/tag/${selected.tag_name}`,
      sizeFormatted: macArmAsset ? formatBytes(macArmAsset.size) : undefined,
      validationStatus: 'Release Ready',
      isRecommended: detected === 'macos-arm64',
      description:
        'Native BSD route & networksetup HAL. Official Apple Silicon package.',
    },
    'macos-x64': {
      platformId: 'macos-x64',
      platformName: 'macOS Intel',
      arch: 'x64 (Intel Mac)',
      available: Boolean(macX64Asset),
      version: displayVer,
      channel,
      assetName: macX64Asset?.name || `AutoFailover-${ver}-macOS-x64.dmg`,
      downloadUrl:
        macX64Asset?.browser_download_url ||
        `${FALLBACK_RELEASES_URL}/tag/${selected.tag_name}`,
      sizeFormatted: macX64Asset ? formatBytes(macX64Asset.size) : undefined,
      validationStatus: 'Available for Testing',
      isRecommended: false,
      description: 'Native Intel macOS build. Unsigned release package.',
    },
  };

  const titlePrefix =
    channel === 'BETA' ? 'AutoFailover 3.0 Beta' : 'AutoFailover';

  return {
    tagName: selected.tag_name,
    releaseTitle: selected.name || `${titlePrefix} (${selected.tag_name})`,
    channel,
    publishedAt: selected.published_at,
    htmlUrl: selected.html_url,
    commitSha: selected.target_commitish,
    releaseNotes: selected.body,
    checksumsUrl: checksumsAsset?.browser_download_url,
    platforms,
    isFallback: false,
  };
}

export function resolveReleaseFromList(
  releases: GitHubRelease[],
  detected: PlatformId
): ResolvedRelease | null {
  const all = resolveAllReleasesFromList(releases, detected);
  return all.length > 0 ? all[0] : null;
}

export function resolveAllReleasesFromList(
  releases: GitHubRelease[],
  detected: PlatformId
): ResolvedRelease[] {
  const parsedList = releases
    .map((r) => ({
      release: r,
      parsed: parseReleaseTag(r.tag_name),
    }))
    .filter(
      (
        item
      ): item is { release: GitHubRelease; parsed: ParsedReleaseVersion } =>
        item.parsed !== null
    );

  if (parsedList.length === 0) return [];

  // Sort descending: highest version first using numeric comparison
  parsedList.sort((a, b) => compareReleaseVersions(b.parsed, a.parsed));

  return parsedList.map((item) => resolveSingleRelease(item.release, detected));
}

export function createFallbackRelease(detected: PlatformId): ResolvedRelease {
  const latestTag = 'v3.1.0';
  const ver = '3.1.0';
  const releaseUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/tag/${latestTag}`;
  const downloadBase = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${latestTag}`;

  return {
    tagName: latestTag,
    releaseTitle: 'AutoFailover 3.1.0 Release (v3.1.0)',
    channel: 'STABLE',
    publishedAt: '2026-09-14T02:00:00Z',
    htmlUrl: releaseUrl,
    releaseNotes:
      'Official multi-platform desktop release packages for AutoFailover 3.1.0 by Modula with 4-stage interface deck presentation pipeline, dynamic card order retention, Zoom/vMix stability guarantee, and enterprise open-source documentation.',
    isFallback: true,
    checksumsUrl: `${downloadBase}/SHA256SUMS.txt`,
    platforms: {
      windows: {
        platformId: 'windows',
        platformName: 'Windows',
        arch: 'x64 (Windows 10 / 11)',
        available: true,
        version: `AutoFailover ${ver}`,
        channel: 'STABLE',
        assetName: `AutoFailover-${ver}-Windows-x64.zip`,
        downloadUrl: `${downloadBase}/AutoFailover-${ver}-Windows-x64.zip`,
        validationStatus: 'Release Ready',
        isRecommended: detected === 'windows',
        description: 'Native Windows executable package with NetTCPIP HAL.',
      },
      linux: {
        platformId: 'linux',
        platformName: 'Linux',
        arch: 'x86_64 / glibc 2.31+',
        available: true,
        version: `AutoFailover ${ver}`,
        channel: 'STABLE',
        assetName: `AutoFailover-${ver}-Linux-x86_64.tar.gz`,
        downloadUrl: `${downloadBase}/AutoFailover-${ver}-Linux-x86_64.tar.gz`,
        validationStatus: 'Release Ready (Real-Host Validated)',
        isRecommended: detected === 'linux',
        description: 'Native Linux standalone archive with Netlink prober.',
      },
      'macos-arm64': {
        platformId: 'macos-arm64',
        platformName: 'macOS Apple Silicon',
        arch: 'arm64 (M1/M2/M3/M4)',
        available: true,
        version: `AutoFailover ${ver}`,
        channel: 'STABLE',
        assetName: `AutoFailover-${ver}-macOS-arm64.dmg`,
        downloadUrl: `${downloadBase}/AutoFailover-${ver}-macOS-arm64.dmg`,
        validationStatus: 'Release Ready',
        isRecommended: detected === 'macos-arm64',
        description: 'Native Apple Silicon disk image (.dmg) with BSD route HAL.',
      },
      'macos-x64': {
        platformId: 'macos-x64',
        platformName: 'macOS Intel',
        arch: 'x64 (Intel)',
        available: true,
        version: `AutoFailover ${ver}`,
        channel: 'STABLE',
        assetName: `AutoFailover-${ver}-macOS-x64.dmg`,
        downloadUrl: `${downloadBase}/AutoFailover-${ver}-macOS-x64.dmg`,
        validationStatus: 'Release Ready',
        isRecommended: detected === 'macos-x64',
        description: 'Native Intel macOS disk image (.dmg).',
      },
    },
  };
}

export function createFallbackReleasesHistory(
  detected: PlatformId
): ResolvedRelease[] {
  const current = createFallbackRelease(detected);

  const makeRelease = (
    tag: string,
    ver: string,
    title: string,
    channel: 'STABLE' | 'BETA' | 'PREVIEW',
    publishedAt: string,
    notes: string,
    winAssetVer: string = ver
  ): ResolvedRelease => {
    const releaseUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/tag/${tag}`;
    const downloadBase = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${tag}`;
    return {
      tagName: tag,
      releaseTitle: title,
      channel,
      publishedAt,
      htmlUrl: releaseUrl,
      releaseNotes: notes,
      isFallback: true,
      checksumsUrl: `${downloadBase}/SHA256SUMS.txt`,
      platforms: {
        windows: {
          platformId: 'windows',
          platformName: 'Windows',
          arch: 'x64 (Windows 10 / 11)',
          available: true,
          version: `AutoFailover ${ver}`,
          channel,
          assetName: `AutoFailover-${winAssetVer}-Windows-x64.zip`,
          downloadUrl: `${downloadBase}/AutoFailover-${winAssetVer}-Windows-x64.zip`,
          validationStatus: channel === 'BETA' ? 'Beta Release Ready' : 'Release Ready',
          isRecommended: detected === 'windows',
          description: 'Native Windows package with PowerShell NetTCPIP HAL.',
        },
        linux: {
          platformId: 'linux',
          platformName: 'Linux',
          arch: 'x86_64 / glibc 2.31+',
          available: true,
          version: `AutoFailover ${ver}`,
          channel,
          assetName: `AutoFailover-${winAssetVer}-Linux-x86_64.tar.gz`,
          downloadUrl: `${downloadBase}/AutoFailover-${winAssetVer}-Linux-x86_64.tar.gz`,
          validationStatus: 'Real-Host Validated',
          isRecommended: detected === 'linux',
          description: 'Native Linux archive with Netlink & sysfs prober.',
        },
        'macos-arm64': {
          platformId: 'macos-arm64',
          platformName: 'macOS Apple Silicon',
          arch: 'arm64 (M1/M2/M3/M4)',
          available: true,
          version: `AutoFailover ${ver}`,
          channel,
          assetName: `AutoFailover-${winAssetVer}-macOS-arm64.dmg`,
          downloadUrl: `${downloadBase}/AutoFailover-${winAssetVer}-macOS-arm64.dmg`,
          validationStatus: 'Release Ready',
          isRecommended: detected === 'macos-arm64',
          description: 'Native Apple Silicon DMG package.',
        },
        'macos-x64': {
          platformId: 'macos-x64',
          platformName: 'macOS Intel',
          arch: 'x64 (Intel)',
          available: true,
          version: `AutoFailover ${ver}`,
          channel,
          assetName: `AutoFailover-${winAssetVer}-macOS-x64.dmg`,
          downloadUrl: `${downloadBase}/AutoFailover-${winAssetVer}-macOS-x64.dmg`,
          validationStatus: 'Release Ready',
          isRecommended: detected === 'macos-x64',
          description: 'Native Intel macOS disk image.',
        },
      },
    };
  };

  const rel301 = makeRelease(
    'v3.0.1',
    '3.0.1',
    'AutoFailover 3.0.1 Release (v3.0.1)',
    'STABLE',
    '2026-09-14T01:00:00Z',
    '5-Case deterministic interface priority hierarchy and active workload continuity protection for Zoom, vMix, and OBS.'
  );

  const rel300p26 = makeRelease(
    'v3.0.0-preview.26',
    '3.0.0 Beta (preview.26)',
    'AutoFailover 3.0 Beta (v3.0.0-preview.26)',
    'BETA',
    '2026-09-13T19:00:00Z',
    'Official multi-platform Beta Release with Full HD desktop cockpit showcase, 4-provider speedtest benchmark, and native windowed executable.',
    '3.0.0'
  );

  const rel300p25 = makeRelease(
    'v3.0.0-preview.25',
    '3.0.0 Preview 25',
    'AutoFailover 3.0 Preview 25 (v3.0.0-preview.25)',
    'PREVIEW',
    '2026-09-13T18:00:00Z',
    'Kernel BSOD teardown prevention with SO_LINGER(1, 0) and decoupled process iteration caching.',
    '3.0.0'
  );

  const rel300p24 = makeRelease(
    'v3.0.0-preview.24',
    '3.0.0 Preview 24',
    'AutoFailover 3.0 Preview 24 (v3.0.0-preview.24)',
    'PREVIEW',
    '2026-09-13T17:00:00Z',
    'Card-based Interface Deck modernization and RFC 3550 statistical jitter measurement.',
    '3.0.0'
  );

  return [current, rel301, rel300p26, rel300p25, rel300p24];
}

export async function fetchLiveReleasesHistory(
  detected: PlatformId
): Promise<ResolvedRelease[]> {
  const fallbacks = createFallbackReleasesHistory(detected);
  try {
    const url = `${API_URL}?per_page=30&_nocache=${Date.now()}`;
    const res = await fetch(url, {
      headers: {
        Accept: 'application/vnd.github.v3+json',
      },
    });

    if (res.ok) {
      const releases: GitHubRelease[] = await res.json();
      const resolvedList = resolveAllReleasesFromList(releases, detected);
      
      // Merge live list with required historical fallbacks so the specified 5 versions are always present
      const map = new Map<string, ResolvedRelease>();
      resolvedList.forEach((r) => map.set(r.tagName, r));
      fallbacks.forEach((f) => {
        if (!map.has(f.tagName)) {
          map.set(f.tagName, f);
        }
      });

      const combined = Array.from(map.values());
      combined.sort((a, b) => {
        const pa = parseReleaseTag(a.tagName);
        const pb = parseReleaseTag(b.tagName);
        if (pa && pb) return compareReleaseVersions(pb, pa);
        return 0;
      });

      return combined;
    }
  } catch (err) {
    console.warn('Failed to fetch live GitHub releases history:', err);
  }
  return fallbacks;
}

