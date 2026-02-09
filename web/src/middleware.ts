import { NextRequest, NextResponse } from "next/server"

const publicAdminPaths = ["/admin/login", "/admin/verify"]

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl

  if (pathname.startsWith("/admin") && !publicAdminPaths.includes(pathname)) {
    const session = req.cookies.get("admin_session")?.value
    if (!session) {
      return NextResponse.redirect(new URL("/admin/login", req.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/admin/:path*"],
}
