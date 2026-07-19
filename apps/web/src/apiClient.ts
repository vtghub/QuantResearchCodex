import { getConsole } from "./generated/apiClient";

export function fetchConsolePayload(signal?: AbortSignal) {
  return getConsole({}, signal);
}
