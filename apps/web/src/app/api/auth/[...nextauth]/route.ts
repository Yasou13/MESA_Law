import NextAuth from "next-auth"
import KeycloakProvider from "next-auth/providers/keycloak"

const handler = NextAuth({
  providers: [
    KeycloakProvider({
      clientId: "mesa-client",
      clientSecret: "mesa-client-secret",
      issuer: "http://localhost:8080/realms/mesa_law",
    })
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token
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
