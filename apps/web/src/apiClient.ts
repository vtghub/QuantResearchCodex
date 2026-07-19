import type { ConsolePayload } from "./consoleData";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchConsolePayload(signal?: AbortSignal): Promise<ConsolePayload> {
  const response = await fetch(`${apiBaseUrl}/api/v1/console`, {
    headers: {
      "x-role": "platform_admin"
    },
    signal
  });

  if (!response.ok) {
    throw new Error(`Console API returned ${response.status}`);
  }

  return response.json() as Promise<ConsolePayload>;
}
