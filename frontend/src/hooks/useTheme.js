// Purpose: Theme (light/dark mode) state manager with localStorage persistence and multi-instance sync.
// Security: Reads and writes only to localStorage key "resitsaya-theme"; never executes injected content.

import { useEffect, useState } from "react";

const STORAGE_KEY = "resitsaya-theme";
const THEME_EVENT = "resitsaya-theme-change";
export const THEME_DARK = "dark";
export const THEME_LIGHT = "light";

function getInitialTheme() {
  try {
    return localStorage.getItem(STORAGE_KEY) || THEME_LIGHT;
  } catch {
    return THEME_LIGHT;
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(getInitialTheme);

  useEffect(() => {
    // Sync DOM attribute on mount or change
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // localStorage unavailable (e.g. strict private browsing mode)
    }
  }, [theme]);

  useEffect(() => {
    // Listen for changes from other components on the same page
    const handleThemeChange = (e) => {
      if (e.detail && e.detail !== theme) {
        setTheme(e.detail);
      }
    };

    // Listen for changes from other browser tabs
    const handleStorageChange = (e) => {
      if (e.key === STORAGE_KEY && e.newValue && e.newValue !== theme) {
        setTheme(e.newValue);
      }
    };

    window.addEventListener(THEME_EVENT, handleThemeChange);
    window.addEventListener("storage", handleStorageChange);

    return () => {
      window.removeEventListener(THEME_EVENT, handleThemeChange);
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [theme]);

  const toggleTheme = () => {
    const nextTheme = theme === THEME_DARK ? THEME_LIGHT : THEME_DARK;
    setTheme(nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
    try {
      localStorage.setItem(STORAGE_KEY, nextTheme);
    } catch {
      // Ignored
    }
    window.dispatchEvent(new CustomEvent(THEME_EVENT, { detail: nextTheme }));
  };

  const isDark = theme === THEME_DARK;

  return { theme, isDark, toggleTheme };
}
