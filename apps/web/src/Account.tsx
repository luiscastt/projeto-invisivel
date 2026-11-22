import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight,
  Download,
  LogOut,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { api, errorText, post, setToken, supabase, useApi } from "./api";
import { useApp } from "./context";
import { date, label, safeReturn } from "./models";
import { Busy, Dialog, Empty, Err, LoginGate, PageTitle, Tag } from "./ui";
export function Login() {
  const { config, user } = useApp(),
    cache = useQueryClient(),
    go = useNavigate(),
    [q] = useSearchParams();
  const [reg, setReg] = useState(false),
    [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [name, setName] = useState(""),
    [error, setError] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!config.data) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (config.data.provider === "supabase") {
        const client = await supabase(config.data);
        const result = reg
          ? await client.auth.signUp({
              email,
              password,
              options: {
                data: { display_name: name },
                emailRedirectTo: window.location.origin + "/entrar",
              },
            })
          : await client.auth.signInWithPassword({ email, password });
        if (result.error) throw result.error;
        if (!result.data.session) {
          setMessage("Confira seu e-mail para confirmar o cadastro.");
          return;
        }
        setToken(result.data.session.access_token);
      } else
        await post(
          reg ? "/auth/register" : "/auth/login",
          reg ? { email, password, display_name: name } : { email, password },
        );
      await cache.invalidateQueries();
      go(safeReturn(q.get("voltar")), { replace: true });
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        title="Minha conta"
        description="Participe do acompanhamento do território."
      />
      <section className="panel narrow form-stack">
        <div className="big-icon">
          <ShieldCheck />
        </div>
        <h2>{reg ? "Criar conta" : "Entrar na plataforma"}</h2>
        {user.data ? (
          <>
            <p>Você está conectado como {user.data.display_name}.</p>
            <Link className="btn primary" to="/perfil">
              Abrir meu perfil
            </Link>
          </>
        ) : config.isLoading ? (
          <Busy />
        ) : config.error ? (
          <Err error={config.error} retry={config.refetch} />
        ) : (
          <>
            <>
              {" "}
              {config.data?.provider === "local" &&
                config.data.local_test_accounts &&
                !reg && (
                  <div className="test-accounts">
                    <small>Contas de teste local</small>
                    <div className="actions">
                      {config.data.test_accounts?.map((a) => (
                        <button
                          key={a.email}
                          className="btn secondary"
                          type="button"
                          onClick={() => {
                            setEmail(a.email);
                            setPassword(a.password);
                            setError("");
                          }}
                        >
                          {a.role === "admin" ? "Moderação" : "Cidadão"}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
            </>
            <form className="form-stack" onSubmit={submit}>
              {reg && (
                <label>
                  Nome público ou pseudônimo
                  <input
                    autoComplete="nickname"
                    required
                    minLength={2}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </label>
              )}
              <label>
                E-mail
                <input
                  required
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>
              <label>
                Senha
                <input
                  required
                  minLength={reg ? 10 : 1}
                  maxLength={128}
                  type="password"
                  autoComplete={reg ? "new-password" : "current-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
              {reg && (
                <small>
                  Ao participar, consulte as informações de{" "}
                  <Link to="/privacidade">privacidade</Link>.
                </small>
              )}
              {error && <Err error={error} />}
              <div role="status">{message}</div>
              <button disabled={busy} className="btn primary">
                {busy ? "Aguarde…" : reg ? "Criar conta" : "Entrar"}
                <ArrowRight size={16} />
              </button>
            </form>
            <button
              className="text-btn"
              onClick={() => {
                setReg(!reg);
                setError("");
                setMessage("");
              }}
            >
              {reg ? "Já tenho uma conta" : "Criar minha conta"}
            </button>
          </>
        )}
      </section>
    </>
  );
}
type MyReport = {
  id: string;
  title: string;
  tracking_code: string;
  moderation_status: string;
  reason: string | null;
  created_at?: string;
  issue_id?: string | null;
  clarifications?: { description: string; created_at: string }[];
};

function ClarificationReply({ report }: { report: MyReport }) {
  const cache = useQueryClient();
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      await post(`/me/reports/${report.id}/reply`, { description });
      await cache.invalidateQueries({ queryKey: ["/me/reports"] });
      setDescription("");
    } catch(e) { setError(errorText(e)); }
    finally { setBusy(false); }
  }
  return <div className="form-stack">
    {report.clarifications?.map((r, i) => <p key={i}><strong>Resposta enviada · {date(r.created_at)}</strong><br />{r.description}</p>)}
    {report.moderation_status === "clarification_requested" && <form className="form-stack" onSubmit={submit}>
      <label>Responder à moderação<textarea required minLength={20} maxLength={3000} value={description} onChange={e => setDescription(e.target.value)} /></label>
      <small>Resposta privada para a equipe. O relato original permanece preservado.</small>
      {error && <Err error={error} />}
      <button disabled={busy} className="btn secondary fit">{busy ? "Enviando…" : "Enviar esclarecimento"}</button>
    </form>}
  </div>;
}
export function Profile() {
  const { user, config } = useApp(),
    cache = useQueryClient(),
    go = useNavigate(),
    reports = useApi<MyReport[]>("/me/reports", !!user.data);
  const [confirm, setConfirm] = useState(false),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function act(action: "logout" | "delete" | "export") {
    setBusy(true);
    setError("");
    try {
      if (action === "export") {
        const data = await api("/me/export");
        const url = URL.createObjectURL(
          new Blob([JSON.stringify(data, null, 2)], {
            type: "application/json",
          }),
        );
        const a = document.createElement("a");
        a.href = url;
        a.download = "invisivel-meus-dados.json";
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 2000);
        return;
      }
      if (action === "delete")
        await api("/me", {
          method: "DELETE",
          body: JSON.stringify(password ? { password } : {}),
        });
      if (config.data?.provider === "supabase") {
        const client = await supabase(config.data);
        await client.auth.signOut();
        setToken();
      } else if (action === "logout") await post("/auth/logout", {});
      cache.setQueryData(["session"], null);
      cache.removeQueries({
        predicate: (q) =>
          typeof q.queryKey[0] === "string" &&
          (q.queryKey[0].startsWith("/me/") ||
            q.queryKey[0].startsWith("/admin/") ||
            q.queryKey[0].startsWith("/issues/")),
      });
      await cache.invalidateQueries();
      setConfirm(false);
      go("/");
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  if (user.isLoading) return <Busy />;
  if (user.error) return <Err error={user.error} retry={user.refetch} />;
  if (!user.data) return <LoginGate action="acessar seu perfil" />;
  return (
    <>
      <PageTitle
        title="Meu perfil"
        description={user.data.display_name + " · " + user.data.email}
      >
        <button
          className="btn secondary"
          disabled={busy}
          onClick={() => act("logout")}
        >
          <LogOut size={15} />
          Sair
        </button>
      </PageTitle>
      <section className="panel">
        <div className="panel-title">
          <h2>Meus relatos</h2>
          <Link to="/relatar" className="text-link">
            Novo relato <ArrowRight size={15} />
          </Link>
        </div>
        {reports.isLoading ? (
          <Busy />
        ) : reports.error ? (
          <Err error={reports.error} retry={reports.refetch} />
        ) : reports.data?.length ? (
          reports.data.map((r) => (
            <article className="record" key={r.id}>
              <Tag>{label(r.moderation_status)}</Tag>
              <h3>{r.title}</h3>
              <small>
                {r.tracking_code}{" "}
                {r.created_at ? "· " + date(r.created_at) : ""}
              </small>
              {r.reason && <p>{r.reason}</p>}
              {(r.moderation_status === "clarification_requested" || !!r.clarifications?.length) && <ClarificationReply report={r} />}
              {r.issue_id && (
                <Link className="text-link" to={"/problemas/" + r.issue_id}>
                  Abrir dossiê publicado <ArrowRight size={14} />
                </Link>
              )}
            </article>
          ))
        ) : (
          <Empty
            title="Você ainda não enviou relatos"
            text="Os protocolos e as decisões da moderação aparecem aqui."
          />
        )}
      </section>
      <section className="panel prose">
        <h2>Dados da conta</h2>
        <p>Exporte uma cópia dos seus dados ou solicite a exclusão da conta.</p>
        <div className="actions">
          <button
            disabled={busy}
            className="btn secondary"
            onClick={() => act("export")}
          >
            <Download size={16} />
            Exportar dados
          </button>
          <button
            disabled={busy}
            className="btn danger"
            onClick={() => {
              setError("");
              setConfirm(true);
            }}
          >
            <Trash2 size={16} />
            Excluir conta
          </button>
        </div>
        {error && !confirm && <Err error={error} />}
      </section>
      {confirm && (
        <Dialog
          title="Excluir sua conta?"
          close={() => {
            if (!busy) setConfirm(false);
          }}
        >
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              void act("delete");
            }}
          >
            <p>
              A exclusão encerra o acesso e remove os dados privados.
              Contribuições públicas podem permanecer anonimizadas.
            </p>
            {config.data?.provider === "local" && (
              <label>
                Confirme sua senha
                <input
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>
            )}
            {error && <Err error={error} />}
            <div className="actions">
              <button
                type="button"
                className="btn secondary"
                onClick={() => setConfirm(false)}
              >
                Cancelar
              </button>
              <button disabled={busy} className="btn danger">
                Confirmar exclusão
              </button>
            </div>
          </form>
        </Dialog>
      )}
    </>
  );
}
