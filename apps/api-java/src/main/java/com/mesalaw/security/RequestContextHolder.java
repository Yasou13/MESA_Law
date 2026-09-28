package com.mesalaw.security;

/**
 * Thread-local holder for the current request's {@link RequestContext}.
 * Used to propagate tenant/user context through the request lifecycle.
 *
 * <p>Set by the TenantContextFilter at the start of each request,
 * cleared at the end. Replaces Python's contextvars-based approach.</p>
 */
public final class RequestContextHolder {

    private static final ThreadLocal<RequestContext> CONTEXT = new ThreadLocal<>();

    private RequestContextHolder() {
        // Utility class
    }

    public static void set(RequestContext context) {
        CONTEXT.set(context);
    }

    public static RequestContext get() {
        RequestContext ctx = CONTEXT.get();
        if (ctx == null) {
            throw new IllegalStateException("No RequestContext set. Is TenantContextFilter active?");
        }
        return ctx;
    }

    public static RequestContext getOrNull() {
        return CONTEXT.get();
    }

    public static void clear() {
        CONTEXT.remove();
    }
}
