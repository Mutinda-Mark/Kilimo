"use client"

import {
  FormEvent,
  useEffect,
  useState,
} from "react"

import {
  LoaderCircle,
  ShieldCheck,
} from "lucide-react"

import {
  useRouter,
} from "next/navigation"

import {
  createClient,
} from "@/lib/supabase/client"

import {
  Button,
} from "@/components/ui/button"

import {
  Input,
} from "@/components/ui/input"


export function MfaChallenge() {
  const router =
    useRouter()

  const [
    factorId,
    setFactorId,
  ] =
    useState<string | null>(
      null
    )

  const [
    code,
    setCode,
  ] =
    useState("")

  const [
    loading,
    setLoading,
  ] =
    useState(true)

  const [
    verifying,
    setVerifying,
  ] =
    useState(false)

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null
    )


  useEffect(() => {
    let active = true

    async function loadFactor() {
      const supabase =
        createClient()

      const {
        data,
        error:
          factorsError,
      } =
        await supabase.auth.mfa
          .listFactors()

      if (!active) {
        return
      }

      if (factorsError) {
        setError(
          factorsError.message
        )
        setLoading(false)
        return
      }

      const factor =
        data.totp.find(
          (item) =>
            item.status ===
            "verified"
        )

      if (!factor) {
        router.replace(
          "/mfa-setup"
        )
        return
      }

      setFactorId(
        factor.id
      )

      setLoading(false)
    }

    void loadFactor()

    return () => {
      active = false
    }
  }, [router])


  async function verify(
    event: FormEvent
  ) {
    event.preventDefault()

    if (
      !factorId ||
      code.length !== 6
    ) {
      return
    }

    setVerifying(true)
    setError(null)

    const supabase =
      createClient()

    const {
      error:
        verifyError,
    } =
      await supabase.auth.mfa
        .challengeAndVerify({
          factorId,
          code,
        })

    if (verifyError) {
      setError(
        "The code was not accepted. Confirm the code in your authenticator and try again."
      )

      setVerifying(false)
      return
    }

    router.replace("/")
    router.refresh()
  }


  if (loading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <LoaderCircle className="size-5 animate-spin text-muted-foreground" />
      </div>
    )
  }


  return (
    <form
      onSubmit={verify}
      className="space-y-5"
    >
      <div>
        <label
          htmlFor="mfa-code"
          className="text-sm font-medium"
        >
          Authenticator code
        </label>

        <p className="mt-1 text-sm leading-6 text-muted-foreground">
          Open your authenticator application and
          enter the current six-digit code for KILIMO.
        </p>

        <Input
          id="mfa-code"
          autoFocus
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          placeholder="000000"
          value={code}
          onChange={
            (event) => {
              const value =
                event.target.value
                  .replace(
                    /\D/g,
                    ""
                  )
                  .slice(
                    0,
                    6
                  )

              setCode(value)
            }
          }
          className="mt-4 h-14 text-center font-mono text-xl tracking-[0.45em] tabular-nums"
        />
      </div>


      {error && (
        <p
          role="alert"
          className="text-sm text-destructive"
        >
          {error}
        </p>
      )}


      <Button
        type="submit"
        className="h-11 w-full"
        disabled={
          verifying ||
          code.length !== 6
        }
      >
        {verifying ? (
          <>
            <LoaderCircle className="size-4 animate-spin" />
            Verifying…
          </>
        ) : (
          <>
            <ShieldCheck className="size-4" />
            Verify and continue
          </>
        )}
      </Button>
    </form>
  )
}