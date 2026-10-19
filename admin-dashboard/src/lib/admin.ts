import {
  createClient,
} from "@/lib/supabase/server"


export type AdminRole =
  | "super_admin"
  | "admin"
  | "viewer"


export interface AdminUser {
  id: string
  email: string
  display_name: string | null
  role: AdminRole
  status:
    | "active"
    | "suspended"
  created_at: string
  updated_at: string
}


export async function getAdminRecord(
  email: string
): Promise<AdminUser | null> {
  const supabase =
    await createClient()

  const {
    data,
    error,
  } =
    await supabase
      .from("admin_users")
      .select(
        [
          "id",
          "email",
          "display_name",
          "role",
          "status",
          "created_at",
          "updated_at",
        ].join(",")
      )
      .ilike(
        "email",
        email
          .trim()
          .toLowerCase()
      )
      .maybeSingle()


  if (error) {
    console.error(
      "Unable to load administrator record:",
      error.message
    )

    return null
  }


  return data as AdminUser | null
}