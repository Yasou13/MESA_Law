import NextAuth from "next-auth"
import KeycloakProvider from "next-auth/providers/keycloak"
import CredentialsProvider from "next-auth/providers/credentials"
import type { Provider } from "next-auth/providers/index"

const providers: Provider[] = [
  KeycloakProvider({
    clientId: process.env.KEYCLOAK_CLIENT_ID || "mesa-client",
    clientSecret: process.env.KEYCLOAK_CLIENT_SECRET || "",
    issuer: process.env.KEYCLOAK_PUBLIC_ISSUER || "http://localhost:8080/realms/mesa_law",
    authorization: process.env.KEYCLOAK_PUBLIC_ISSUER ? `${process.env.KEYCLOAK_PUBLIC_ISSUER}/protocol/openid-connect/auth` : undefined,
    token: process.env.KEYCLOAK_INTERNAL_URL ? `${process.env.KEYCLOAK_INTERNAL_URL}/realms/mesa_law/protocol/openid-connect/token` : undefined,
    userinfo: process.env.KEYCLOAK_INTERNAL_URL ? `${process.env.KEYCLOAK_INTERNAL_URL}/realms/mesa_law/protocol/openid-connect/userinfo` : undefined,
  })
]

const handler = NextAuth({
  secret: process.env.NEXTAUTH_SECRET || "development_secret_only_do_not_use_in_prod",
  session: { strategy: "jwt", maxAge: 12 * 60 * 60 },
  pages: {
    signIn: '/login',
    error: '/login',
  },
  providers,
  callbacks: {
    async jwt({ token, account, trigger, session, user }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      if (user && 'activeFirmId' in user) {
        token.activeFirmId = (user as { activeFirmId?: string }).activeFirmId;
      }
      if (trigger === "update" && session?.activeFirmId) {
        token.activeFirmId = session.activeFirmId;
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string | undefined;
      session.activeFirmId = token.activeFirmId as string | undefined;
      return session;
    }
  }
})

export { handler as GET, handler as POST }

