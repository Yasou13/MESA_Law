export const telemetry = {
  /**
   * Tracks an event in the application.
   * If telemetry is disabled in firm settings, this will be a no-op.
   */
  trackEvent: (eventName: string, properties?: Record<string, unknown>) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Telemetry] ${eventName}`, properties)
    }
    // TODO: Integrate with PostHog or Amplitude
  },

  /**
   * Identifies a user for telemetry purposes.
   * The caller must pass a non-sensitive identifier; no compliance claim is implied.
   */
  identifyUser: (userId: string, traits?: Record<string, unknown>) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[Telemetry] Identify User ${userId}`, traits)
    }
    // TODO: Integrate with PostHog or Amplitude
  },

  /**
   * Captures an exception for error reporting.
   */
  captureException: (error: Error, context?: Record<string, unknown>) => {
    if (process.env.NODE_ENV === 'development') {
      console.error(`[Telemetry] Exception Captured:`, error, context)
    }
    // TODO: Integrate with Sentry
  }
}
