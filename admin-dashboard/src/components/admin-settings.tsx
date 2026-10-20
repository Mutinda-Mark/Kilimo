"use client"

import {
  Check,
  Laptop,
  LogOut,
  Moon,
  ShieldCheck,
  Sun,
} from "lucide-react"

import {
  useTheme,
} from "next-themes"

import {
  useRouter,
} from "next/navigation"

import {
  useState,
} from "react"

import {
  createClient,
} from "@/lib/supabase/client"


type ThemeOption = {
  value:
    | "light"
    | "dark"
    | "system"

  label: string
  description: string
  icon: React.ElementType
}


const themeOptions: ThemeOption[] = [
  {
    value: "light",
    label: "Light",
    description:
      "Use the light dashboard appearance.",
    icon: Sun,
  },
  {
    value: "dark",
    label: "Dark",
    description:
      "Use the dark dashboard appearance.",
    icon: Moon,
  },
  {
    value: "system",
    label: "System",
    description:
      "Follow your device appearance setting.",
    icon: Laptop,
  },
]


export function AdminSettings({
  email,
  role,
}: {
  email: string
  role: string
}) {
  const {
    theme,
    setTheme,
  } =
    useTheme()

  const router =
    useRouter()


  const [
    signingOut,
    setSigningOut,
  ] =
    useState(false)

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
    <div className="space-y-6">

      {/* =================================================
          APPEARANCE
      ================================================= */}

      <section className="overflow-hidden rounded-2xl border bg-card">

        <div className="border-b px-6 py-5">

          <h2 className="text-base font-semibold">
            Appearance
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Choose how the KILIMO administration console
            appears on this device.
          </p>

        </div>


        <div className="grid gap-3 p-6 md:grid-cols-3">

          {themeOptions.map(
            (
              option
            ) => {
              const Icon =
                option.icon

              const selected =
                //mounted &&
                theme === option.value

              return (
                <button
                  key={
                    option.value
                  }
                  type="button"
                  onClick={() =>
                    setTheme(
                      option.value
                    )
                  }
                  className={[
                    "relative rounded-xl border p-4 text-left transition-colors",
                    "hover:bg-accent/50",
                    selected
                      ? "border-foreground bg-accent/40"
                      : "bg-background",
                  ].join(" ")}
                >

                  <div className="flex items-center justify-between">

                    <div className="flex size-9 items-center justify-center rounded-lg border bg-card">
                      <Icon className="size-4" />
                    </div>

                    {selected && (
                      <div className="flex size-5 items-center justify-center rounded-full bg-foreground text-background">
                        <Check className="size-3" />
                      </div>
                    )}

                  </div>


                  <p className="mt-4 text-sm font-medium">
                    {option.label}
                  </p>

                  <p className="mt-1 text-xs leading-5 text-muted-foreground">
                    {option.description}
                  </p>

                </button>
              )
            }
          )}

        </div>

      </section>


      {/* =================================================
          SECURITY
      ================================================= */}

      <section className="overflow-hidden rounded-2xl border bg-card">

        <div className="border-b px-6 py-5">

          <h2 className="text-base font-semibold">
            Security and access
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Review the security requirements protecting
            your administrative session.
          </p>

        </div>


        <div className="divide-y">

          <div className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">

            <div className="flex items-start gap-3">

              <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border bg-muted/30">
                <ShieldCheck className="size-4" />
              </div>

              <div>

                <p className="text-sm font-medium">
                  Multi-factor authentication
                </p>

                <p className="mt-1 text-xs text-muted-foreground">
                  Authenticator verification is required
                  before the administration console can be
                  accessed.
                </p>

              </div>

            </div>

            <span className="w-fit rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
              Enforced
            </span>

          </div>


          <div className="grid gap-4 px-6 py-5 sm:grid-cols-2">

            <div>

              <p className="text-xs text-muted-foreground">
                Signed-in account
              </p>

              <p className="mt-1 break-all text-sm font-medium">
                {email}
              </p>

            </div>


            <div>

              <p className="text-xs text-muted-foreground">
                KILIMO role
              </p>

              <p className="mt-1 text-sm font-medium">
                {role}
              </p>

            </div>

          </div>

        </div>

      </section>


      {/* =================================================
          SESSION
      ================================================= */}

      <section className="overflow-hidden rounded-2xl border bg-card">

        <div className="border-b px-6 py-5">

          <h2 className="text-base font-semibold">
            Session
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            Manage the current administrator session on
            this device.
          </p>

        </div>


        <div className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">

          <div>

            <p className="text-sm font-medium">
              Sign out of KILIMO
            </p>

            <p className="mt-1 max-w-xl text-xs leading-5 text-muted-foreground">
              Your current Supabase authentication session
              will be ended and you will need to authenticate
              again before accessing administrative pages.
            </p>

          </div>


          <button
            type="button"
            disabled={
              signingOut
            }
            onClick={
              signOut
            }
            className="inline-flex h-9 shrink-0 items-center justify-center gap-2 rounded-lg border bg-background px-4 text-sm font-medium transition-colors hover:bg-accent disabled:pointer-events-none disabled:opacity-50"
          >

            <LogOut className="size-4" />

            {signingOut
              ? "Signing out..."
              : "Sign out"}

          </button>

        </div>

      </section>

    </div>
  )
}