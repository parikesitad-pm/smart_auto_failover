export type PlatformId = 'windows' | 'linux' | 'macos-arm64' | 'macos-x64';

export interface GitHubAsset {
  name: string;
  browser_download_url: string;
  size: number;
}

export interface GitHubRelease {
  tag_name: string;
  name: string;
  prerelease: boolean;
  published_at: string;
  html_url: string;
  body: string;
  target_commitish?: string;
  assets: GitHubAsset[];
}

export interface PlatformReleaseInfo {
  platformId: PlatformId;
  platformName: string;
  arch: string;
  available: boolean;
  version: string;
  channel: 'STABLE' | 'PREVIEW';
  assetName?: string;
  downloadUrl?: string;
  sizeFormatted?: string;
  validationStatus: string;
  isRecommended: boolean;
  description: string;
}

export interface ResolvedRelease {
  tagName: string;
  releaseTitle: string;
  channel: 'STABLE' | 'PREVIEW';
  publishedAt: string;
  htmlUrl: string;
  commitSha?: string;
  releaseNotes: string;
  checksumsUrl?: string;
  platforms: Record<PlatformId, PlatformReleaseInfo>;
  isFallback: boolean;
}
