import { lazy, Suspense, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  List,
  Map as MapIcon,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { useApp } from "./context";
import { params, useApi } from "./api";
import { categories, label, type IssuePage, type Neighborhood } from "./models";
import { Busy, Empty, Err, IssueRow, PageTitle, ReportButton } from "./ui";
const TerritoryMap = lazy(() => import("./TerritoryMap"));
const operational = [
  "reported",
  "corroborated",
  "in_progress",
  "declared_resolved",
  "verified_resolved",
  "contested",
];
export default function Explore({ mapView = false }: { mapView?: boolean }) {
  const { city, demo } = useApp(),
    [q, setQ] = useSearchParams(),
    [extra, setExtra] = useState(false);
  const page = Math.max(1, Number(q.get("pagina")) || 1);
  const get = (key: string) => q.get(key) || "";
  function change(key: string, value: string) {
    setQ(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete("pagina");
        if (value) next.set(key, value);
        else next.delete(key);
        return next;
      },
      { replace: true },
    );
  }
  const neighborhoods = useApi<Neighborhood[]>(
    "/municipalities/" + city.code + "/neighborhoods",
  );
  const issues = useApi<IssuePage>(
    "/issues?" +
      params({
        municipality: city.code,
        demo,
        search: get("busca"),
        category: get("categoria"),
        operational_status: get("situacao"),
        verification_status: get("verificacao"),
        neighborhood: get("bairro"),
        sort: get("ordem") || "recent",
        page,
        page_size: mapView ? 100 : 20,
      }),
  );
  const filtered = [
    "busca",
    "categoria",
    "situacao",
    "bairro",
    "verificacao",
  ].some((k) => get(k));
  return (
    <>
      <PageTitle
        title={mapView ? "Explorar território" : "Problemas do território"}
        description={
          "Consulte os registros públicos de " +
          city.name +
          " · " +
          city.state_abbreviation +
          "."
        }
      >
        <ReportButton />
      </PageTitle>
      <section className="panel filter-panel">
        <div className="filters">
          <label className="search-field">
            <span>Pesquisar</span>
            <div className="input-icon">
              <Search />
              <input
                placeholder="Título ou descrição"
                value={get("busca")}
                onChange={(e) => change("busca", e.target.value)}
              />
            </div>
          </label>
          <label>
            Categoria
            <select
              value={get("categoria")}
              onChange={(e) => change("categoria", e.target.value)}
            >
              <option value="">Todas as categorias</option>
              {Object.entries(categories).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </label>
          <label>
            Situação
            <select
              value={get("situacao")}
              onChange={(e) => change("situacao", e.target.value)}
            >
              <option value="">Todas as situações</option>
              {operational.map((s) => (
                <option key={s} value={s}>
                  {label(s)}
                </option>
              ))}
            </select>
          </label>
          <button
            className="btn secondary"
            onClick={() => setExtra(!extra)}
            aria-expanded={extra}
          >
            <SlidersHorizontal size={16} /> Filtros
          </button>
        </div>
        {extra && (
          <div className="filters filters-extra">
            <label>
              Bairro
              <select
                value={get("bairro")}
                onChange={(e) => change("bairro", e.target.value)}
              >
                <option value="">Todos os bairros</option>
                {neighborhoods.data?.map((n) => (
                  <option key={n.id}>{n.name}</option>
                ))}
              </select>
            </label>
            <label>
              Verificação
              <select
                value={get("verificacao")}
                onChange={(e) => change("verificacao", e.target.value)}
              >
                <option value="">Todas as verificações</option>
                <option value="community_report">Relato comunitário</option>
              </select>
            </label>
            <label>
              Ordenar
              <select
                value={get("ordem") || "recent"}
                onChange={(e) => change("ordem", e.target.value)}
              >
                <option value="recent">Mais recentes</option>
                <option value="reports">Mais relatos</option>
                <option value="priority">Prioridade</option>
                <option value="unresolved">Em aberto</option>
              </select>
            </label>
          </div>
        )}
        {filtered && (
          <button className="text-btn" onClick={() => setQ({})}>
            Limpar filtros
          </button>
        )}
      </section>
      <section className="panel">
        <div className="panel-title">
          <div>
            <div className="eyebrow dark">
              <span className="line" /> {city.name.toLocaleUpperCase("pt-BR")}
            </div>
            <h2>
              {issues.data
                ? issues.data.total +
                  " " +
                  (issues.data.total === 1
                    ? "problema encontrado"
                    : "problemas encontrados")
                : "Registros territoriais"}
            </h2>
          </div>
          <div className="segmented">
            <Link
              className={mapView ? "active" : ""}
              aria-label="Exibir mapa"
              to={"/explorar?" + q}
            >
              <MapIcon size={16} /> Mapa
            </Link>
            <Link
              className={!mapView ? "active" : ""}
              aria-label="Exibir lista"
              to={"/problemas?" + q}
            >
              <List size={16} /> Lista
            </Link>
          </div>
        </div>
        {mapView && (
          <Suspense fallback={<Busy />}>
            <TerritoryMap city={city} issues={issues.data?.items} />
          </Suspense>
        )}
        {issues.isLoading ? (
          <Busy />
        ) : issues.error ? (
          <Err error={issues.error} retry={issues.refetch} />
        ) : issues.data?.items.length ? (
          issues.data.items.map((i) => <IssueRow key={i.id} issue={i} />)
        ) : (
          <Empty
            title={filtered ? "Nenhum resultado para estes filtros" : undefined}
            text={
              filtered
                ? "Ajuste a busca ou limpe os filtros para consultar outros registros."
                : undefined
            }
            action={!filtered}
          />
        )}
        {issues.data && issues.data.total > issues.data.page_size && (
          <div className="pagination">
            <button
              className="icon-btn"
              disabled={page === 1}
              aria-label="Página anterior"
              onClick={() => change("pagina", String(page - 1))}
            >
              <ChevronLeft />
            </button>
            Página {page} de{" "}
            {Math.ceil(issues.data.total / issues.data.page_size)}
            <button
              className="icon-btn"
              disabled={page * issues.data.page_size >= issues.data.total}
              aria-label="Próxima página"
              onClick={() => change("pagina", String(page + 1))}
            >
              <ChevronRight />
            </button>
          </div>
        )}
      </section>
    </>
  );
}
