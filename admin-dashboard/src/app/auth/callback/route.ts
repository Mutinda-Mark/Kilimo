import {
  NextResponse,
} from "next/server"

import {
  createClient,
} from "@/lib/supabase/server"


export async function GET(
  request: Request
) {
  const url =
    new URL(request.url)

  const code =
    url.searchParams.get(
      "code"
    )

  const origin =
    url.origin

  if (!code) {
    return NextResponse.redirect(
      `${origin}/sign-in?error=oauth`
    )
  }


  const supabase =
    await createClient()

  const {
    error,
  } =
    await supabase.auth
      .exchangeCodeForSession(
        code
      )


  if (error) {
    return NextResponse.redirect(
      `${origin}/sign-in?error=oauth`
    )
  }


  /*
   * For now this goes to the MFA decision
   * route. In the next stage this page decides
   * whether to enroll or challenge an existing
   * TOTP factor.
   */
  return NextResponse.redirect(
    `${origin}/verify`
  )
}