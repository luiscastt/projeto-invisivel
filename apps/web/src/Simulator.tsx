import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  BarChart,
  Bar,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArrowRight, Calculator, ExternalLink } from "lucide-react";
import { errorText, post, useApi } from "./api";
import { useApp } from "./context";
import {
  categories,
  money,
  number,
  type Intervention,
  type Simulation,
} from "./models";
import { Busy, Err, IssueRow, PageTitle, Tag } from "./ui";
const strategies = {
  priority: "Maior prioridade",
  recent: "Mais recentes",
  reports: "Mais relatos",
};
type Strategy = keyof typeof strategies;
function Result({ s }: { s: Simulation }) {
  return (
    <section className="panel prose">
      <div className="inline-between">
        <Tag tone={s.demo ? "amber" : "green"}>
          {s.demo ? "Cenário de demonstração" : "Cenário salvo"}
        </Tag>
        <Link className="text-link" to={"/simulador/" + s.id}>
          Link do cenário <ExternalLink size={14} />
        </Link>
      </div>
      <h2>{strategies[s.strategy as Strategy] || s.strategy}</h2>
      <dl className="details">
        <dt>Categoria</dt>
        <dd>{categories[s.category]}</dd>
        <dt>Município (IBGE)</dt>
        <dd>{s.municipality_code}</dd>
        <dt>Orçamento</dt>
        <dd>{money(s.budget)}</dd>
        <dt>Custo por unidade</dt>
        <dd>{money(s.unit_cost)}</dd>
        <dt>Capacidade teórica</dt>
        <dd>{number(s.capacity)}</dd>
        <dt>Problemas contemplados</dt>
        <dd>{s.selected_count}</dd>
        <dt>Investimento simulado</dt>
        <dd>{money(s.spent)}</dd>
        <dt>Saldo</dt>
        <dd>{money(s.balance)}</dd>
      </dl>
      {!!s.excluded_official_dossiers && (
        <p className="footnote">
          {s.excluded_official_dossiers} dossiês oficiais de escala municipal foram excluídos do cálculo de custo por intervenção física; não identificam intervenções pontuais.
        </p>
      )}
      {s.issues.length > 0 && (
        <details>
          <summary>Ver problemas selecionados</summary>
          {s.issues.map((i) => (
            <IssueRow key={i.id} issue={i} />
          ))}
        </details>
      )}
      {s.assumptions.length > 0 && (
        <ul>
          {s.assumptions.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
      <p className="footnote">{s.disclaimer}</p>
    </section>
  );
}
export default function Simulator() {
  const { id } = useParams(),
    saved = useApi<Simulation>(
      "/simulations/" + encodeURIComponent(id || ""),
      !!id,
    ),
    list = useApi<Intervention[]>("/interventions", !id),
    { city, demo } = useApp();
  if (id)
    return (
      <>
        <PageTitle
          title="Cenário de investimento"
          description="Parâmetros e resultado da simulação salva."
        >
          <Link className="btn secondary" to="/simulador">
            Nova simulação
          </Link>
        </PageTitle>
        {saved.isLoading ? (
          <Busy />
        ) : saved.error ? (
          <Err error={saved.error} />
        ) : (
          saved.data && <Result s={saved.data} />
        )}
      </>
    );
  return (
    <>
      <PageTitle
        title="Simulador de investimentos"
        description={
          "Compare a aplicação de um orçamento hipotético em " + city.name + "."
        }
      />
      {list.isLoading ? (
        <Busy />
      ) : list.error ? (
        <Err error={list.error} retry={list.refetch} />
      ) : list.data?.length ? (
        <Scenario key={city.code + "-" + demo} options={list.data} />
      ) : (
        <p className="notice">Nenhuma intervenção disponível para simulação.</p>
      )}
    </>
  );
}
function Scenario({ options }: { options: Intervention[] }) {
  const { city, demo } = useApp(),
    [opt, setOpt] = useState(options[0]),
    [budget, setBudget] = useState("100000"),
    [cost, setCost] = useState(String(opt.default_unit_cost)),
    [first, setFirst] = useState<Strategy>("priority"),
    [second, setSecond] = useState<Strategy>("reports"),
    [compare, setCompare] = useState(true),
    [res, setRes] = useState<Simulation[]>([]),
    [busy, setBusy] = useState(false),
    [err, setErr] = useState("");
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr("");
    setRes([]);
    const base = {
      municipality_code: city.code,
      category: opt.category,
      budget: Number(budget),
      unit_cost: Number(cost),
      demo,
    };
    try {
      const a = await post<Simulation>("/simulations", {
        ...base,
        strategy: first,
      });
      setRes([a]);
      if (compare) {
        const b = await post<Simulation>("/simulations", {
          ...base,
          strategy: second,
        });
        setRes([a, b]);
      }
    } catch (e) {
      setErr(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <section className="panel prose">
        <div className="section-head">
          <h2>Configurar cenário</h2>
          <Calculator size={20} />
        </div>
        <form className="form-stack" onSubmit={submit}>
          <label>
            Intervenção
            <select
              value={opt.id}
              onChange={(e) => {
                const n = options.find((o) => o.id === e.target.value)!;
                setOpt(n);
                setCost(String(n.default_unit_cost));
              }}
            >
              {options.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <p>{opt.assumption}</p>
          <div className="fields">
            <label>
              Orçamento hipotético (R$)
              <input
                required
                type="number"
                min="0"
                max="100000000000"
                step="0.01"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
              />
            </label>
            <label>
              Custo por {opt.unit} (R$)
              <input
                required
                type="number"
                min="0.01"
                max="1000000000"
                step="0.01"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
              />
            </label>
          </div>
          <label className="check-row">
            <input
              type="checkbox"
              checked={compare}
              onChange={(e) => setCompare(e.target.checked)}
            />
            Comparar duas estratégias
          </label>
          <div className="fields">
            <label>
              Estratégia principal
              <select
                value={first}
                onChange={(e) => {
                  const v = e.target.value as Strategy;
                  setFirst(v);
                  if (second === v) setSecond(first);
                }}
              >
                {Object.entries(strategies).map(([k, v]) => (
                  <option key={k} value={k}>
                    {v}
                  </option>
                ))}
              </select>
            </label>
            {compare && (
              <label>
                Estratégia comparativa
                <select
                  value={second}
                  onChange={(e) => setSecond(e.target.value as Strategy)}
                >
                  {Object.entries(strategies)
                    .filter(([k]) => k !== first)
                    .map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                </select>
              </label>
            )}
          </div>
          <p>
            O custo unitário é uma hipótese editável. Os resultados são salvos
            para consulta por link.
          </p>
          {err && <Err error={err} />}
          <button disabled={busy} className="btn primary fit">
            {busy ? "Calculando…" : "Simular investimento"}
            <ArrowRight size={16} />
          </button>
        </form>
      </section>
      {res.length > 1 && (
        <section className="panel prose">
          <h2>Aplicação do orçamento</h2>
          <p>Valor aplicado e saldo em reais por estratégia.</p>
          <div
            className="chart"
            role="img"
            aria-label="Comparação de investimento e saldo, detalhada nos cenários abaixo"
          >
            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                layout="vertical"
                data={res.map((s) => ({
                  name: strategies[s.strategy as Strategy],
                  Aplicado: s.spent,
                  Saldo: s.balance,
                }))}
              >
                <CartesianGrid horizontal={false} strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => number(v)} />
                <YAxis dataKey="name" type="category" width={112} />
                <Tooltip formatter={(v) => money(Number(v))} />
                <Bar dataKey="Aplicado" fill="#276953" stackId="total" />
                <Bar dataKey="Saldo" fill="#b9d89b" stackId="total" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}
      <div aria-live="polite" className="result-grid">
        {res.map((s) => (
          <Result key={s.id} s={s} />
        ))}
      </div>
    </>
  );
}
