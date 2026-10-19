import type {
  User,
} from "@supabase/supabase-js"

import type {
  AdminUser,
} from "@/lib/admin"

import {
  SidebarTrigger,
} from "@/components/ui/sidebar"

import {
  GlobalSearch,
} from "@/components/global-search"

import {
  ThemeToggle,
} from "@/components/theme-toggle"

import {
  NotificationCenter,
} from "@/components/notification-center"

import {
  DashboardRefresh,
} from "@/components/dashboard-refresh"

import {
  AdminProfileMenu,
} from "@/components/admin-profile-menu"


interface DashboardHeaderProps {
  user: User
  admin: AdminUser
}


export function DashboardHeader({
  user,
  admin,
}: DashboardHeaderProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center border-b bg-background/90 px-5 backdrop-blur supports-[backdrop-filter]:bg-background/75">

      {/* Left side */}

      <div className="flex min-w-0 flex-1 items-center gap-3">

        <SidebarTrigger className="-ml-1" />

        <div className="hidden h-4 w-px bg-border sm:block" />

        <div className="hidden min-w-0 md:block">

          <p className="truncate text-sm font-medium">
            Administration Console
          </p>

          <p className="truncate text-xs text-muted-foreground">
            KILIMO operational workspace
          </p>

        </div>

      </div>


      {/* Right side */}

      <div className="flex items-center gap-2">

        <GlobalSearch />

        <div className="hidden h-5 w-px bg-border lg:block" />

        <DashboardRefresh />

        <ThemeToggle />

        <NotificationCenter />

        <div className="hidden h-5 w-px bg-border md:block" />

        <AdminProfileMenu
          user={user}
          admin={admin}
        />

      </div>

    </header>
  )
}