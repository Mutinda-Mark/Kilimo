"use client"

import {
  FormEvent,
  useEffect,
  useState,
} from "react"

import {
  CheckCircle2,
  Copy,
  KeyRound,
  LoaderCircle,
  ShieldCheck,
  Smartphone,
} from "lucide-react"

import { useRouter } from "next/navigation"

import { createClient } from "@/lib/supabase/client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"


interface EnrollmentState {
  factorId: string
  qrCode: string
  secret: string
}


export function MfaEnrollment() {
  const router = useRouter()

  const [
    enrollment,
    setEnrollment,
  ] =
    useState<EnrollmentState | null>(
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
    copied,
    setCopied,
  ] =
    useState(false)

  const [
    error,
    setError,
  ] =
    useState<string | null>(null)


  useEffect(() => {
    let active = true

    async function beginEnrollment() {
      const supabase =
        createClient()

      /*
       * Avoid creating unnecessary factors if
       * the component is mounted again.
       */
      const {
        data: factors,
        error: factorsError,
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

      const existingVerified =
        factors.totp.find(
          (factor) =>
            factor.status ===
            "verified"
        )

      if (existingVerified) {
        router.replace(
          "/mfa-challenge"
        )
        return
      }


      /*
       * Remove old unverified TOTP factors
       * created by abandoned setup attempts.
       */



      const {
        data,
        error: enrollError,
      } =
        await supabase.auth.mfa
          .enroll({
            factorType: "totp",
            friendlyName:
              "KILIMO Admin Authenticator",
          })

      if (!active) {
        return
      }

      if (enrollError) {
        setError(
          enrollError.message
        )
        setLoading(false)
        return
      }

      setEnrollment({
        factorId: data.id,
        qrCode:
          data.totp.qr_code,
        secret:
          data.totp.secret,
      })

      setLoading(false)
    }

    void beginEnrollment()

    return () => {
      active = false
    }
  }, [router])


  async function copySecret() {
    if (!enrollment) {
      return
    }

    await navigator.clipboard
      .writeText(
        enrollment.secret
      )

    setCopied(true)

    window.setTimeout(
      () => {
        setCopied(false)
      },
      1800
    )
  }


  async function verifyCode(
    event: FormEvent
  ) {
    event.preventDefault()

    if (
      !enrollment ||
      code.length !== 6
    ) {
      return
    }

    setVerifying(true)
    setError(null)

    const supabase =
      createClient()

    const {
      error: verifyError,
    } =
      await supabase.auth.mfa
        .challengeAndVerify({
          factorId:
            enrollment.factorId,
          code,
        })

    if (verifyError) {
      setError(
        "The verification code was not accepted. Check your authenticator and try again."
      )

      setVerifying(false)
      return
    }

    router.replace("/")
    router.refresh()
  }


  if (loading) {
    return (
      <div className="flex min-h-64 items-center justify-center">
        <LoaderCircle className="size-5 animate-spin text-muted-foreground" />
      </div>
    )
  }


  if (
    error &&
    !enrollment
  ) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-5">
        <p className="text-sm font-medium text-destructive">
          MFA setup could not be started
        </p>

        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          {error}
        </p>
      </div>
    )
  }


  if (!enrollment) {
    return null
  }


  return (
    <div className="space-y-8">

      <div className="rounded-xl border bg-card p-5">
        <div className="flex gap-4">
          <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
            <Smartphone className="size-5" />
          </div>

          <div>
            <p className="text-sm font-medium">
              Add KILIMO to your authenticator
            </p>

            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              Scan this QR code using Google Authenticator,
              Microsoft Authenticator, Authy, or another
              compatible TOTP application.
            </p>
          </div>
        </div>


        <div className="mt-6 flex justify-center rounded-xl border bg-white p-5">
          {/* Supabase returns an SVG/data representation suitable for img */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={
              enrollment.qrCode
            }
            alt="KILIMO authenticator QR code"
            className="size-52"
          />
        </div>
      </div>


      <div>
        <p className="text-sm font-medium">
          Unable to scan?
        </p>

        <p className="mt-1 text-sm text-muted-foreground">
          Enter this setup key manually in your authenticator.
        </p>

        <div className="mt-3 flex items-center gap-2">
          <code className="min-w-0 flex-1 overflow-x-auto rounded-lg border bg-muted/50 px-3 py-2.5 font-mono text-xs">
            {enrollment.secret}
          </code>

          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Copy authenticator secret"
            onClick={
              copySecret
            }
          >
            {copied ? (
              <CheckCircle2 className="size-4" />
            ) : (
              <Copy className="size-4" />
            )}
          </Button>
        </div>
      </div>


      <form
        onSubmit={
          verifyCode
        }
        className="space-y-4"
      >
        <div>
          <label
            htmlFor="totp-code"
            className="text-sm font-medium"
          >
            Verification code
          </label>

          <p className="mt-1 text-sm text-muted-foreground">
            Enter the six-digit code currently displayed
            by your authenticator.
          </p>

          <Input
            id="totp-code"
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
            className="mt-3 h-12 font-mono text-lg tracking-[0.35em] tabular-nums"
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
            code.length !== 6 ||
            verifying
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
              Enable two-factor authentication
            </>
          )}
        </Button>
      </form>


      <div className="flex gap-3 border-t pt-5">
        <KeyRound className="mt-0.5 size-4 shrink-0 text-muted-foreground" />

        <p className="text-xs leading-5 text-muted-foreground">
          KILIMO requires multi-factor authentication for
          administrative access. The authenticator secret
          should not be shared with another person.
        </p>
      </div>

    </div>
  )
}