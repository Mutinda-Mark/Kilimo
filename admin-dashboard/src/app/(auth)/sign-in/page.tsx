import {
  Leaf,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react"

import {
  GoogleSignInButton,
} from "@/components/google-sign-in-button"


export const metadata = {
  title: "Sign in",
}


export default function SignInPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">

        <section className="relative hidden overflow-hidden border-r bg-zinc-950 p-12 text-white lg:flex lg:flex-col">

          <div className="relative z-10 flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl border border-white/10 bg-white/10">
              <Leaf className="size-5" />
            </div>

            <div>
              <p className="font-semibold tracking-tight">
                KILIMO
              </p>

              <p className="text-xs text-zinc-400">
                Intelligence Console
              </p>
            </div>
          </div>


          <div className="relative z-10 my-auto max-w-xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-300">
              <ShieldCheck className="size-3.5" />
              Restricted administration environment
            </div>

            <h1 className="max-w-lg text-4xl font-semibold tracking-tight xl:text-5xl">
              Operational intelligence for the KILIMO platform.
            </h1>

            <p className="mt-5 max-w-lg text-sm leading-7 text-zinc-400">
              Monitor farmer activity, inspect tomato disease
              assessments, review analytics and supervise platform
              health from a secure administrative workspace.
            </p>
          </div>


          <div className="relative z-10 flex items-center gap-2 text-xs text-zinc-500">
            <LockKeyhole className="size-3.5" />
            Google identity and multi-factor authentication
          </div>


          <div
            aria-hidden="true"
            className="absolute -right-52 top-1/3 size-[520px] rounded-full bg-emerald-500/10 blur-3xl"
          />
        </section>


        <section className="flex items-center justify-center px-6 py-12 sm:px-12">
          <div className="w-full max-w-sm">

            <div className="mb-10 flex items-center gap-3 lg:hidden">
              <div className="flex size-9 items-center justify-center rounded-lg border">
                <Leaf className="size-4" />
              </div>

              <div>
                <p className="text-sm font-semibold">
                  KILIMO
                </p>

                <p className="text-xs text-muted-foreground">
                  Intelligence Console
                </p>
              </div>
            </div>


            <div className="mb-8">
              <p className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Administration
              </p>

              <h2 className="text-2xl font-semibold tracking-tight">
                Sign in to KILIMO
              </h2>

              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                Continue with an authorised Google account.
                Multi-factor verification is required before
                administrative access is granted.
              </p>
            </div>


            <GoogleSignInButton />


            <div className="my-8 h-px bg-border" />


            <div className="flex gap-3">
              <ShieldCheck className="mt-0.5 size-4 shrink-0 text-muted-foreground" />

              <p className="text-xs leading-5 text-muted-foreground">
                Access is restricted to authorised KILIMO
                administrators. Authentication activity may
                be recorded for security purposes.
              </p>
            </div>

          </div>
        </section>

      </div>
    </main>
  )
}