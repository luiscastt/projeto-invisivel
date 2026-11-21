import {
  lazy,
  Suspense,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  LocateFixed,
  MapPin,
  Paperclip,
  Plus,
  Trash2,
} from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { api, errorText, post, useApi } from "./api";
import { useApp } from "./context";
import {
  categories,
  label,
  externalUrl,
  localDate,
  validCoordinates,
  type Category,
  type Duplicate,
  type IssueDetail,
  type Neighborhood,
  type ReportInput,
  type SourceInput,
} from "./models";
import { Busy, Err, LoginGate, PageTitle, Tag } from "./ui";
import TerritorySelect from "./TerritorySelect";
const TerritoryMap = lazy(() => import("./TerritoryMap"));
const steps = [
  "Localização",
  "Descrição",
  "Evidências",
  "Semelhanças",
  "Revisão",
];
const blankSource = (): SourceInput => ({
  title: "",
  url: "",
  publisher: "",
  source_type: "official",
  published_at: null,
});
export default function Report() {
  const { user, city, demo } = useApp();
  const [q] = useSearchParams(),
    issueId = q.get("problema");
  const detail = useApi<IssueDetail>(
    "/issues/" + encodeURIComponent(issueId || ""),
    !!issueId,
  );
  if (user.isLoading) return <Busy />;
  if (user.error) return <Err error={user.error} retry={user.refetch} />;
  if (!user.data) return <LoginGate action="enviar um relato" />;
  if (issueId && detail.isLoading) return <Busy />;
  if (issueId && detail.error)
    return <Err error={detail.error} retry={detail.refetch} />;
  return (
    <Wizard
      key={
        (detail.data?.id || city.code) + "-" + (detail.data?.is_demo ?? demo)
      }
      issue={detail.data}
    />
  );
}
function Wizard({ issue }: { issue?: IssueDetail }) {
  const app = useApp(),
    cache = useQueryClient();
  const city = issue
      ? {
          code: issue.municipality_code,
          state_code: issue.municipality_code.slice(0, 2),
          name: issue.municipality_name,
          state_abbreviation: issue.state_abbreviation,
          center: null,
        }
      : app.city,
    demo = issue?.is_demo ?? app.demo;
  const [step, setStep] = useState(0),
    [lat, setLat] = useState(issue?.latitude.toString() || ""),
    [lng, setLng] = useState(issue?.longitude.toString() || ""),
    [neighborhood, setNeighborhood] = useState(issue?.neighborhood || ""),
    [title, setTitle] = useState(issue?.title || ""),
    [description, setDescription] = useState(""),
    [category, setCategory] = useState<Category>(
      issue?.category || "infrastructure",
    ),
    [when, setWhen] = useState(""),
    [anonymous, setAnonymous] = useState(true),
    [sourceList, setSourceList] = useState<SourceInput[]>([]),
    [uploads, setUploads] = useState<{ id: string; caption: string }[]>([]),
    [file, setFile] = useState<File | null>(null),
    [caption, setCaption] = useState(""),
    [matches, setMatches] = useState<Duplicate[]>([]),
    [link, setLink] = useState<string | null>(issue?.id || null),
    [err, setErr] = useState(""),
    [busy, setBusy] = useState(false),
    [geoBusy, setGeoBusy] = useState(false),
    [territory, setTerritory] = useState(false),
    [received, setReceived] = useState("");
  const fileInput = useRef<HTMLInputElement>(null),
    locked = useRef(false),
    heading = useRef<HTMLHeadingElement>(null),
    mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    if (step > 0) heading.current?.focus();
  }, [step]);
  const ns = useApi<Neighborhood[]>(
    "/municipalities/" + city.code + "/neighborhoods",
  );
  const payload = (): ReportInput => ({
    title: title.trim(),
    description: description.trim(),
    category,
    state_code: city.state_code,
    municipality_code: city.code,
    neighborhood: neighborhood.trim(),
    latitude: Number(lat),
    longitude: Number(lng),
    occurrence_date: when || null,
    anonymous,
    evidence_ids: uploads.map((x) => x.id),
    sources: sourceList.map((s) => ({
      ...s,
      title: s.title.trim(),
      url: s.url.trim(),
      publisher: s.publisher.trim(),
    })),
    existing_issue_id: link,
    is_demo: demo,
  });
  async function task(fn: () => Promise<void>) {
    if (locked.current) return;
    locked.current = true;
    setBusy(true);
    setErr("");
    try {
      await fn();
    } catch (e) {
      setErr(errorText(e));
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  async function upload() {
    if (!file) throw Error("Selecione uma imagem.");
    if (
      !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
      file.size > 5 * 1024 * 1024
    )
      throw Error("Use uma imagem JPG, PNG ou WebP de até 5 MiB.");
    const form = new FormData();
    form.append("file", file);
    form.append("caption", caption.trim());
    const r = await api<{ id: string; caption: string }>("/uploads", {
      method: "POST",
      body: form,
    });
    setUploads((v) => [...v, r]);
    setFile(null);
    setCaption("");
    if (fileInput.current) fileInput.current.value = "";
  }
  async function next(e: FormEvent) {
    e.preventDefault();
    await task(async () => {
      if (step === 0 && !validCoordinates(lat, lng))
        throw Error(
          "Informe latitude e longitude válidas ou marque o ponto no mapa.",
        );
      if (
        step === 1 &&
        (title.trim().length < 8 || description.trim().length < 20)
      )
        throw Error(
          "Escreva um título com ao menos 8 caracteres e uma descrição com ao menos 20.",
        );
      if (step === 2) {
        if (file) throw Error("Anexe a imagem selecionada antes de continuar.");
        if (sourceList.some((s) => !s.title.trim() || !externalUrl(s.url)))
          throw Error(
            "Cada referência precisa de título, publicador e endereço HTTPS público.",
          );
        setMatches(
          await post<Duplicate[]>("/reports/check-duplicates", payload()),
        );
      }
      if (step === 4) {
        const r = await post<{ tracking_code: string }>("/reports", payload());
        setReceived(r.tracking_code);
        await cache.invalidateQueries({ queryKey: ["/me/reports"] });
        return;
      }
      setStep((v) => v + 1);
    });
  }
  function locate() {
    if (!navigator.geolocation) {
      setErr("Localização indisponível neste navegador.");
      return;
    }
    setGeoBusy(true);
    setErr("");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (mounted.current) {
          setLat(pos.coords.latitude.toFixed(6));
          setLng(pos.coords.longitude.toFixed(6));
          setGeoBusy(false);
        }
      },
      () => {
        if (mounted.current) {
          setErr(
            "Não foi possível obter a localização. Marque o mapa ou informe as coordenadas.",
          );
          setGeoBusy(false);
        }
      },
      { timeout: 12000 },
    );
  }
  const patch = (idx: number, values: Partial<SourceInput>) =>
    setSourceList((s) =>
      s.map((v, i) => (i === idx ? { ...v, ...values } : v)),
    );
  if (received)
    return (
      <section className="panel success">
        <CheckCircle2 />
        <h1>Relato recebido</h1>
        <p>
          Seu envio está na fila de moderação. Acompanhe a análise com o
          protocolo <strong>{received}</strong>.
        </p>
        <Link className="btn primary" to="/perfil">
          Acompanhar meus relatos <ArrowRight size={16} />
        </Link>
      </section>
    );
  return (
    <>
      <PageTitle
        title={issue ? "Complementar problema" : "Novo relato"}
        description="Documente uma situação de interesse coletivo no seu território."
      />
      {demo && <p className="notice">Este envio pertence à demonstração.</p>}
      <section className="panel wizard">
        <ol className="steps">
          {steps.map((s, i) => (
            <li
              className={i === step ? "current" : i < step ? "done" : ""}
              aria-current={i === step ? "step" : undefined}
              key={s}
            >
              <span>{i < step ? <Check size={12} /> : i + 1}</span>
              {s}
            </li>
          ))}
        </ol>
        <form onSubmit={next}>
          <div className="form-stack">
            <h2 ref={heading} tabIndex={-1}>
              {
                [
                  "Onde está o problema?",
                  "O que está acontecendo?",
                  "Há imagens ou referências?",
                  "É um problema já registrado?",
                  "Revise seu relato",
                ][step]
              }
            </h2>
            {step === 0 && (
              <>
                <div className="inline-between">
                  <strong>
                    <MapPin size={16} /> {city.name} · {city.state_abbreviation}
                  </strong>
                  {!issue && (
                    <button
                      type="button"
                      className="text-btn"
                      onClick={() => setTerritory(true)}
                    >
                      Trocar território
                    </button>
                  )}
                </div>
                <p>Marque o ponto no mapa ou digite as coordenadas.</p>
                <Suspense fallback={<Busy />}>
                  <TerritoryMap
                    city={city}
                    picked={
                      validCoordinates(lat, lng)
                        ? [Number(lng), Number(lat)]
                        : null
                    }
                    onPick={([x, y]) => {
                      setLat(y.toString());
                      setLng(x.toString());
                    }}
                  />
                </Suspense>
                <div className="fields">
                  <label>
                    Latitude
                    <input
                      required
                      type="number"
                      min="-34"
                      max="6"
                      step="any"
                      value={lat}
                      onChange={(e) => setLat(e.target.value)}
                    />
                  </label>
                  <label>
                    Longitude
                    <input
                      required
                      type="number"
                      min="-74"
                      max="-28"
                      step="any"
                      value={lng}
                      onChange={(e) => setLng(e.target.value)}
                    />
                  </label>
                </div>
                <button
                  className="btn secondary fit"
                  type="button"
                  disabled={geoBusy}
                  onClick={locate}
                >
                  <LocateFixed size={16} />
                  {geoBusy ? "Localizando…" : "Usar minha localização"}
                </button>
                <label>
                  Bairro (opcional)
                  <select
                    value={neighborhood}
                    onChange={(e) => setNeighborhood(e.target.value)}
                  >
                    <option value="">Sem bairro informado</option>
                    {ns.data?.map((n) => (
                      <option key={n.id} value={n.name}>
                        {n.name}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}
            {step === 1 && (
              <>
                <label>
                  Categoria
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as Category)}
                  >
                    {Object.entries(categories).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Título
                  <input
                    required
                    minLength={8}
                    maxLength={180}
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Resuma a situação em uma frase"
                  />
                </label>
                <label>
                  Descrição
                  <textarea
                    required
                    minLength={20}
                    maxLength={6000}
                    rows={5}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="O que você observou e como isso afeta o local?"
                  />
                </label>
                <label>
                  Data da ocorrência (opcional)
                  <input
                    type="date"
                    max={localDate()}
                    value={when}
                    onChange={(e) => setWhen(e.target.value)}
                  />
                </label>
              </>
            )}
            {step === 2 && (
              <>
                <p>
                  Esta etapa é opcional. Evite rostos, placas e dados pessoais
                  nas imagens.
                </p>
                <label>
                  Fotografia · JPG, PNG ou WebP, até 5 MiB
                  <input
                    type="file"
                    ref={fileInput}
                    accept="image/jpeg,image/png,image/webp"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                  />
                </label>
                <label>
                  Legenda da imagem
                  <input
                    maxLength={300}
                    value={caption}
                    onChange={(e) => setCaption(e.target.value)}
                  />
                </label>
                <button
                  type="button"
                  disabled={!file || busy || uploads.length >= 5}
                  className="btn secondary fit"
                  onClick={() => task(upload)}
                >
                  <Paperclip size={16} />
                  Anexar imagem
                </button>
                {uploads.map((x) => (
                  <div key={x.id} className="inline-between">
                    <span>{x.caption || "Imagem anexada"}</span>
                    <button
                      type="button"
                      className="icon-btn"
                      aria-label="Remover imagem"
                      onClick={() =>
                        setUploads((v) => v.filter((y) => y.id !== x.id))
                      }
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                ))}
                {sourceList.map((s, i) => (
                  <fieldset className="form-stack" key={i}>
                    <legend>Referência {i + 1}</legend>
                    <label>
                      Título da referência
                      <input
                        required
                        minLength={3}
                        maxLength={240}
                        value={s.title}
                        onChange={(e) => patch(i, { title: e.target.value })}
                      />
                    </label>
                    <label>
                      Endereço da referência
                      <input
                        type="url"
                        required
                        pattern="https://.+"
                        maxLength={2048}
                        placeholder="https://…"
                        value={s.url}
                        onChange={(e) => patch(i, { url: e.target.value })}
                      />
                    </label>
                    <div className="fields">
                      <label>
                        Publicador
                        <input
                          required
                          minLength={2}
                          maxLength={160}
                          value={s.publisher}
                          onChange={(e) =>
                            patch(i, { publisher: e.target.value })
                          }
                        />
                      </label>
                      <label>
                        Tipo
                        <select
                          value={s.source_type}
                          onChange={(e) =>
                            patch(i, {
                              source_type: e.target
                                .value as SourceInput["source_type"],
                            })
                          }
                        >
                          <option value="official">Oficial</option>
                          <option value="journalistic">Jornalística</option>
                          <option value="community">Comunitária</option>
                        </select>
                      </label>
                    </div>
                    <label>
                      Data de publicação
                      <input
                        type="date"
                        value={s.published_at || ""}
                        onChange={(e) =>
                          patch(i, { published_at: e.target.value || null })
                        }
                      />
                    </label>
                    <button
                      type="button"
                      className="text-btn"
                      onClick={() =>
                        setSourceList((v) => v.filter((_, idx) => idx !== i))
                      }
                    >
                      Remover referência
                    </button>
                  </fieldset>
                ))}
                <button
                  className="btn secondary fit"
                  type="button"
                  disabled={sourceList.length >= 5}
                  onClick={() => setSourceList((v) => [...v, blankSource()])}
                >
                  <Plus size={16} />
                  Adicionar referência
                </button>
              </>
            )}
            {step === 3 && (
              <>
                <p>
                  {matches.length || issue
                    ? "Escolha o registro relacionado ou indique que se trata de outro problema."
                    : "A busca não encontrou problemas semelhantes. Seu envio seguirá como novo registro."}
                </p>
                {issue && !matches.some((d) => d.issue.id === issue.id) && (
                  <label className="radio-row">
                    <input
                      type="radio"
                      checked={link === issue.id}
                      onChange={() => setLink(issue.id)}
                    />
                    {issue.title}
                  </label>
                )}
                {matches.map((d) => (
                  <label className="radio-row" key={d.issue.id}>
                    <input
                      type="radio"
                      checked={link === d.issue.id}
                      onChange={() => setLink(d.issue.id)}
                    />
                    <span>
                      <b>{d.issue.title}</b>
                      <small>
                        {d.distance_meters != null
                          ? Math.round(d.distance_meters) + " m · "
                          : ""}
                        {label(d.interpretation)} · {Math.round(d.score * 100)}%
                        de semelhança
                      </small>
                    </span>
                  </label>
                ))}
                <label className="radio-row">
                  <input
                    type="radio"
                    checked={!link}
                    onChange={() => setLink(null)}
                  />
                  É um problema diferente
                </label>
              </>
            )}
            {step === 4 && (
              <>
                <Tag>{categories[category]}</Tag>
                <h3>{title}</h3>
                <p className="pre">{description}</p>
                <dl className="details">
                  <dt>Local</dt>
                  <dd>
                    {[neighborhood, city.name].filter(Boolean).join(", ")} (
                    {lat}, {lng})
                  </dd>
                  <dt>Contribuição</dt>
                  <dd>
                    {link
                      ? "Complemento de registro existente"
                      : "Novo problema"}
                  </dd>
                  <dt>Material</dt>
                  <dd>
                    {uploads.length} imagem(ns) · {sourceList.length}{" "}
                    referência(s)
                  </dd>
                </dl>
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={anonymous}
                    onChange={(e) => setAnonymous(e.target.checked)}
                  />
                  Ocultar meu nome na publicação
                </label>
                <p>
                  Seu relato passa pela moderação antes de aparecer no mapa.
                </p>
              </>
            )}
            {err && <Err error={err} />}
            <div className="wizard-actions">
              {step > 0 && (
                <button
                  type="button"
                  className="btn secondary"
                  disabled={busy}
                  onClick={() => {
                    setErr("");
                    setStep(step - 1);
                  }}
                >
                  <ArrowLeft size={16} />
                  Voltar
                </button>
              )}
              <button
                type="submit"
                className="btn primary"
                disabled={busy || geoBusy}
              >
                {busy
                  ? "Aguarde…"
                  : step === 4
                    ? "Enviar para moderação"
                    : "Continuar"}
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </form>
      </section>
      {territory && <TerritorySelect close={() => setTerritory(false)} />}
    </>
  );
}
