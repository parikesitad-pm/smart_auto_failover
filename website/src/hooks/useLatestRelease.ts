import { useState, useEffect, useCallback } from 'react';
import {
  getLatestAutoFailoverRelease,
  fetchLiveReleases,
  fetchLiveReleasesHistory,
  createFallbackReleasesHistory,
  detectUserPlatform,
} from '../services/githubReleases';
import { ResolvedRelease } from '../types/releases';

export function useLatestRelease() {
  const [release, setRelease] = useState<ResolvedRelease | null>(null);
  const [releasesHistory, setReleasesHistory] = useState<ResolvedRelease[]>([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    const detected = detectUserPlatform();
    const [freshRelease, freshHistory] = await Promise.all([
      fetchLiveReleases(detected),
      fetchLiveReleasesHistory(detected),
    ]);
    if (freshRelease) {
      setRelease(freshRelease);
    }
    if (freshHistory && freshHistory.length > 0) {
      setReleasesHistory(freshHistory);
    }
    setIsRefreshing(false);
  }, []);

  useEffect(() => {
    let isMounted = true;
    const detected = detectUserPlatform();
    setReleasesHistory(createFallbackReleasesHistory(detected));

    // Call SWR resolver with update callback
    getLatestAutoFailoverRelease((fresh) => {
      if (isMounted) {
        setRelease(fresh);
      }
    })
      .then((data) => {
        if (isMounted) {
          setRelease(data);
          setLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    // Also fetch full releases history in background
    fetchLiveReleasesHistory(detected)
      .then((history) => {
        if (isMounted && history && history.length > 0) {
          setReleasesHistory(history);
        }
      })
      .catch(() => {
        // ignore background fetch error, fallbacks already set
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return { release, releasesHistory, loading, isRefreshing, refresh };
}

