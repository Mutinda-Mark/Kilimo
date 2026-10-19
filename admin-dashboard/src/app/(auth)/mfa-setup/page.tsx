import {
  Leaf,
  ShieldCheck,
} from "lucide-react"

import { redirect } from "next/navigation"

import { MfaEnrollment } from "@/components/mfa-enrollment"

import { createClient } from "@/lib/supabase/server"

export const instant = false

export const metadata = {
  title:
    "Set up two-factor authentication",
}


export default async function MfaSetupPage() {
  const supabase =
    await createClient()

  const {
    data: {
      user,
    },
  } =
    await supabase.auth.getUser()

  if (!user) {
    redirect("/sign-in")
  }


  const {
    data: aal,
  } =
    await supabase.auth.mfa
      .getAuthenticatorAssuranceLevel()

  if (
    aal?.currentLevel ===
    "aal2"
  ) {
    redirect("/")
  }


  if (
    aal?.nextLevel ===
    "aal2"
  ) {
    redirect(
      "/mfa-challenge"
    )
  }


  return (
    <main className="min-h-screen bg-muted/20 px-6 py-12">
      <div className="mx-auto max-w-lg">

        <div className="mb-10">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg border bg-background">
              <Leaf className="size-4" />
            </div>

            <div>
              <p className="text-sm font-semibold">
                KILIMO
              </p>

              <p className="text-xs text-muted-foreground">
                Administration Security
              </p>
            </div>
          </div>


          <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
            <ShieldCheck className="size-3.5" />
            Security setup
          </div>

          <h1 className="text-3xl font-semibold tracking-tight">
            Protect your administrator account
          </h1>

          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            KILIMO requires an authenticator application
            in addition to Google sign-in. This additional
            factor protects administrative access if your
            Google account session is compromised.
          </p>
        </div>


        <div className="rounded-2xl border bg-background p-6 shadow-sm sm:p-8">
          <MfaEnrollment />
        </div>

      </div>
    </main>
  )
}