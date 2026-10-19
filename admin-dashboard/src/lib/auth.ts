import {
  redirect,
} from "next/navigation"

import {
  getAdminRecord,
  type AdminUser,
} from "@/lib/admin"

import {
  createClient,
} from "@/lib/supabase/server"


export async function getCurrentUser() {
  const supabase =
    await createClient()

  const {
    data: {
      user,
    },
  } =
    await supabase.auth
      .getUser()

  return user
}


export async function requireAuthenticatedUser() {
  const user =
    await getCurrentUser()

  if (!user) {
    redirect("/sign-in")
  }

  return user
}


export async function requireAdminUser(): Promise<{
  user: Awaited<
    ReturnType<
      typeof requireAuthenticatedUser
    >
  >
  admin: AdminUser
}> {
  const supabase =
    await createClient()

  const {
    data: {
      user,
    },
  } =
    await supabase.auth
      .getUser()


  if (!user) {
    redirect("/sign-in")
  }


  const email =
    user.email
      ?.trim()
      .toLowerCase()


  if (!email) {
    redirect("/unauthorized")
  }


  const admin =
    await getAdminRecord(
      email
    )


  if (
    !admin ||
    admin.status !== "active"
  ) {
    redirect("/unauthorized")
  }


  const {
    data: aal,
    error: aalError,
  } =
    await supabase.auth.mfa
      .getAuthenticatorAssuranceLevel()


  if (aalError) {
    redirect("/verify")
  }


  if (
    aal.currentLevel === "aal2"
  ) {
    return {
      user,
      admin,
    }
  }


  if (
    aal.nextLevel === "aal2"
  ) {
    redirect(
      "/mfa-challenge"
    )
  }


  redirect(
    "/mfa-setup"
  )
}