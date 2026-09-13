import { useState, useEffect, useCallback } from 'react';
import {
  getLatestAutoFailoverRelease,
  fetchLiveReleases,
  detectUserPlatform,
} from '../services/githubReleases';
import { ResolvedRelease } from '../types/releases';

export function useLatestRelease() {
  const [release, setRelease] = useState<ResolvedRelease | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    const detected = detectUserPlatform();
    const fresh = await fetchLiveReleases(detected);
    if (fresh) {
      setRelease(fresh);
    }
    setIsRefreshing(false);
  }, []);

  useEffect(() => {
    let isMounted = true;

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

    return () => {
      isMounted = false;
    };
  }, []);

  return { release, loading, isRefreshing, refresh };
}
