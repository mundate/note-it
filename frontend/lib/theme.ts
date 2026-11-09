/**
 * Light/dark theme. The choice is stored in localStorage; "system" follows the OS setting.
 * The `.dark` class on <html> switches the CSS variables in styles/globals.css.
 *
 * index.html has a tiny inline copy of `resolve`/`apply` that runs before the app loads,
 * so the page never flashes the wrong theme. Keep STORAGE_KEY in sync with it.
 */
import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark" | "system";
export const THEMES: Theme[] = ["light", "dark", "system"];

const STORAGE_KEY = "theme";
const darkQuery = () => window.matchMedia("(prefers-color-scheme: dark)");

function readTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") return stored;
  } catch {}
  return "system";
}

function apply(theme: Theme): void {
  const dark = theme === "dark" || (theme === "system" && darkQuery().matches);
  document.documentElement.classList.toggle("dark", dark);
}

export function useTheme(): { theme: Theme; setTheme: (theme: Theme) => void } {
  const [theme, setThemeState] = useState<Theme>(readTheme);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {}
  }, []);

  useEffect(() => {
    apply(theme);
    if (theme !== "system") return;
    // Follow OS changes live while on "system".
    const query = darkQuery();
    const onChange = () => apply("system");
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, [theme]);

  // Keep other open tabs in sync.
  useEffect(() => {
    const onStorage = (e: StorageEvent) => e.key === STORAGE_KEY && setThemeState(readTheme());
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  return { theme, setTheme };
}
