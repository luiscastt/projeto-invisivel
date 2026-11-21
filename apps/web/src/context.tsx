import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  api,
  ApiError,
  useApi,
  supabase,
  setToken,
  type AuthConfig,
} from "./api";
import type { City, State, User } from "./models";
const pilot: City = {
  code: "3205002",
  state_code: "32",
  name: "Serra",
  state_abbreviation: "ES",
  center: null,
};
function useWorkspace() {
  const cache = useQueryClient(),
    config = useApi<AuthConfig>("/auth/config");
  const [authReady, setReady] = useState(false);
  useEffect(() => {
    if (!config.data) return;
    let active = true,
      unsubscribe: (() => void) | undefined;
    if (config.data.provider === "supabase")
      supabase(config.data)
        .then((client) => {
          if (!active) return;
          const { data } = client.auth.onAuthStateChange((_e, s) => {
            setToken(s?.access_token);
            setReady(true);
            void cache.invalidateQueries();
          });
          unsubscribe = () => data.subscription.unsubscribe();
        })
        .catch(() => {
          if (active) setReady(true);
        });
    else setReady(true);
    return () => {
      active = false;
      unsubscribe?.();
    };
  }, [config.data, cache]);
  const user = useQuery({
    queryKey: ["session"],
    enabled: authReady,
    queryFn: async () => {
      try {
        return await api<User>("/auth/me");
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null;
        throw e;
      }
    },
  });
  const [city, setCity] = useState<City>(pilot),
    [demo, setDemo] = useState(false);
  const states = useApi<State[]>("/states");
  const cityList = useApi<City[]>(
    "/states/" + city.state_code + "/municipalities",
  );
  const activeCity = cityList.data?.find((c) => c.code === city.code) ?? city;
  const [online, setOnline] = useState(navigator.onLine);
  useEffect(() => {
    const handler = () => setOnline(navigator.onLine);
    window.addEventListener("online", handler);
    window.addEventListener("offline", handler);
    return () => {
      window.removeEventListener("online", handler);
      window.removeEventListener("offline", handler);
    };
  }, []);
  return {
    city: activeCity,
    setCity,
    demo,
    setDemo,
    states,
    user: {
      ...user,
      isLoading:
        config.isLoading || (!authReady && !config.error) || user.isLoading,
      error: user.error || config.error,
    },
    config,
    online,
  };
}
const Context = createContext<ReturnType<typeof useWorkspace> | null>(null);
export function Provider({ children }: { children: ReactNode }) {
  const state = useWorkspace();
  return <Context.Provider value={state}>{children}</Context.Provider>;
}
export function useApp() {
  const c = useContext(Context);
  if (!c) throw Error("Contexto territorial ausente");
  return c;
}
