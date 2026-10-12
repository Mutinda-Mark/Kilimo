"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Activity,
  ClipboardList,
  LayoutDashboard,
  Leaf,
  Settings,
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


const navigationItems = [
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
  {
    title: "System",
    href: "/system",
    icon: Settings,
  },
]


export function AppSidebar() {
  const pathname = usePathname()

  return (
    <Sidebar
      collapsible="icon"
      variant="inset"
    >
      <SidebarHeader>

        <div className="flex items-center gap-3 px-2 py-3">

          <div className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">

            <Leaf className="size-5" />

          </div>

          <div className="grid flex-1 text-left text-sm leading-tight">

            <span className="truncate font-semibold">
              KILIMO
            </span>

            <span className="truncate text-xs text-muted-foreground">
              Admin Dashboard
            </span>

          </div>

        </div>

      </SidebarHeader>


      <SidebarContent>

        <SidebarGroup>

          <SidebarGroupLabel>
            Platform
          </SidebarGroupLabel>

          <SidebarGroupContent>

            <SidebarMenu>

              {navigationItems.map(
                (item) => {

                  const active =
                    item.href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(
                          item.href
                        )

                  return (
                    <SidebarMenuItem
                      key={item.href}
                    >

                      <SidebarMenuButton
                        render={
                          <Link
                            href={item.href}
                          />
                        }
                        isActive={active}
                        tooltip={item.title}
                      >

                        <item.icon />

                        <span>
                          {item.title}
                        </span>

                      </SidebarMenuButton>

                    </SidebarMenuItem>
                  )
                }
              )}

            </SidebarMenu>

          </SidebarGroupContent>

        </SidebarGroup>

      </SidebarContent>


      <SidebarFooter>

        <div className="px-2 py-2 text-xs text-muted-foreground">
          KILIMO v0.5
        </div>

      </SidebarFooter>

      <SidebarRail />

    </Sidebar>
  )
}