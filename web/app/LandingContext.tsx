'use client';

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

type LandingContextValue = {
  league: string | null;
  setLeague: (next: string | null) => void;
};

const LandingContext = createContext<LandingContextValue | null>(null);

export function LandingProvider({ children }: { children: ReactNode }) {
  const [league, setLeague] = useState<string | null>(null);

  const value = useMemo<LandingContextValue>(
    () => ({ league, setLeague }),
    [league],
  );

  return (
    <LandingContext.Provider value={value}>{children}</LandingContext.Provider>
  );
}

export function useLanding(): LandingContextValue {
  const ctx = useContext(LandingContext);
  if (!ctx) {
    return {
      league: null,
      setLeague: () => {},
    };
  }
  return ctx;
}
