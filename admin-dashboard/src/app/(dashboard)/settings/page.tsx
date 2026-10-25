import {
  AdminSettings,
} from "@/components/admin-settings"

import {
  requireAdminUser,
} from "@/lib/auth"


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


export default async function SettingsPage() {
  const {
    admin,
  } =
    await requireAdminUser()

  return (
    <main className="flex-1 px-6 py-8 lg:px-8 xl:px-10">

      <div className="mx-auto max-w-6xl">

        <div>

          <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Preferences
          </p>

          <h1 className="mt-2 text-2xl font-semibold tracking-tight">
            Settings
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Manage appearance, security information,
            and your current KILIMO administrator session.
          </p>

        </div>


        <div className="mt-8">

          <AdminSettings
            email={
              admin.email
            }
            role={
              roleLabel(
                admin.role
              )
            }
          />

        </div>

      </div>

    </main>
  )
}