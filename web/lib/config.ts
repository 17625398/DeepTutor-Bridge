/**
 * Application branding configuration.
 *
 * For build-time configuration, set the environment variable:
 *   NEXT_PUBLIC_APP_NAME="My Tutor"
 *
 * For runtime configuration (after build), the app name is fetched from
 * the backend API at /api/v1/config/app. See AppConfigContext.tsx.
 */
export const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? "DeepTutor";
