import {
  BadgeCheck,
  CalendarDays,
  Clock3,
  KeyRound,
  Mail,
  ShieldCheck,
  UserRound,
} from "lucide-react"

import {
  requireAdminUser,
} from "@/lib/auth"

import {
  createClient,
} from "@/lib/supabase/server"


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


function formatDate(
  value:
    | string
    | null
    | undefined,
) {
  if (!value) {
    return "Not available"
  }

  const date =
    new Date(
      value
    )

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return "Not available"
  }

  return new Intl.DateTimeFormat(
    "en-KE",
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  ).format(
    date
  )
}


function providerLabel(
  provider:
    | string
    | undefined,
) {
  if (!provider) {
    return "Supabase"
  }

  switch (
    provider.toLowerCase()
  ) {
    case "google":
      return "Google"

    case "email":
      return "Email"

    default:
      return (
        provider
          .charAt(0)
          .toUpperCase()
        +
        provider.slice(1)
      )
  }
}


export default async function ProfilePage() {
  const {
    user,
    admin,
  } =
    await requireAdminUser()

  const supabase =
    await createClient()

  const {
    data: aal,
  } =
    await supabase.auth.mfa
      .getAuthenticatorAssuranceLevel()

  const displayName =
    admin.display_name ??
    user.user_metadata
      ?.full_name ??
    user.user_metadata
      ?.name ??
    "Administrator"

  const provider =
    user.app_metadata
      ?.provider

  const currentAal =
    aal?.currentLevel ??
    "unknown"

  const mfaProtected =
    currentAal === "aal2"

  return (
    <main className="flex-1 px-6 py-8 lg:px-8 xl:px-10">
      <div className="mx-auto max-w-6xl">

        {/* =================================================
            HEADER
        ================================================= */}

        <div>
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Account
          </p>

          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            Administrator profile
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Review your authenticated KILIMO administrator
            identity and account security information.
          </p>
        </div>


        {/* =================================================
            PROFILE HERO
        ================================================= */}

        <section className="mt-8 overflow-hidden rounded-2xl border bg-card">

          <div className="border-b bg-muted/20 px-6 py-6 md:px-8">

            <div className="flex flex-col gap-5 sm:flex-row sm:items-center">

              <div className="flex size-20 shrink-0 items-center justify-center rounded-2xl border bg-background font-mono text-xl font-semibold shadow-sm">
                {initials(
                  displayName
                )}
              </div>

              <div className="min-w-0">

                <div className="flex flex-wrap items-center gap-2">

                  <h2 className="truncate text-xl font-semibold">
                    {displayName}
                  </h2>

                  {admin.status === "active" && (
                    <span className="inline-flex items-center gap-1 rounded-full border bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400">
                      <BadgeCheck className="size-3.5" />
                      Active
                    </span>
                  )}

                </div>

                <p className="mt-1 truncate text-sm text-muted-foreground">
                  {admin.email}
                </p>

                <p className="mt-2 text-xs font-medium text-muted-foreground">
                  {roleLabel(
                    admin.role
                  )}
                </p>

              </div>

            </div>

          </div>


          {/* =================================================
              IDENTITY DETAILS
          ================================================= */}

          <div className="grid gap-0 md:grid-cols-2">

            <ProfileField
              icon={
                <UserRound className="size-4" />
              }
              label="Display name"
              value={displayName}
            />

            <ProfileField
              icon={
                <Mail className="size-4" />
              }
              label="Email address"
              value={
                user.email ??
                admin.email
              }
            />

            <ProfileField
              icon={
                <ShieldCheck className="size-4" />
              }
              label="Administrator role"
              value={
                roleLabel(
                  admin.role
                )
              }
            />

            <ProfileField
              icon={
                <KeyRound className="size-4" />
              }
              label="Authentication provider"
              value={
                providerLabel(
                  provider
                )
              }
            />

            <ProfileField
              icon={
                <CalendarDays className="size-4" />
              }
              label="Account created"
              value={
                formatDate(
                  user.created_at
                )
              }
            />

            <ProfileField
              icon={
                <Clock3 className="size-4" />
              }
              label="Last sign-in"
              value={
                formatDate(
                  user.last_sign_in_at
                )
              }
            />

          </div>

        </section>


        {/* =================================================
            SECURITY
        ================================================= */}

        <section className="mt-6">

          <div className="mb-4">
            <h2 className="text-base font-semibold">
              Account security
            </h2>

            <p className="mt-1 text-sm text-muted-foreground">
              Authentication controls protecting this
              administrator session.
            </p>
          </div>


          <div className="grid gap-4 md:grid-cols-2">

            <div className="rounded-xl border bg-card p-5">

              <div className="flex items-start gap-4">

                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border bg-muted/30">
                  <ShieldCheck className="size-5" />
                </div>

                <div>

                  <div className="flex items-center gap-2">

                    <p className="text-sm font-medium">
                      Multi-factor authentication
                    </p>

                    <span
                      className={
                        mfaProtected
                          ? "rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400"
                          : "rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-400"
                      }
                    >
                      {mfaProtected
                        ? "Protected"
                        : "Verification required"}
                    </span>

                  </div>

                  <p className="mt-2 text-xs leading-5 text-muted-foreground">
                    KILIMO administrative access requires
                    authenticator-based multi-factor
                    verification.
                  </p>

                </div>

              </div>

            </div>


            <div className="rounded-xl border bg-card p-5">

              <div className="flex items-start gap-4">

                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg border bg-muted/30">
                  <KeyRound className="size-5" />
                </div>

                <div>

                  <p className="text-sm font-medium">
                    Assurance level
                  </p>

                  <p className="mt-2 font-mono text-sm font-semibold uppercase">
                    {currentAal}
                  </p>

                  <p className="mt-1 text-xs leading-5 text-muted-foreground">
                    AAL2 confirms that both the primary
                    identity and second authentication factor
                    have been verified.
                  </p>

                </div>

              </div>

            </div>

          </div>

        </section>


        {/* =================================================
            READ-ONLY NOTE
        ================================================= */}

        <div className="mt-6 rounded-xl border border-dashed bg-muted/20 px-5 py-4">

          <p className="text-sm font-medium">
            Managed identity
          </p>

          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Authentication-controlled identity fields are
            read-only in KILIMO. Changes to the sign-in
            identity must be performed through the connected
            authentication provider or administrator access
            configuration.
          </p>

        </div>

      </div>
    </main>
  )
}


function ProfileField({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex gap-4 border-b p-6 last:border-b-0 md:[&:nth-last-child(-n+2)]:border-b-0 md:[&:nth-child(odd)]:border-r">

      <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg border bg-muted/30 text-muted-foreground">
        {icon}
      </div>

      <div className="min-w-0">

        <p className="text-xs font-medium text-muted-foreground">
          {label}
        </p>

        <p className="mt-1 break-words text-sm font-medium">
          {value}
        </p>

      </div>

    </div>
  )
}