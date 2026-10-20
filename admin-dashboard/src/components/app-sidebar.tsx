"use client"

import Link from "next/link"
import {
  usePathname,
} from "next/navigation"

import {
  Activity,
  ClipboardList,
  LayoutDashboard,
  Leaf,
  ServerCog,
  Settings,
  ShieldCheck,
  UserRound,
  Users,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"


const workspaceItems = [
  {
    title: "Overview",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Farmers",
    href: "/farmers",
    icon: Users,
  },
  {
    title: "Assessments",
    href: "/assessments",
    icon: ClipboardList,
  },
  {
    title: "Analytics",
    href: "/analytics",
    icon: Activity,
  },
]


const operationsItems = [
  {
    title: "System",
    href: "/system",
    icon: ServerCog,
  },
]


const accountItems = [
  {
    title: "Profile",
    href: "/profile",
    icon: UserRound,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
]


export function AppSidebar() {
  const pathname =
    usePathname()


  function isActive(
    href: string,
  ) {
    return href === "/"
      ? pathname === "/"
      : pathname.startsWith(
          href
        )
  }


  return (
    <Sidebar
      collapsible="icon"
      variant="sidebar"
      className="border-r"
    >

      {/* =================================================
          BRAND
      ================================================= */}

      <SidebarHeader className="px-3 py-4">

        <div className="flex items-center gap-3 px-1">

          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border bg-background">
            <Leaf className="size-4.5" />
          </div>

          <div className="min-w-0 group-data-[collapsible=icon]:hidden">

            <p className="truncate text-sm font-semibold tracking-tight">
              KILIMO
            </p>

            <p className="truncate text-xs text-muted-foreground">
              Intelligence Console
            </p>

          </div>

        </div>

      </SidebarHeader>


      <SidebarContent>

        {/* =================================================
            WORKSPACE
        ================================================= */}

        <SidebarGroup>

          <SidebarGroupLabel>
            Workspace
          </SidebarGroupLabel>

          <SidebarGroupContent>

            <SidebarMenu>

              {workspaceItems.map(
                (
                  item
                ) => (
                  <SidebarMenuItem
                    key={
                      item.href
                    }
                  >

                    <SidebarMenuButton
                      render={
                        <Link
                          href={
                            item.href
                          }
                        />
                      }
                      isActive={
                        isActive(
                          item.href
                        )
                      }
                      tooltip={
                        item.title
                      }
                      className="h-9"
                    >

                      <item.icon />

                      <span>
                        {item.title}
                      </span>

                    </SidebarMenuButton>

                  </SidebarMenuItem>
                )
              )}

            </SidebarMenu>

          </SidebarGroupContent>

        </SidebarGroup>


        {/* =================================================
            OPERATIONS
        ================================================= */}

        <SidebarGroup>

          <SidebarGroupLabel>
            Operations
          </SidebarGroupLabel>

          <SidebarGroupContent>

            <SidebarMenu>

              {operationsItems.map(
                (
                  item
                ) => (
                  <SidebarMenuItem
                    key={
                      item.href
                    }
                  >

                    <SidebarMenuButton
                      render={
                        <Link
                          href={
                            item.href
                          }
                        />
                      }
                      isActive={
                        isActive(
                          item.href
                        )
                      }
                      tooltip={
                        item.title
                      }
                      className="h-9"
                    >

                      <item.icon />

                      <span>
                        {item.title}
                      </span>

                    </SidebarMenuButton>

                  </SidebarMenuItem>
                )
              )}

            </SidebarMenu>

          </SidebarGroupContent>

        </SidebarGroup>


        {/* =================================================
            ACCOUNT
        ================================================= */}

        <SidebarGroup>

          <SidebarGroupLabel>
            Account
          </SidebarGroupLabel>

          <SidebarGroupContent>

            <SidebarMenu>

              {accountItems.map(
                (
                  item
                ) => (
                  <SidebarMenuItem
                    key={
                      item.href
                    }
                  >

                    <SidebarMenuButton
                      render={
                        <Link
                          href={
                            item.href
                          }
                        />
                      }
                      isActive={
                        isActive(
                          item.href
                        )
                      }
                      tooltip={
                        item.title
                      }
                      className="h-9"
                    >

                      <item.icon />

                      <span>
                        {item.title}
                      </span>

                    </SidebarMenuButton>

                  </SidebarMenuItem>
                )
              )}

            </SidebarMenu>

          </SidebarGroupContent>

        </SidebarGroup>

      </SidebarContent>


      {/* =================================================
          FOOTER
      ================================================= */}

      <SidebarFooter className="px-3 pb-3">

        <div className="rounded-lg border bg-background/80 p-3 group-data-[collapsible=icon]:hidden">

          <div className="flex items-center gap-2">

            <span className="relative flex size-2">

              <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-400 opacity-50" />

              <span className="relative inline-flex size-2 rounded-full bg-emerald-500" />

            </span>

            <span className="text-xs font-medium">
              System operational
            </span>

          </div>


          <div className="mt-2 flex items-center gap-2 text-[11px] text-muted-foreground">

            <ShieldCheck className="size-3" />

            Protected administration

          </div>

        </div>


        <div className="mt-2 px-1 text-[11px] text-muted-foreground group-data-[collapsible=icon]:hidden">
          KILIMO v0.5
        </div>

      </SidebarFooter>


      <SidebarRail />

    </Sidebar>
  )
}