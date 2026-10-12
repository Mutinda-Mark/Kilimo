import type { Metadata } from "next"

import { Suspense } from "react"

import "./globals.css"

import { AppSidebar } from "@/components/app-sidebar"

import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"


export const metadata: Metadata = {
  title: "KILIMO Admin",
  description:
    "Administration dashboard for the KILIMO tomato advisory system",
}


function SidebarLoading() {
  return (
    <div className="hidden h-screen w-64 border-r bg-sidebar md:block" />
  )
}


function DashboardLoading() {
  return (
    <main className="flex-1 p-6 lg:p-10">

      <div className="mb-8 space-y-3">

        <div className="h-8 w-56 animate-pulse rounded-md bg-muted" />

        <div className="h-4 w-96 max-w-full animate-pulse rounded-md bg-muted" />

      </div>


      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        {Array.from({
          length: 4,
        }).map(
          (_, index) => (

            <div
              key={index}
              className="rounded-xl border bg-card p-6"
            >

              <div className="mb-4 h-4 w-28 animate-pulse rounded bg-muted" />

              <div className="h-8 w-20 animate-pulse rounded bg-muted" />

              <div className="mt-3 h-3 w-36 animate-pulse rounded bg-muted" />

            </div>

          )
        )}

      </div>


      <div className="mt-8 grid gap-6 lg:grid-cols-2">

        <div className="h-[320px] animate-pulse rounded-xl border bg-card" />

        <div className="h-[320px] animate-pulse rounded-xl border bg-card" />

      </div>

    </main>
  )
}


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">

      <body>

        <SidebarProvider>

          {/* 
            AppSidebar uses usePathname(), which is runtime URL data.
            Next.js 16 requires it to be inside Suspense.
          */}

          <Suspense
            fallback={
              <SidebarLoading />
            }
          >

            <AppSidebar />

          </Suspense>


          <SidebarInset>

            <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">

              <SidebarTrigger />

              <div className="h-4 w-px bg-border" />

              <span className="text-sm font-medium">
                KILIMO Administration
              </span>

            </header>


            {/* 
              Dashboard pages fetch live FastAPI data using
              cache: "no-store", so the page content is also
              streamed through Suspense.
            */}

            <Suspense
              fallback={
                <DashboardLoading />
              }
            >

              {children}

            </Suspense>

          </SidebarInset>

        </SidebarProvider>

      </body>

    </html>
  )
}