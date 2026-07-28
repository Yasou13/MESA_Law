import NextAuth from "next-auth";

declare module "next-auth" {
  interface Session {
    accessToken?: string;
    activeFirmId?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    activeFirmId?: string;
  }
}
