import NextAuth from "next-auth"
import KeycloakProvider from "next-auth/providers/keycloak"
import type { Provider } from "next-auth/providers/index"

const environment = process.env.MESA_LAW_ENVIRONMENT || "development"
const secureEnvironment = ["production", "staging", "pilot"].includes(environment)

function insecureSecret(value: string | undefined, minimum = 32): boolean {
  if (!value || value.length < minimum) return true
  return /(change_me|development|replace_with|supersecret|password123)/i.test(value)
}

if (
  secureEnvironment &&
  (
    insecureSecret(process.env.NEXTAUTH_SECRET) ||
    insecureSecret(process.env.KEYCLOAK_CLIENT_SECRET) ||
    !process.env.KEYCLOAK_PUBLIC_ISSUER?.startsWith("https://")
  )
) {
  throw new Error(
    "Secure deployments require strong secrets and an HTTPS Keycloak issuer",
  )
}

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
  secret: process.env.NEXTAUTH_SECRET,
  session: { strategy: "jwt", maxAge: 12 * 60 * 60 },
  pages: {
    signIn: '/login',
    error: '/login',
  },
  providers,
  callbacks: {
    async jwt({ token, account, user }) {
      if (account?.access_token) {
        token.accessToken = account.access_token;
      }
      const userAccessToken = user && 'access_token' in user ? user.access_token : undefined
      if (typeof userAccessToken === 'string') {
        token.accessToken = userAccessToken
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string | undefined;
      return session;
    }
  }
})

export { handler as GET, handler as POST }
