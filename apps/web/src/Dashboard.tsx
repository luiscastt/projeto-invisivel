import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  CheckCheck,
  Compass,
  Layers3,
  Map as MapIcon,
  MapPin,
  MessagesSquare,
  Plus,
  ScanLine,
} from "lucide-react";
import { useApp } from "./context";
import { useApi } from "./api";
import {
  formatIndicator,
  number,
  type Indicator,
  type IssuePage,
  type Summary,
} from "./models";
import { Busy, Empty, Err, External, IssueRow } from "./ui";
const TerritoryMap = lazy(() => import("./TerritoryMap"));
function Contours() {
  return (
    <svg
      className="contours"
      viewBox="0 0 520 230"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <defs>
        <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
          <path
            d="M30 0H0V30"
            fill="none"
            stroke="#98b885"
            strokeOpacity=".15"
          />
        </pattern>
      </defs>
      <rect width="520" height="230" fill="url(#grid)" />
      <g fill="none" stroke="#afcc9b" strokeWidth="1.1">
        {Array.from({ length: 32 }, (_, i) => {
          const shift = i * 8;
          return (
            <path
              key={i}
              opacity={0.25 + (i % 5) * 0.035}
              d={
                "M" +
                (-240 + shift) +
                " 275 C" +
                (-235 + shift) +
                " 195 " +
                (-80 + shift) +
                " 243 " +
                (-77 + shift) +
                " 120 S" +
                (35 + shift) +
                " 85 " +
                (48 + shift) +
                " 10 S" +
                (137 + shift) +
                " -26 " +
                (155 + shift) +
                " -80"
              }
            />
          );
        })}
      </g>
      <g fill="none" stroke="#ccefa3" strokeWidth="1.4" opacity=".85">
        <path d="M337 112h17m-8.5-8.5v17m95 46h11m-5.5-5.5v11M232 53h9m-4.5-4.5v9" />
        <circle cx="345.5" cy="112" r="15" strokeDasharray="3 4" />
      </g>
    </svg>
  );
}
export function Indicators({ items }: { items: Indicator[] }) {
  return (
    <div className="indicator-list">
      {items.map((i) => (
        <div className="indicator" key={i.id}>
          <div>
            <strong>{i.name}</strong>
            <small>{i.year || "Ano indisponível"} · Escala municipal</small>
          </div>
          <div>
            <b>{formatIndicator(i)}</b>
            <small>
              <External url={i.source_url}>{i.source_name}</External>
            </small>
          </div>
        </div>
      ))}
      {!items.length && (
        <p className="muted">Dado não disponível para este município.</p>
      )}
    </div>
  );
}
export default function Dashboard() {
  const { city, demo } = useApp(),
    summary = useApi<Summary>(
      "/territories/" + city.code + "/summary?demo=" + demo,
    ),
    issues = useApi<IssuePage>(
      "/issues?municipality=" +
        city.code +
        "&demo=" +
        demo +
        "&sort=recent&page=1&page_size=50",
    );
  const counts = summary.data?.counts;
  const cards = [
    {
      name: "Problemas mapeados",
      v: counts?.total,
      icon: MapPin,
      tone: "forest",
    },
    { name: "Em aberto", v: counts?.unresolved, icon: ScanLine, tone: "amber" },
    { name: "Resolvidos", v: counts?.resolved, icon: CheckCheck, tone: "blue" },
    {
      name: "Relatos associados",
      v: counts?.reports,
      icon: MessagesSquare,
      tone: "violet",
    },
  ];
  return (
    <>
      <section className="hero">
        <Contours />
        <div className="hero-content">
          <div className="eyebrow">
            <i /> OBSERVATÓRIO TERRITORIAL
          </div>
          <h1>Panorama territorial</h1>
          <p>
            Explore os dados públicos e acompanhe os problemas de {city.name}.
          </p>
          <div className="hero-actions">
            <Link className="btn lime" to="/explorar">
              <Compass size={17} /> Explorar mapa <ArrowUpRight size={15} />
            </Link>
            <Link className="hero-link" to="/relatar">
              <Plus size={16} /> Novo relato
            </Link>
          </div>
        </div>
      </section>
      {summary.error && <Err error={summary.error} retry={summary.refetch} />}
      <div className="metrics">
        {cards.map((c) => (
          <article className="metric" key={c.name}>
            <div className={"metric-icon " + c.tone}>
              <c.icon size={19} />
            </div>
            <div>
              <strong>{c.v == null ? "—" : number(c.v)}</strong>
              <p>{c.name}</p>
            </div>
          </article>
        ))}
      </div>
      <div className="dashboard-grid">
        <section className="panel map-panel">
          <div className="panel-title">
            <div>
              <div className="eyebrow dark">
                <span className="line" /> CARTOGRAFIA
              </div>
              <h2>Mapa do território</h2>
            </div>
            <Link
              className="icon-btn"
              aria-label="Abrir mapa completo"
              to="/explorar"
            >
              <ArrowUpRight size={19} />
            </Link>
          </div>
          <Suspense fallback={<Busy />}>
            <TerritoryMap city={city} issues={issues.data?.items} />
          </Suspense>
          <div className="map-foot">
            <span>
              <i className="legend-line" /> Limite municipal
            </span>
            <span>
              <i className="legend-dot" /> Problema publicado
            </span>
          </div>
        </section>
        <section className="panel side-info">
          <div className="panel-title">
            <div>
              <div className="eyebrow dark">
                <span className="line" /> DADOS PÚBLICOS
              </div>
              <h2>Perfil municipal</h2>
            </div>
            <Layers3 size={20} />
          </div>
          <div className="territory-name">
            <div className="territory-icon">
              <MapIcon size={24} />
            </div>
            <div>
              <h3>{city.name}</h3>
              <small>
                {city.state_abbreviation} · IBGE {city.code}
              </small>
            </div>
          </div>
          {summary.isLoading ? (
            <Busy />
          ) : (
            <div className="profile-indicators">
              {(summary.data?.indicators || [])
                .filter(
                  (i, index, items) =>
                    i.value != null &&
                    items.findIndex(
                      (other) =>
                        other.sector === i.sector && other.value != null,
                    ) === index,
                )
                .slice(0, 2)
                .map((i) => (
                  <div key={i.id}>
                    <small>{i.name}</small>
                    <strong>{formatIndicator(i)}</strong>
                    <small>
                      <External url={i.source_url}>{i.source_name}</External> ·{" "}
                      {i.year || "Ano indisponível"} · Municipal
                    </small>
                  </div>
                ))}
              {!summary.data?.indicators.some((i) => i.value != null) && (
                <p className="muted">Indicadores municipais indisponíveis.</p>
              )}
            </div>
          )}
          <a className="panel-footer-link" href="#indicadores">
            Todos os indicadores <ArrowRight size={15} />
          </a>
        </section>
      </div>
      <section className="panel">
        <div className="panel-title">
          <div>
            <div className="eyebrow dark">
              <span className="line" /> ACOMPANHAMENTO
            </div>
            <h2>Problemas recentes</h2>
          </div>
          <Link className="text-link" to="/problemas">
            Ver todos <ArrowRight size={15} />
          </Link>
        </div>
        {issues.isLoading ? (
          <Busy />
        ) : issues.error ? (
          <Err error={issues.error} retry={issues.refetch} />
        ) : issues.data?.items.length ? (
          issues.data.items
            .slice(0, 4)
            .map((i) => <IssueRow key={i.id} issue={i} />)
        ) : (
          <Empty />
        )}
      </section>
      <section id="indicadores" className="panel">
        <div className="panel-title">
          <div>
            <h2>Indicadores oficiais</h2>
            <Link className="text-link" to="/dados">Cadastros, obras e ouvidoria</Link>
            <p>Referências municipais para {city.name}.</p>
          </div>
          <Link to="/fontes" className="text-link">
            Fontes <ArrowUpRight size={16} />
          </Link>
        </div>
        {summary.data && <Indicators items={summary.data.indicators} />}
        <p className="footnote">{summary.data?.assessment.reason}</p>
      </section>
    </>
  );
}
