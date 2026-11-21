import { useQuery } from "@tanstack/react-query";
import type { SupabaseClient } from "@supabase/supabase-js";
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
let token: string | undefined;
export function setToken(value?: string) {
  token = value;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", "Bearer " + token);
  let response: Response;
  try {
    response = await fetch("/api/v1" + path, {
      ...options,
      headers,
      credentials: "include",
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      0,
      "Não foi possível alcançar o servidor. Confira sua conexão.",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail =
      typeof body.detail === "string"
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail.map((x: { msg?: string }) => x.msg).join(" · ")
          : "Falha ao consultar o serviço (" + response.status + ").";
    throw new ApiError(response.status, detail);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export const post = <T>(path: string, body: unknown) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });
export function useApi<T>(path: string, enabled = true) {
  return useQuery<T, Error>({
    queryKey: [path],
    queryFn: () => api<T>(path),
    enabled,
  });
}
export function params(
  values: Record<string, string | number | boolean | undefined>,
) {
  const q = new URLSearchParams();
  Object.entries(values).forEach(([k, v]) => {
    if (v !== "" && v !== undefined) q.set(k, String(v));
  });
  return q.toString();
}
export type AuthConfig = {
  provider: "local" | "supabase";
  supabase_url: string;
  supabase_anon_key: string;
  local_test_accounts: boolean;
  test_accounts?: {
    email: string;
    password: string;
    display_name: string;
    role: string;
  }[];
};
export async function mediaBlob(path: string) {
  const url = new URL(path, location.origin);
  if (
    url.origin !== location.origin ||
    !url.pathname.startsWith("/api/v1/media/")
  )
    throw Error("Endereço de imagem inválido.");
  const headers = new Headers();
  if (token) headers.set("Authorization", "Bearer " + token);
  const response = await fetch(url, {
    credentials: "include",
    headers,
    cache: "no-store",
  });
  if (!response.ok) throw Error("Não foi possível consultar a imagem.");
  return response.blob();
}
let client: Promise<SupabaseClient> | undefined;
export function supabase(config: AuthConfig) {
  if (!client)
    client = import("@supabase/supabase-js").then(({ createClient }) =>
      createClient(config.supabase_url, config.supabase_anon_key),
    );
  return client;
}
export const errorText = (e: unknown) =>
  e instanceof Error ? e.message : "Não foi possível concluir a operação.";
