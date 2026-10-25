"use client"

import Link from "next/link"

import {
  ChevronDown,
  LogOut,
  Settings,
  ShieldCheck,
  UserRound,
} from "lucide-react"

import {
  useEffect,
  useRef,
  useState,
} from "react"

import {
  useRouter,
} from "next/navigation"

import type {
  User,
} from "@supabase/supabase-js"

import type {
  AdminUser,
} from "@/lib/admin"

import {
  createClient,
} from "@/lib/supabase/client"


interface AdminProfileMenuProps {
  user: User
  admin: AdminUser
}


function initials(
  name: string,
) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map(
      (part) =>
        part[0]?.toUpperCase()
    )
    .join("")
}


function roleLabel(
  role: string,
) {
  switch (role) {
    case "super_admin":
      return "Super Admin"

    case "viewer":
      return "Viewer"

    default:
      return "Administrator"
  }
}


export function AdminProfileMenu({
  user,
  admin,
}: AdminProfileMenuProps) {
  const router =
    useRouter()

  const containerRef =
    useRef<HTMLDivElement>(
      null
    )

  const [
    open,
    setOpen,
  ] =
    useState(false)

  const [
    signingOut,
    setSigningOut,
  ] =
    useState(false)


  const displayName =
    admin.display_name ??
    user.user_metadata
      ?.full_name ??
    user.user_metadata
      ?.name ??
    "Administrator"


  useEffect(() => {
    function close(
      event: MouseEvent,
    ) {
      if (
        containerRef.current &&
        !containerRef.current.contains(
          event.target as Node
        )
      ) {
        setOpen(false)
      }
    }

    document.addEventListener(
      "mousedown",
      close
    )

    return () =>
      document.removeEventListener(
        "mousedown",
        close
      )
  }, [])


  async function signOut() {
    setSigningOut(true)

    const supabase =
      createClient()

    await supabase.auth
      .signOut()

    router.replace(
      "/sign-in"
    )

    router.refresh()
  }


  return (
    <div
      ref={containerRef}
      className="relative"
    >

      {/* =================================================
          TRIGGER
      ================================================= */}

      <button
        type="button"
        aria-expanded={
          open
        }
        aria-haspopup="menu"
        onClick={() =>
          setOpen(
            (
              value
            ) =>
              !value
          )
        }
        className="flex h-10 items-center gap-2 rounded-lg px-2 transition-colors hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >

        <div className="flex size-8 items-center justify-center rounded-full border bg-muted font-mono text-xs font-semibold">
          {initials(
            displayName
          )}
        </div>


        <div className="hidden max-w-36 text-left xl:block">

          <p className="truncate text-xs font-medium">
            {displayName}
          </p>

          <p className="truncate text-[10px] text-muted-foreground">
            {roleLabel(
              admin.role
            )}
          </p>

        </div>


        <ChevronDown className="hidden size-3.5 text-muted-foreground xl:block" />

      </button>


      {/* =================================================
          MENU
      ================================================= */}

      {open && (

        <div
          role="menu"
          className="absolute right-0 top-12 z-50 w-72 overflow-hidden rounded-xl border bg-popover shadow-lg"
        >

          {/* =============================================
              IDENTITY
          ============================================= */}

          <div className="border-b p-4">

            <div className="flex items-center gap-3">

              <div className="flex size-10 items-center justify-center rounded-full border bg-muted font-mono text-xs font-semibold">
                {initials(
                  displayName
                )}
              </div>


              <div className="min-w-0">

                <p className="truncate text-sm font-medium">
                  {displayName}
                </p>

                <p className="truncate text-xs text-muted-foreground">
                  {admin.email}
                </p>

              </div>

            </div>


            <div className="mt-4 flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2">

              <ShieldCheck className="size-3.5 text-emerald-600 dark:text-emerald-400" />

              <div>

                <p className="text-xs font-medium">
                  MFA protected
                </p>

                <p className="text-[10px] text-muted-foreground">
                  Authenticator verified
                </p>

              </div>

            </div>

          </div>


          {/* =============================================
              NAVIGATION
          ============================================= */}

          <div className="p-2">

            <Link
              href="/profile"
              role="menuitem"
              onClick={() =>
                setOpen(
                  false
                )
              }
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-accent"
            >

              <UserRound className="size-4 text-muted-foreground" />

              <div>

                <p className="text-xs font-medium">
                  Profile
                </p>

                <p className="text-[10px] text-muted-foreground">
                  Identity and account security
                </p>

              </div>

            </Link>


            <Link
              href="/settings"
              role="menuitem"
              onClick={() =>
                setOpen(
                  false
                )
              }
              className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-accent"
            >

              <Settings className="size-4 text-muted-foreground" />

              <div>

                <p className="text-xs font-medium">
                  Settings
                </p>

                <p className="text-[10px] text-muted-foreground">
                  Appearance and session
                </p>

              </div>

            </Link>


            <div className="my-2 border-t" />


            <div className="flex items-center gap-3 rounded-lg px-3 py-2">

              <ShieldCheck className="size-4 text-muted-foreground" />

              <div>

                <p className="text-xs font-medium">
                  Role
                </p>

                <p className="text-[10px] text-muted-foreground">
                  {roleLabel(
                    admin.role
                  )}
                </p>

              </div>

            </div>


            <button
              type="button"
              role="menuitem"
              disabled={
                signingOut
              }
              onClick={
                signOut
              }
              className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-accent disabled:opacity-50"
            >

              <LogOut className="size-4 text-muted-foreground" />

              <div>

                <p className="text-xs font-medium">
                  {signingOut
                    ? "Signing out..."
                    : "Sign out"}
                </p>

                <p className="text-[10px] text-muted-foreground">
                  End this administrator session
                </p>

              </div>

            </button>

          </div>

        </div>

      )}

    </div>
  )
}