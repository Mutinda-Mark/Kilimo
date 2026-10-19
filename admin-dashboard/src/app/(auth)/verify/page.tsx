import { redirect } from "next/navigation"

import { createClient } from "@/lib/supabase/server"

export const instant = false

export const metadata = {
  title: "Security verification",
}


export default async function VerifyPage() {
  const supabase = await createClient()

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/sign-in")
  }

  const {
    data: aal,
    error: aalError,
  } =
    await supabase.auth.mfa
      .getAuthenticatorAssuranceLevel()

  if (aalError) {
    throw new Error(
      `Unable to determine authentication level: ${aalError.message}`
    )
  }

  /*
   * Already completed MFA for this session.
   */
  if (
    aal.currentLevel === "aal2"
  ) {
    redirect("/")
  }

  /*
   * aal1 -> aal2 means a verified MFA
   * factor already exists but has not yet
   * been completed for this session.
   */
  if (
    aal.currentLevel === "aal1" &&
    aal.nextLevel === "aal2"
  ) {
    redirect("/mfa-challenge")
  }

  /*
   * aal1 -> aal1 means the account does not
   * currently have an MFA factor enrolled.
   */
  redirect("/mfa-setup")
}