"use client"

import {
  LogOut,
} from "lucide-react"

import {
  useState,
} from "react"

import {
  useRouter,
} from "next/navigation"

import {
  createClient,
} from "@/lib/supabase/client"

import {
  Button,
} from "@/components/ui/button"


export function SignOutButton() {
  const router =
    useRouter()

  const [
    loading,
    setLoading,
  ] =
    useState(false)


  async function signOut() {
    setLoading(true)

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
    <Button
      type="button"
      variant="ghost"
      size="sm"
      disabled={loading}
      onClick={signOut}
    >
      <LogOut className="size-4" />

      {loading
        ? "Signing out…"
        : "Sign out"}
    </Button>
  )
}