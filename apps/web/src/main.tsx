import { lazy, Suspense, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  Link,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  BookOpen,
  Calculator,
  ChevronDown,
  ChevronRight,
  Compass,
  Database,
  Download,
  FlaskConical,
  Globe2,
  Info,
  LayoutDashboard,
  ListChecks,
  MapPin,
  Menu,
  Plus,
  ShieldCheck,
  UserRound,
  WifiOff,
} from "lucide-react";
import { Provider, useApp } from "./context";
import { Brand, Busy, Dialog, ErrorBoundary } from "./ui";
import Dashboard from "./Dashboard";
import TerritorySelect from "./TerritorySelect";
import "./style.css";
const Explore = lazy(() => import("./Explore")),
  OfficialData = lazy(() => import("./OfficialData")),
  Detail = lazy(() => import("./Detail")),
  Report = lazy(() => import("./Report")),
  Simulator = lazy(() => import("./Simulator")),
  Admin = lazy(() => import("./Admin"));
const Login = lazy(() =>
    import("./Account").then((m) => ({ default: m.Login })),
  ),
  Profile = lazy(() =>
    import("./Account").then((m) => ({ default: m.Profile })),
  ),
  Sources = lazy(() =>
    import("./Information").then((m) => ({ default: m.Sources })),
  ),
  InfoPage = lazy(() =>
    import("./Information").then((m) => ({ default: m.Info })),
  );
const sections = [
  {
    name: "TERRITÓRIO",
    items: [
      { path: "/", name: "Visão geral", icon: LayoutDashboard },
      { path: "/explorar", name: "Explorar mapa", icon: Compass },
      { path: "/problemas", name: "Problemas", icon: ListChecks },
      { path: "/relatar", name: "Novo relato", icon: Plus },
      { path: "/simulador", name: "Simulador", icon: Calculator },
    ],
  },
  {
    name: "OBSERVATÓRIO",
    items: [
      { path: "/dados", name: "Dados e serviços", icon: Database },
      { path: "/fontes", name: "Fontes de dados", icon: Database },
      { path: "/metodologia", name: "Metodologia", icon: BookOpen },
      { path: "/sobre", name: "Sobre o projeto", icon: Info },
    ],
  },
];
type InstallEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: string }>;
};
const client = new QueryClient({
  defaultOptions: {
    queries: { retry: false, staleTime: 30000, refetchOnWindowFocus: false },
  },
});
function MenuList({ close }: { close?: () => void }) {
  const { user } = useApp();
  return (
    <>
      {sections.map((section) => (
        <div className="nav-group" key={section.name}>
          <small>{section.name}</small>
          {section.items.map((n) => (
            <NavLink
              end={n.path === "/"}
              to={n.path}
              key={n.path}
              onClick={close}
            >
              <n.icon size={18} />
              {n.name}
            </NavLink>
          ))}
        </div>
      ))}
      {user.data?.role === "admin" && (
        <div className="nav-group">
          <small>ADMINISTRAÇÃO</small>
          <NavLink to="/admin" onClick={close}>
            <ShieldCheck size={18} />
            Moderação
          </NavLink>
        </div>
      )}
    </>
  );
}
function Layout() {
  const { city, demo, setDemo, online, user } = useApp(),
    loc = useLocation(),
    [territory, setTerritory] = useState(false),
    [mobile, setMobile] = useState(false),
    [install, setInstall] = useState<InstallEvent | null>(null);
  const account = user.data ? "/perfil" : "/entrar",
    current =
      sections
        .flatMap((s) => s.items)
        .find((n) =>
          n.path === "/"
            ? loc.pathname === "/"
            : loc.pathname.startsWith(n.path),
        )?.name ||
      {
        "/entrar": "Minha conta",
        "/perfil": "Meu perfil",
        "/admin": "Moderação",
        "/privacidade": "Privacidade",
      }[loc.pathname] ||
      "Página";
  useEffect(() => {
    window.scrollTo(0, 0);
    setMobile(false);
    document.title = current + " · INVISIVEL";
  }, [loc.pathname, current]);
  useEffect(() => {
    const listen = (e: Event) => {
      e.preventDefault();
      setInstall(e as InstallEvent);
    };
    window.addEventListener("beforeinstallprompt", listen);
    return () => window.removeEventListener("beforeinstallprompt", listen);
  }, []);
  const demoSwitch = (
    <button
      className="demo-switch"
      type="button"
      role="switch"
      aria-checked={demo}
      aria-label="Modo demonstração"
      onClick={() => setDemo(!demo)}
    >
      <FlaskConical size={17} />
      <span>Modo demonstração</span>
      <i className={demo ? "on" : ""} />
    </button>
  );
  return (
    <div className="app">
      <a className="skip" href="#conteudo">
        Pular para o conteúdo
      </a>
      <aside className="sidebar">
        <div className="logo-area">
          <Brand />
          <span>Observatório territorial</span>
        </div>
        <nav aria-label="Navegação principal">
          <MenuList />
        </nav>
        <div className="side-bottom">
          {demoSwitch}
          {install && (
            <button
              className="install-btn"
              onClick={async () => {
                await install.prompt();
                await install.userChoice;
                setInstall(null);
              }}
            >
              <Download size={16} />
              Instalar aplicativo
            </button>
          )}
          <Link to="/privacidade">
            <ShieldCheck size={15} /> Privacidade
          </Link>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <Globe2 size={18} />
            <span>Observatório</span>
            <ChevronRight size={13} />
            <strong>{current}</strong>
          </div>
          <div className="mobile-brand">
            <button
              className="icon-btn"
              aria-label="Abrir menu"
              onClick={() => setMobile(true)}
            >
              <Menu size={20} />
            </button>
            <Brand />
          </div>
          <div className="top-actions">
            <button className="place-button" onClick={() => setTerritory(true)}>
              <MapPin size={16} />
              <span>
                {city.name}, {city.state_abbreviation}
              </span>
              <ChevronDown size={14} />
            </button>
            <Link
              className="account-button"
              to={account}
              aria-label={user.data ? "Meu perfil" : "Entrar"}
            >
              <UserRound size={17} />
              <span>{user.data ? "Meu perfil" : "Entrar"}</span>
            </Link>
          </div>
        </header>
        <main id="conteudo" tabIndex={-1} className="main-content">
          {!online && (
            <p className="notice">
              <WifiOff size={17} />
              Você está offline. Conecte-se para consultar dados ou enviar
              relatos.
            </p>
          )}
          {demo && (
            <div className="notice demo-banner">
              <FlaskConical size={16} />
              <span>
                Demonstração · Os problemas exibidos são ilustrativos. Os
                indicadores mantêm suas fontes oficiais.
              </span>
              <button onClick={() => setDemo(false)} className="text-btn">
                Sair
              </button>
            </div>
          )}
          <ErrorBoundary key={loc.pathname}>
            <Suspense fallback={<Busy />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route
                  path="/explorar"
                  element={<Explore key={city.code + demo + "mapa"} mapView />}
                />
                <Route
                  path="/problemas"
                  element={<Explore key={city.code + demo + "lista"} />}
                />
                <Route path="/problemas/:id" element={<Detail />} />
                <Route path="/relatar" element={<Report />} />
                <Route path="/entrar" element={<Login />} />
                <Route path="/perfil" element={<Profile />} />
                <Route path="/admin" element={<Admin />} />
                <Route path="/simulador" element={<Simulator />} />
                <Route path="/simulador/:id" element={<Simulator />} />
                <Route path="/fontes" element={<Sources />} />
                <Route path="/dados" element={<OfficialData key={city.code} />} />
                {(["sobre", "metodologia", "privacidade"] as const).map((k) => (
                  <Route
                    key={k}
                    path={"/" + k}
                    element={<InfoPage page={k} />}
                  />
                ))}
                <Route
                  path="*"
                  element={
                    <section className="panel prose">
                      <h1>Página não encontrada</h1>
                      <Link to="/">Voltar ao painel territorial</Link>
                    </section>
                  }
                />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </main>
        <footer>
          <span>INVISIVEL · Observatório territorial</span>
          <Link to="/privacidade">Privacidade</Link>
        </footer>
      </div>
      <nav className="bottom-nav" aria-label="Navegação móvel">
        {[
          { p: "/", n: "Início", i: LayoutDashboard },
          { p: "/explorar", n: "Mapa", i: Compass },
          { p: "/relatar", n: "Relatar", i: Plus },
          { p: "/problemas", n: "Problemas", i: ListChecks },
          { p: account, n: "Perfil", i: UserRound },
        ].map((n) => (
          <NavLink end={n.p === "/"} key={n.p} to={n.p}>
            <n.i size={19} />
            {n.n}
          </NavLink>
        ))}
      </nav>
      {territory && <TerritorySelect close={() => setTerritory(false)} />}{" "}
      {mobile && (
        <Dialog title="Navegação" close={() => setMobile(false)}>
          <nav className="drawer">
            <MenuList close={() => setMobile(false)} />
            {demoSwitch}
            <Link to="/privacidade" onClick={() => setMobile(false)}>
              Privacidade
            </Link>
            {install && (
              <button
                className="btn secondary"
                onClick={async () => {
                  await install.prompt();
                  await install.userChoice;
                  setInstall(null);
                }}
              >
                Instalar aplicativo
              </button>
            )}
          </nav>
        </Dialog>
      )}
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={client}>
    <BrowserRouter>
      <Provider>
        <Layout />
      </Provider>
    </BrowserRouter>
  </QueryClientProvider>,
);
if (import.meta.env.PROD && "serviceWorker" in navigator)
  window.addEventListener("load", () => {
    void navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
