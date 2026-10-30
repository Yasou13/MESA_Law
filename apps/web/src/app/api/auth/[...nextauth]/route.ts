import NextAuth from "next-auth"
import KeycloakProvider from "next-auth/providers/keycloak"
import CredentialsProvider from "next-auth/providers/credentials"
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
  CredentialsProvider({
    id: "keycloak-credentials",
    name: "Keycloak Credentials",
    credentials: {
      username: { label: "Username or Email", type: "text" },
      password: { label: "Password", type: "password" },
    },
    async authorize(credentials) {
      if (!credentials?.username || !credentials?.password) {
        return null
      }

      const rawUrls = [
        process.env.KEYCLOAK_INTERNAL_URL,
        process.env.KEYCLOAK_PUBLIC_ISSUER,
        "http://localhost:8080/realms/mesa_law",
        "http://127.0.0.1:8080/realms/mesa_law",
      ].filter(Boolean) as string[]

      const baseCandidates = Array.from(
        new Set(rawUrls.map((u) => u.replace(/\/realms\/.*$/, "").replace(/\/$/, "")))
      )

      const bodyParams = new URLSearchParams()
      bodyParams.append("grant_type", "password")
      bodyParams.append("client_id", process.env.KEYCLOAK_CLIENT_ID || "mesa-client")
      if (process.env.KEYCLOAK_CLIENT_SECRET) {
        bodyParams.append("client_secret", process.env.KEYCLOAK_CLIENT_SECRET)
      }
      bodyParams.append("username", credentials.username.trim())
      bodyParams.append("password", credentials.password)
      bodyParams.append("scope", "openid profile email")

      for (const base of baseCandidates) {
        const tokenEndpoint = `${base}/realms/mesa_law/protocol/openid-connect/token`
        try {
          const res = await fetch(tokenEndpoint, {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
            },
            body: bodyParams.toString(),
          })

          if (!res.ok) {
            continue
          }

          const data = await res.json()
          if (!data.access_token) {
            continue
          }

          let name = credentials.username
          let email = credentials.username
          try {
            const parts = data.access_token.split(".")
            if (parts.length === 3) {
              const payload = JSON.parse(Buffer.from(parts[1], "base64").toString("utf-8"))
              name = payload.name || payload.preferred_username || name
              email = payload.email || email
            }
          } catch {
            // ignore token parse error
          }

          return {
            id: name,
            name,
            email,
            access_token: data.access_token,
          }
        } catch {
          // try next candidate base URL
        }
      }

      return null
    },
  }),
  KeycloakProvider({
    clientId: process.env.KEYCLOAK_CLIENT_ID || "mesa-client",
    clientSecret: process.env.KEYCLOAK_CLIENT_SECRET || "",
    issuer: process.env.KEYCLOAK_PUBLIC_ISSUER || "http://localhost:8080/realms/mesa_law",
    authorization: process.env.KEYCLOAK_PUBLIC_ISSUER ? `${process.env.KEYCLOAK_PUBLIC_ISSUER}/protocol/openid-connect/auth` : undefined,
    token: process.env.KEYCLOAK_INTERNAL_URL ? `${process.env.KEYCLOAK_INTERNAL_URL}/realms/mesa_law/protocol/openid-connect/token` : undefined,
    userinfo: process.env.KEYCLOAK_INTERNAL_URL ? `${process.env.KEYCLOAK_INTERNAL_URL}/realms/mesa_law/protocol/openid-connect/userinfo` : undefined,
  }),
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
