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
const CACHE_KEY = 'autofailover_release_cache_v2';
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes

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

  // Match: v3.0.0, 3.0.0, v3.0.0-preview.19, 3.0.0-preview.9
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

  // Numeric preview comparison (e.g. preview.19 > preview.9, preview.100 > preview.19)
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

export function shouldInvalidateCache(): boolean {
  if (typeof window === 'undefined') return false;
  try {
    const params = new URLSearchParams(window.location.search);
    return (
      params.has('refresh') ||
      params.has('clear_cache') ||
      params.has('nocache')
    );
  } catch {
    return false;
  }
}

export async function getLatestAutoFailoverRelease(): Promise<ResolvedRelease> {
  const detected = detectUserPlatform();

  // Clean obsolete cache keys
  try {
    localStorage.removeItem('autofailover_release_cache');
  } catch {
    // ignore
  }

  // 1. Try Cache if not explicitly bypassed
  if (!shouldInvalidateCache()) {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Date.now() - parsed.timestamp < CACHE_TTL_MS && parsed.data) {
          return parsed.data;
        }
      }
    } catch {
      // ignore cache read errors
    }
  }

  // 2. Fetch from GitHub API
  try {
    const res = await fetch(API_URL, {
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
    console.warn('Failed to fetch GitHub releases, using fallback:', err);
  }

  // 3. Fallback when API fails or rate limited
  return createFallbackRelease(detected);
}

export function resolveReleaseFromList(
  releases: GitHubRelease[],
  detected: PlatformId
): ResolvedRelease | null {
  // Parse and validate version for each release
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

  if (parsedList.length === 0) return null;

  // Sort descending: highest version first using numeric comparison
  parsedList.sort((a, b) => compareReleaseVersions(b.parsed, a.parsed));

  const selected = parsedList[0].release;
  const channel: 'STABLE' | 'PREVIEW' = selected.prerelease
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

  const platforms: Record<PlatformId, PlatformReleaseInfo> = {
    windows: {
      platformId: 'windows',
      platformName: 'Windows',
      arch: 'x64 (Windows 10 / 11)',
      available: Boolean(winAsset),
      version: `AutoFailover 3.0 (${ver})`,
      channel,
      assetName: winAsset?.name || 'AutoFailover-3.0.0-Windows-x64.zip',
      downloadUrl: winAsset?.browser_download_url,
      sizeFormatted: winAsset ? formatBytes(winAsset.size) : undefined,
      validationStatus: 'Available for Testing',
      isRecommended: detected === 'windows',
      description:
        'Native PowerShell NetTCPIP HAL. Downloadable for physical PC verification.',
    },
    linux: {
      platformId: 'linux',
      platformName: 'Linux',
      arch: 'x86_64 / glibc 2.31+',
      available: Boolean(linuxAsset),
      version: `AutoFailover 3.0 (${ver})`,
      channel,
      assetName: linuxAsset?.name || 'AutoFailover-3.0.0-Linux-x86_64.tar.gz',
      downloadUrl: linuxAsset?.browser_download_url,
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
      version: `AutoFailover 3.0 (${ver})`,
      channel,
      assetName: macArmAsset?.name || 'AutoFailover-3.0.0-macOS-arm64.dmg',
      downloadUrl: macArmAsset?.browser_download_url,
      sizeFormatted: macArmAsset ? formatBytes(macArmAsset.size) : undefined,
      validationStatus: 'Available for Testing',
      isRecommended: detected === 'macos-arm64',
      description:
        'Native BSD route & networksetup HAL. Unsigned preview build.',
    },
    'macos-x64': {
      platformId: 'macos-x64',
      platformName: 'macOS Intel',
      arch: 'x64 (Intel Mac)',
      available: Boolean(macX64Asset),
      version: `AutoFailover 3.0 (${ver})`,
      channel,
      assetName: macX64Asset?.name || 'AutoFailover-3.0.0-macOS-x64.dmg',
      downloadUrl: macX64Asset?.browser_download_url,
      sizeFormatted: macX64Asset ? formatBytes(macX64Asset.size) : undefined,
      validationStatus: 'Available for Testing',
      isRecommended: false,
      description: 'Native Intel macOS build. Unsigned preview build.',
    },
  };

  return {
    tagName: selected.tag_name,
    releaseTitle: selected.name || `AutoFailover ${selected.tag_name}`,
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

function createFallbackRelease(detected: PlatformId): ResolvedRelease {
  return {
    tagName: 'v3.0.0-preview.18',
    releaseTitle: 'AutoFailover 3.0 Preview 18',
    channel: 'PREVIEW',
    publishedAt: new Date().toISOString(),
    htmlUrl: FALLBACK_RELEASES_URL,
    releaseNotes:
      'Real-time release discovery via GitHub API is currently loading or rate-limited.',
    isFallback: true,
    platforms: {
      windows: {
        platformId: 'windows',
        platformName: 'Windows',
        arch: 'x64 (Windows 10 / 11)',
        available: true,
        version: 'AutoFailover 3.0 (preview.18)',
        channel: 'PREVIEW',
        assetName: 'AutoFailover-3.0.0-Windows-x64.zip',
        downloadUrl: FALLBACK_RELEASES_URL,
        validationStatus: 'Available for Testing',
        isRecommended: detected === 'windows',
        description: 'Native Windows executable package.',
      },
      linux: {
        platformId: 'linux',
        platformName: 'Linux',
        arch: 'x86_64 / glibc 2.31+',
        available: true,
        version: 'AutoFailover 3.0 (preview.18)',
        channel: 'PREVIEW',
        assetName: 'AutoFailover-3.0.0-Linux-x86_64.tar.gz',
        downloadUrl: FALLBACK_RELEASES_URL,
        validationStatus: 'Real-Host Validated',
        isRecommended: detected === 'linux',
        description: 'Native Linux standalone archive.',
      },
      'macos-arm64': {
        platformId: 'macos-arm64',
        platformName: 'macOS Apple Silicon',
        arch: 'arm64 (M1/M2/M3/M4)',
        available: false,
        version: 'AutoFailover 3.0 (preview.18)',
        channel: 'PREVIEW',
        assetName: 'AutoFailover-3.0.0-macOS-arm64.dmg',
        downloadUrl: FALLBACK_RELEASES_URL,
        validationStatus: 'Available for Testing',
        isRecommended: detected === 'macos-arm64',
        description: 'Native Apple Silicon DMG package.',
      },
      'macos-x64': {
        platformId: 'macos-x64',
        platformName: 'macOS Intel',
        arch: 'x64 (Intel Mac)',
        available: false,
        version: 'AutoFailover 3.0 (preview.18)',
        channel: 'PREVIEW',
        assetName: 'AutoFailover-3.0.0-macOS-x64.dmg',
        downloadUrl: FALLBACK_RELEASES_URL,
        validationStatus: 'Available for Testing',
        isRecommended: false,
        description: 'Native Intel Mac DMG package.',
      },
    },
  };
}
