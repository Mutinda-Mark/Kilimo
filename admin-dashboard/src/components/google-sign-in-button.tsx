"use client"

import {
  useState,
} from "react"

import {
  LoaderCircle,
} from "lucide-react"

import {
  createClient,
} from "@/lib/supabase/client"

import {
  Button,
} from "@/components/ui/button"


export function GoogleSignInButton() {
  const [
    loading,
    setLoading,
  ] = useState(false)

  async function signIn() {
    setLoading(true)

    const supabase =
      createClient()

    const redirectTo =
      `${window.location.origin}/auth/callback`

    const {
      error,
    } =
      await supabase.auth.signInWithOAuth({
        provider: "google",

        options: {
          redirectTo,
        },
      })

    if (error) {
      setLoading(false)

      console.error(
        "Google sign-in failed:",
        error.message
      )
    }
  }


  return (
    <Button
      type="button"
      variant="outline"
      className="h-11 w-full justify-center gap-3"
      disabled={loading}
      onClick={signIn}
    >
      {loading ? (
        <LoaderCircle className="size-4 animate-spin" />
      ) : (
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="size-4"
        >
          <path
            fill="currentColor"
            d="M21.35 11.1H12v2.98h5.38c-.23 1.53-1.8 4.49-5.38 4.49-3.24 0-5.88-2.68-5.88-5.99S8.76 6.59 12 6.59c1.85 0 3.08.8 3.79 1.49l2.58-2.53C16.71 3.98 14.56 3 12 3a9.58 9.58 0 0 0 0 19.16c5.53 0 9.19-3.94 9.19-9.49 0-.64-.07-1.12-.15-1.57Z"
          />
        </svg>
      )}

      {loading
        ? "Redirecting…"
        : "Continue with Google"}
    </Button>
  )
}