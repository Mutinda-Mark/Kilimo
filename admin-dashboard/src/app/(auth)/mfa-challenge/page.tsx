import {
  KeyRound,
  Leaf,
  ShieldCheck,
} from "lucide-react"

import {
  redirect,
} from "next/navigation"

import {
  MfaChallenge,
} from "@/components/mfa-challenge"

import {
  createClient,
} from "@/lib/supabase/server"

export const instant = false

export const metadata = {
  title:
    "Two-factor verification",
}


export default async function MfaChallengePage() {
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
    aal?.nextLevel !==
    "aal2"
  ) {
    redirect(
      "/mfa-setup"
    )
  }


  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/20 px-6 py-12">

      <div className="w-full max-w-md">

        <div className="mb-8 flex items-center justify-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl border bg-background">
            <Leaf className="size-5" />
          </div>

          <div>
            <p className="font-semibold tracking-tight">
              KILIMO
            </p>

            <p className="text-xs text-muted-foreground">
              Secure Administration
            </p>
          </div>
        </div>


        <div className="rounded-2xl border bg-background p-8 shadow-sm">

          <div className="mb-7 flex size-11 items-center justify-center rounded-xl bg-muted">
            <KeyRound className="size-5" />
          </div>


          <div className="mb-7">
            <div className="mb-2 flex items-center gap-2">
              <ShieldCheck className="size-4 text-muted-foreground" />

              <span className="text-xs font-medium uppercase tracking-[0.15em] text-muted-foreground">
                Second factor
              </span>
            </div>

            <h1 className="text-2xl font-semibold tracking-tight">
              Verify your identity
            </h1>

            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Google sign-in was successful. Complete the
              second authentication factor to access the
              KILIMO administration console.
            </p>
          </div>


          <MfaChallenge />

        </div>

      </div>

    </main>
  )
}