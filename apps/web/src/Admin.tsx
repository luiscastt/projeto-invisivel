import { useEffect, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { RefreshCw, ShieldCheck } from "lucide-react";
import { errorText, post, useApi, mediaBlob } from "./api";
import { useApp } from "./context";
import {
  categories,
  date,
  label,
  type IssueDetail,
  type ModerationItem,
} from "./models";
import { Busy, Empty, Err, External, LoginGate, PageTitle, Tag } from "./ui";
function EvidencePhoto({ url, caption }: { url: string; caption: string }) {
  const [src, setSrc] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    let live = true,
      objectUrl = "";
    mediaBlob(url)
      .then((blob) => {
        if (live) {
          objectUrl = URL.createObjectURL(blob);
          setSrc(objectUrl);
        }
      })
      .catch((e) => {
        if (live) setError(errorText(e));
      });
    return () => {
      live = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url]);
  return (
    <figure>
      {src && <img src={src} alt={caption || "Imagem em análise"} />}
      <figcaption>{caption || "Imagem em análise"}</figcaption>
      {error && <Err error={error} />}
    </figure>
  );
}
function Review({ r }: { r: ModerationItem }) {
  const cache = useQueryClient(),
    [action, setAction] = useState("approve"),
    [target, setTarget] = useState(r.existing_issue_id || ""),
    [reason, setReason] = useState(""),
    [err, setErr] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      await post(
        "/admin/reports/" + r.id + "/" + action,
        action === "approve"
          ? { reason: reason.trim(), issue_id: target.trim() || null }
          : { reason: reason.trim() },
      );
      await cache.invalidateQueries();
    } catch (e) {
      setErr(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="panel prose">
      <div className="inline-between">
        <small>
          {r.tracking_code} · {date(r.created_at)}
        </small>
        <Tag>{label(r.moderation_status)}</Tag>
        <Tag tone={r.is_demo ? "amber" : "green"}>
          {r.is_demo ? "Demonstração" : "Participação real"}
        </Tag>
      </div>
      <h2>{r.title}</h2>
      <p>
        {categories[r.category]} · {r.municipality_name} ·{" "}
        {r.neighborhood || "Sem bairro"}
      </p>
      <p className="pre">{r.description}</p>
      {r.clarifications?.map((reply, i) => <blockquote key={i}><strong>Esclarecimento privado · {date(reply.created_at)}</strong><p className="pre">{reply.description}</p></blockquote>)}
      <small>
        Coordenadas {r.latitude}, {r.longitude}
      </small>
      {r.flags.length > 0 && (
        <p>Sinalizações · {r.flags.map(label).join(", ")}</p>
      )}
      {r.evidence.map((ev) => (
        <EvidencePhoto key={ev.id} url={ev.url} caption={ev.caption} />
      ))}
      {r.sources.map((s) => (
        <p key={s.id || s.url}>
          <External url={s.url}>{s.title}</External> · {s.publisher}
        </p>
      ))}
      <form className="form-stack" onSubmit={submit}>
        <label>
          Decisão
          <select value={action} onChange={(e) => setAction(e.target.value)}>
            <option value="approve">Aprovar publicação</option>
            <option value="clarify">Solicitar esclarecimento</option>
            <option value="reject">Rejeitar relato</option>
          </select>
        </label>
        {action === "approve" && (
          <>
            <label>
              Vincular a um problema (opcional)
              <input
                list={"dups-" + r.id}
                placeholder="Vazio para criar um novo problema"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
              />
              <datalist id={"dups-" + r.id}>
                {r.duplicates.map((d) => (
                  <option key={d.issue.id} value={d.issue.id}>
                    {d.issue.title}
                  </option>
                ))}
              </datalist>
            </label>
            {r.duplicates.map((d) => (
              <div className="inline-between" key={d.issue.id}>
                <Link className="text-link" to={"/problemas/" + d.issue.id}>
                  {d.issue.title}
                </Link>
                <button
                  type="button"
                  className="text-btn"
                  onClick={() => setTarget(d.issue.id)}
                >
                  Selecionar
                </button>
              </div>
            ))}
          </>
        )}
        <label>
          Justificativa (pública se o relato for aprovado)
          <textarea
            required
            minLength={8}
            maxLength={2000}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
        </label>
        {err && <Err error={err} />}
        <button className="btn primary fit" disabled={busy}>
          {busy ? "Registrando…" : "Registrar decisão"}
        </button>
      </form>
    </article>
  );
}
function Manage({ initial }: { initial: string }) {
  const [id, setId] = useState(initial),
    [selected, setSelected] = useState(initial),
    [action, setAction] = useState("status"),
    [status, setStatus] = useState("in_progress"),
    [target, setTarget] = useState(""),
    [version, setVersion] = useState("1"),
    [reason, setReason] = useState(""),
    [busy, setBusy] = useState(false),
    [msg, setMsg] = useState(""),
    [err, setErr] = useState("");
  const issue = useApi<IssueDetail>(
      "/issues/" + encodeURIComponent(selected),
      !!selected,
    ),
    cache = useQueryClient();
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    setMsg("");
    try {
      const body =
        action === "status"
          ? { status, reason }
          : action === "restore"
            ? { version: Number(version), reason }
            : { target_id: target.trim(), reason };
      await post(action === "withdraw" ? "/admin/evidence/" + target + "/withdraw" : "/admin/issues/" + selected + "/" + action, action === "withdraw" ? {reason} : body);
      await cache.invalidateQueries();
      setMsg("Alteração registrada no histórico.");
      setReason("");
      if (action === "merge") {
        setId(target);
        setSelected(target);
      }
    } catch (e) {
      setErr(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel prose">
      <h2>Gerenciar dossiê</h2>
      <form
        className="filter-inline"
        onSubmit={(e) => {
          e.preventDefault();
          setSelected(id.trim());
          setMsg("");
          setErr("");
        }}
      >
        <label>
          Identificador do problema
          <input required value={id} onChange={(e) => setId(e.target.value)} />
        </label>
        <button className="btn secondary">Consultar</button>
      </form>
      {selected &&
        (issue.isLoading ? (
          <Busy />
        ) : issue.error ? (
          <Err error={issue.error} />
        ) : (
          issue.data && (
            <form className="form-stack" onSubmit={submit}>
              <h3>{issue.data.title}</h3>
              <small>
                Versão {issue.data.version} ·{" "}
                {label(issue.data.operational_status)}
              </small>
              <label>
                Operação
                <select
                  value={action}
                  onChange={(e) => setAction(e.target.value)}
                >
                  <option value="status">Alterar situação</option>
                  <option value="restore">Restaurar versão</option>
                  <option value="merge">Unificar com outro problema</option>
                  <option value="withdraw">Retirar evidência publicada</option>
                </select>
              </label>
              {action === "status" ? (
                <label>
                  Nova situação
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                  >
                    {[
                      "reported",
                      "corroborated",
                      "in_progress",
                      "declared_resolved",
                      "verified_resolved",
                      "contested",
                    ].map((s) => (
                      <option key={s} value={s}>
                        {label(s)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : action === "restore" ? (
                <label>
                  Versão a restaurar
                  <input
                    required
                    type="number"
                    min="1"
                    max={issue.data.version}
                    step="1"
                    value={version}
                    onChange={(e) => setVersion(e.target.value)}
                  />
                </label>
              ) : action === "withdraw" ? (
                <label>Evidência a retirar<select required value={target} onChange={e => setTarget(e.target.value)}><option value="">Selecione uma imagem publicada</option>{issue.data.evidence.map(e => <option key={e.id} value={e.id}>{e.caption || e.id}</option>)}</select></label>
              ) : (
                <label>
                  Identificador do dossiê de destino
                  <input
                    required
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                  />
                </label>
              )}
              <label>
                Justificativa pública
                <textarea
                  required
                  minLength={8}
                  maxLength={2000}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                />
              </label>
              <button disabled={busy} className="btn primary fit">
                Confirmar alteração
              </button>
            </form>
          )
        ))}
      {err && <Err error={err} />}
      <p role="status">{msg}</p>
    </section>
  );
}
export default function Admin() {
  const { user } = useApp();
  if (user.isLoading) return <Busy />;
  if (user.error) return <Err error={user.error} retry={user.refetch} />;
  if (!user.data) return <LoginGate action="acessar a moderação" />;
  if (user.data.role !== "admin")
    return (
      <section className="panel prose">
        <ShieldCheck />
        <h1>Acesso restrito</h1>
        <p>Apenas a equipe de moderação pode acessar esta área.</p>
        <Link to="/">Voltar ao painel</Link>
      </section>
    );
  return <AdminPanel />;
}
function AdminPanel() {
  const [params] = useSearchParams();
  const initial = params.get("problema") || "";
  const q = useApi<ModerationItem[]>("/admin/moderation"),
    [tab, setTab] = useState(initial ? "gestao" : "fila"),
    [syncMsg, setSyncMsg] = useState(""),
    [busy, setBusy] = useState(false),
    [err, setErr] = useState("");
  const audit = useApi<Record<string, unknown>[]>(
      "/admin/audit",
      tab === "auditoria",
    ),
    metrics = useApi<Record<string, unknown>>(
      "/admin/metrics",
      tab === "auditoria",
    );
  async function sync() {
    setBusy(true);
    setErr("");
    try {
      const result = await post<Record<string, unknown>>("/admin/sync", {});
      setSyncMsg(JSON.stringify(result, null, 2));
      await audit.refetch();
      await metrics.refetch();
    } catch (e) {
      setErr(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        title="Moderação"
        description="Revise contribuições, registre decisões e acompanhe o histórico administrativo."
      />
      <div className="tab-row">
        {[
          ["fila", "Fila de relatos"],
          ["gestao", "Gerenciar problemas"],
          ["auditoria", "Auditoria e dados"],
        ].map(([k, v]) => (
          <button
            className={"btn " + (tab === k ? "primary" : "secondary")}
            key={k}
            onClick={() => setTab(k)}
          >
            {v}
          </button>
        ))}
      </div>
      {tab === "fila" ? (
        q.isLoading ? (
          <Busy />
        ) : q.error ? (
          <Err error={q.error} retry={q.refetch} />
        ) : q.data?.length ? (
          q.data.map((r) => <Review key={r.id} r={r} />)
        ) : (
          <section className="panel">
            <Empty
              title="Fila de moderação em dia"
              text="Novos relatos aguardando revisão aparecem aqui."
              action={false}
            />
          </section>
        )
      ) : tab === "gestao" ? (
        <Manage initial={initial} />
      ) : (
        <section className="panel prose">
          <h2>Sincronização de fontes</h2>
          <button className="btn secondary" disabled={busy} onClick={sync}>
            <RefreshCw size={15} />
            {busy ? "Sincronizando…" : "Atualizar dados"}
          </button>
          {err && <Err error={err} />}
          <pre role="status">{syncMsg}</pre>
          <h2>Métricas</h2>
          {metrics.error ? (
            <Err error={metrics.error} />
          ) : (
            <pre>{JSON.stringify(metrics.data, null, 2)}</pre>
          )}
          <h2>Auditoria</h2>
          {audit.isLoading ? (
            <Busy />
          ) : audit.error ? (
            <Err error={audit.error} />
          ) : audit.data?.length ? (
            audit.data.map((row, i) => (
              <details key={i}>
                <summary>
                  {label(
                    String(
                      row.action || row.event_type || "Decisão administrativa",
                    ),
                  )}{" "}
                  · {date(String(row.created_at || ""))}
                </summary>
                <pre>{JSON.stringify(row, null, 2)}</pre>
              </details>
            ))
          ) : (
            <p>Nenhuma ação registrada.</p>
          )}
        </section>
      )}
    </>
  );
}
