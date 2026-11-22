import { lazy, Suspense, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  MapPin,
  MessageSquarePlus,
  MinusCircle,
  Share2,
} from "lucide-react";
import { api, errorText, post, useApi } from "./api";
import { useApp } from "./context";
import {
  categories,
  date,
  label,
  hasIssuePoint,
  type Indicator,
  type IssueDetail,
  type Vote,
} from "./models";
import { Busy, Err, External, PageTitle, Tag } from "./ui";
import { Indicators } from "./Dashboard";
const TerritoryMap = lazy(() => import("./TerritoryMap"));
export default function Detail() {
  const { id } = useParams(),
    q = useApi<IssueDetail>("/issues/" + encodeURIComponent(id || ""));
  if (q.isLoading) return <Busy />;
  if (q.error || !q.data)
    return (
      <Err error={q.error || "Registro indisponível."} retry={q.refetch} />
    );
  return <Dossier key={q.data.id} item={q.data} />;
}
function Dossier({ item: i }: { item: IssueDetail }) {
  const { user } = useApp(),
    cache = useQueryClient(),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [linkCopied, setLinkCopied] = useState("");
  const stats = useApi<Indicator[]>(
    "/territories/" + i.municipality_code + "/indicators",
  );
  const vote = async (v: Vote | null) => {
    setBusy(true);
    setMessage("");
    try {
      const path = "/issues/" + i.id + "/votes";
      if (v) await post(path, { vote: v });
      else await api(path, { method: "DELETE" });
      await cache.invalidateQueries({ queryKey: ["/issues/" + i.id] });
      setMessage(v ? "Percepção registrada." : "Voto removido.");
    } catch (e) {
      setMessage(errorText(e));
    } finally {
      setBusy(false);
    }
  };
  const share = async () => {
    try {
      if (navigator.share)
        await navigator.share({ title: i.title, url: location.href });
      else {
        await navigator.clipboard.writeText(location.href);
        setLinkCopied("Link copiado.");
      }
    } catch (e) {
      if (!(e instanceof DOMException && e.name === "AbortError"))
        setLinkCopied(location.href);
    }
  };
  return (
    <>
      <Link to="/problemas" className="back">
        <ArrowLeft size={15} />
        Problemas do território
      </Link>
      <div className="tags">
        <Tag tone="green">{categories[i.category]}</Tag>
        <Tag>{label(i.operational_status)}</Tag>
        <Tag>{i.origin === "official" ? "Fonte oficial · Dossiê temático" : "Origem comunitária"}</Tag>
        {i.is_demo && <Tag tone="amber">Demonstração</Tag>}
      </div>
      <PageTitle
        title={i.title}
        description={[i.neighborhood, i.municipality_name, i.state_abbreviation]
          .filter(Boolean)
          .join(" · ")}
      >
        <button className="btn secondary" onClick={share}>
          <Share2 size={16} />
          Compartilhar
        </button>
      </PageTitle>
      {linkCopied && <p role="status">{linkCopied}</p>}
      {i.operational_status === "source_removed" && (
        <p className="notice">
          Os registros que originaram este dossiê não constam no recorte atual da fonte importada. O dossiê foi arquivado por atualização da fonte; isso não comprova que o problema foi resolvido.
        </p>
      )}
      <div className="content-grid">
        <div className="stack">
          <section className="panel prose">
            <h2>{i.origin === "official" ? "Resumo do dossiê temático" : "Resumo do problema"}</h2>
            <p className="pre">{i.summary}</p>
            <dl className="details">
              <dt>Identificador</dt>
              <dd>{i.id}</dd>
              <dt>Primeiro registro</dt>
              <dd>{date(i.first_reported_at)}</dd>
              <dt>Última atualização</dt>
              <dd>{date(i.last_activity_at)}</dd>
              <dt>Verificação</dt>
              <dd>{label(i.verification_status)}</dd>
              <dt>Prioridade</dt>
              <dd>
                {i.priority.score == null ? "Sem pontuação" : i.priority.score}{" "}
                · {i.priority.reason}
              </dd>
            </dl>
            {user.data?.role === "admin" && (
              <Link className="text-link" to={"/admin?problema=" + i.id}>
                Gerenciar este dossiê
              </Link>
            )}
          </section>
          {i.origin === "official" && (
            <section className="panel prose">
              <h2>Registros oficiais <small>{i.official_records_total ?? i.official_records_count ?? "—"}</small></h2>
              <p>Manifestações agrupadas por município, assunto, órgão e ano; não representam uma contagem de ocorrências físicas únicas. O registro na fonte oficial comprova o recebimento da manifestação, sem confirmar seu conteúdo.</p>
              <p>Município informado pela fonte; endereço não disponível. Encerramento da manifestação não comprova solução.</p>
              {(i.official_records || []).map((record) => (
                <article className="record" key={record.id}>
                  <strong>{record.subject}</strong>
                  <dl className="details">
                    <dt>Órgão</dt><dd>{record.agency || "Não informado"}</dd>
                    <dt>Ano</dt><dd>{record.year ?? "Não informado"}</dd>
                    <dt>Tipo de manifestação</dt><dd>{record.manifestation_type || "Não informado"}</dd>
                    <dt>Situação na fonte</dt><dd>{record.processing_status || "Não informada"}</dd>
                    <dt>Registro na fonte</dt><dd>{date(record.recorded_at)}</dd>
                  </dl>
                  <External url={record.source_url}>Consultar fonte original</External>
                </article>
              ))}
              {(i.official_records_total ?? 0) > (i.official_records?.length ?? 0) && (
                <p className="footnote">Exibindo {i.official_records?.length ?? 0} de {i.official_records_total} registros. Consulte a fonte original para o conjunto completo.</p>
              )}
            </section>
          )}
          <section className="panel prose">
            <h2>
              Relatos na plataforma <small>{i.reports.length}</small>
            </h2>
            {i.reports.map((r) => (
              <article className="record" key={r.id}>
                <strong>{r.display_name || "Participante anônimo"}</strong>
                <small>
                  {date(r.created_at)} · {label(r.contribution_type)}
                </small>
                <p className="pre">{r.description}</p>
              </article>
            ))}
            {!i.reports.length && <p>Nenhum relato publicado.</p>}
            <Link className="btn secondary" to={"/relatar?problema=" + i.id}>
              <MessageSquarePlus size={16} />
              Complementar problema
            </Link>
          </section>
          <section className="panel prose">
            <h2>Evidências e fontes</h2>
            {i.evidence.map((e) => (
              <figure key={e.id}>
                <img
                  loading="lazy"
                  src={e.url}
                  alt={e.caption || "Evidência fotográfica publicada"}
                />
                <figcaption>
                  {e.caption} · {label(e.verification_status)}
                </figcaption>
              </figure>
            ))}
            {i.sources.map((s) => (
              <article className="record" key={s.id}>
                <External url={s.url}>{s.title}</External>
                <small>
                  {s.publisher} · {date(s.published_at)} ·{" "}
                  {
                    {
                      official: "Oficial",
                      journalistic: "Jornalística",
                      community: "Comunitária",
                    }[s.source_type]
                  }
                </small>
              </article>
            ))}
            {!i.evidence.length && !i.sources.length && (
              <p>Nenhuma imagem ou referência publicada.</p>
            )}
          </section>
          <section className="panel prose">
            <h2>Histórico de atualizações</h2>
            {i.updates.map((u) => (
              <article className="timeline" key={u.id}>
                <Clock3 size={17} />
                <div>
                  <small>
                    {date(u.created_at)} · Versão {u.version}
                  </small>
                  <strong>{u.description}</strong>
                  {u.reason && <p>{u.reason}</p>}
                </div>
              </article>
            ))}
            {!i.updates.length && <p>Nenhuma atualização publicada.</p>}
          </section>
        </div>
        <aside className="stack">
          <section className="panel prose">
            <div className="eyebrow dark">PERCEPÇÃO COMUNITÁRIA</div>
            <h2>O problema foi resolvido?</h2>
            <p>
              Os votos registram a percepção dos participantes. A verificação
              depende de evidências.
            </p>
            <div className="vote-options">
              {(["RESOLVED", "UNRESOLVED"] as const).map((v) => (
                <button
                  key={v}
                  className={
                    "btn secondary " + (i.votes.my_vote === v ? "selected" : "")
                  }
                  aria-pressed={i.votes.my_vote === v}
                  disabled={!user.data || busy}
                  onClick={() => vote(v)}
                >
                  {v === "RESOLVED" ? (
                    <CheckCircle2 size={16} />
                  ) : (
                    <MinusCircle size={16} />
                  )}{" "}
                  {v === "RESOLVED" ? "Resolvido" : "Não resolvido"}
                  <b>
                    {v === "RESOLVED" ? i.votes.resolved : i.votes.unresolved}
                  </b>
                </button>
              ))}
            </div>
            {!user.data && (
              <Link
                className="text-link"
                to={
                  "/entrar?voltar=" + encodeURIComponent("/problemas/" + i.id)
                }
              >
                Entre para votar
              </Link>
            )}
            {i.votes.my_vote && (
              <button
                disabled={busy}
                className="text-btn"
                onClick={() => vote(null)}
              >
                Remover meu voto
              </button>
            )}
            <div role="status">{message}</div>
          </section>
          <section className="panel">
            <div className="panel-title">
              <h2>Localização</h2>
              <MapPin size={18} />
            </div>
            <Suspense fallback={<Busy />}>
              <TerritoryMap
                city={{
                  code: i.municipality_code,
                  name: i.municipality_name,
                  state_code: i.municipality_code.slice(0, 2),
                  state_abbreviation: i.state_abbreviation,
                  center: null,
                }}
                issues={[i]}
                picked={hasIssuePoint(i) ? [i.longitude, i.latitude] : null}
              />
            </Suspense>
            <p className="footnote">
              {hasIssuePoint(i) ? `${i.latitude}, ${i.longitude}` : "Localização apenas municipal; endereço não disponível na fonte."}
            </p>
          </section>
        </aside>
      </div>
      <section className="panel">
        <div className="panel-title">
          <h2>Indicadores de {i.municipality_name}</h2>
        </div>
        {stats.isLoading ? (
          <Busy />
        ) : stats.error ? (
          <Err error={stats.error} />
        ) : (
          <Indicators items={stats.data || []} />
        )}
      </section>
    </>
  );
}
