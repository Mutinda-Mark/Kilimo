"use client"

import {
  Moon,
  Sun,
} from "lucide-react"

import {
  useTheme,
} from "next-themes"


export function ThemeToggle() {
  const {
    resolvedTheme,
    setTheme,
  } = useTheme()

  const dark =
    resolvedTheme === "dark"

  return (
    <button
      type="button"
      aria-label={
        dark
          ? "Switch to light mode"
          : "Switch to dark mode"
      }
      title={
        dark
          ? "Light mode"
          : "Dark mode"
      }
      onClick={() =>
        setTheme(
          dark
            ? "light"
            : "dark"
        )
      }
      className="flex size-9 items-center justify-center rounded-lg border bg-background text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      {dark ? (
        <Sun className="size-4" />
      ) : (
        <Moon className="size-4" />
      )}
    </button>
  )
}