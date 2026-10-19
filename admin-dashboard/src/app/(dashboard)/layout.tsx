import {
  Suspense,
} from "react"

import {
  AppSidebar,
} from "@/components/app-sidebar"

import {
  DashboardHeader,
} from "@/components/dashboard-header"

import {
  requireAdminUser,
} from "@/lib/auth"

import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar"


export const instant = false


function SidebarLoading() {
  return (
    <div className="hidden h-screen w-64 border-r bg-sidebar md:block" />
  )
}


function DashboardLoading() {
  return (
    <main className="flex-1 px-6 py-8 lg:px-8 xl:px-10">
      <div className="space-y-4">
        <div className="h-7 w-48 animate-pulse rounded-lg bg-muted" />
        <div className="h-4 w-80 animate-pulse rounded-lg bg-muted" />
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({
          length: 4,
        }).map((_, index) => (
          <div
            key={index}
            className="h-28 animate-pulse rounded-xl border bg-card"
          />
        ))}
      </div>
    </main>
  )
}


export default async function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const {user, admin} =
    await requireAdminUser()

  return (
    <SidebarProvider>
      <Suspense fallback={<SidebarLoading />}>
        <AppSidebar />
      </Suspense>

      <SidebarInset className="min-w-0 bg-background">
        <DashboardHeader user={user} admin={admin} />

        <Suspense fallback={<DashboardLoading />}>
          {children}
        </Suspense>
      </SidebarInset>
    </SidebarProvider>
  )
}