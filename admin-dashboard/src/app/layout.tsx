import type {
  Metadata,
} from "next"

import "./globals.css"

import {
  ThemeProvider,
} from "@/components/theme-provider"


export const metadata: Metadata = {
  title: {
    default:
      "KILIMO Administration",
    template:
      "%s | KILIMO",
  },

  description:
    "Secure administration and intelligence console for the KILIMO tomato disease detection and farmer advisory platform.",
}


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
    >
      <body>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}