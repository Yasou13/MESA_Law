import NextAuth from "next-auth"
import KeycloakProvider from "next-auth/providers/keycloak"

const handler = NextAuth({
  secret: process.env.NEXTAUTH_SECRET || "development_secret_only_do_not_use_in_prod",
  session: { strategy: "jwt", maxAge: 12 * 60 * 60 },
  pages: {
    signIn: '/login',
    error: '/error',
  },
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_CLIENT_ID || "mesa-client",
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET || "",
      issuer: process.env.KEYCLOAK_PUBLIC_ISSUER || "http://localhost:8080/realms/mesa_law",
      authorization: process.env.KEYCLOAK_PUBLIC_ISSUER ? `${process.env.KEYCLOAK_PUBLIC_ISSUER}/protocol/openid-connect/auth` : undefined,
      token: process.env.KEYCLOAK_INTERNAL_URL ? `${process.env.KEYCLOAK_INTERNAL_URL}/realms/mesa_law/protocol/openid-connect/token` : undefined,
      userinfo: process.env.KEYCLOAK_INTERNAL_URL ? `${process.env.KEYCLOAK_INTERNAL_URL}/realms/mesa_law/protocol/openid-connect/userinfo` : undefined,
    })
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token
        // Set id_token or other fields if necessary
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
