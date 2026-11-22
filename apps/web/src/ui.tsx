import { Component, useEffect, useRef, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  Building2,
  Check,
  ChevronRight,
  CircleHelp,
  Droplets,
  GraduationCap,
  HeartPulse,
  Layers3,
  Leaf,
  LoaderCircle,
  MapPin,
  Plus,
  SearchX,
  TrainFront,
  X,
} from "lucide-react";
import {
  categories,
  date,
  label,
  type Issue,
  type Category,
  externalUrl,
} from "./models";
export const categoryIcons = {
  infrastructure: Building2,
  sanitation: Droplets,
  mobility: TrainFront,
  health: HeartPulse,
  education: GraduationCap,
  environment: Leaf,
};
export function Brand() {
  return (
    <Link to="/" aria-label="Invisivel, início" className="brand">
      <Layers3 strokeWidth={2.15} />
      <span>INVISIVEL</span>
    </Link>
  );
}
export function PageTitle({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-title">
      <div>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {children}
    </header>
  );
}
export function Err({
  error,
  retry,
}: {
  error: unknown;
  retry?: () => unknown;
}) {
  return (
    <div className="notice error" role="alert">
      <AlertCircle size={17} />
      <div>
        {error instanceof Error ? error.message : String(error)}{" "}
        {retry && (
          <button className="text-btn" onClick={retry}>
            Tentar novamente
          </button>
        )}
      </div>
    </div>
  );
}
export function Busy() {
  return (
    <div className="busy" role="status">
      <LoaderCircle size={19} /> Carregando…
    </div>
  );
}
export function Empty({
  title = "Nenhum dossiê publicado",
  text = "Nenhum dossiê publicado nesta base; isso não indica ausência de problemas no município.",
  action = true,
}: {
  title?: string;
  text?: string;
  action?: boolean;
}) {
  return (
    <div className="empty">
      <span>
        <SearchX size={23} />
      </span>
      <strong>{title}</strong>
      <p>{text}</p>
      {action && (
        <Link className="text-link" to="/relatar">
          Enviar um relato <ArrowRight size={15} />
        </Link>
      )}
    </div>
  );
}
export function Tag({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <span className={"tag " + tone}>{children}</span>;
}
export function CategoryMark({ category }: { category: Category }) {
  const Icon = categoryIcons[category] || CircleHelp;
  return (
    <span className={"cat-mark " + category}>
      <Icon size={18} />
    </span>
  );
}
export function IssueRow({ issue }: { issue: Issue }) {
  return (
    <Link className="issue-row" to={"/problemas/" + issue.id}>
      <CategoryMark category={issue.category} />
      <div>
        <small>
          {categories[issue.category]} · {label(issue.operational_status)}{" "}
          {issue.is_demo ? "· Demonstração" : ""}
        </small>
        <h3>{issue.title}</h3>
        <small>
          {issue.origin === "official" ? "Fonte oficial · Dossiê temático" : "Origem comunitária"}
          {issue.origin === "official" && <> · {issue.official_records_count ?? "—"} registros oficiais</>}
          {" · "}{issue.reports_count} relatos na plataforma
        </small>
        <p>
          <MapPin size={13} />
          {[issue.neighborhood, issue.municipality_name]
            .filter(Boolean)
            .join(", ")}{" "}
          · {date(issue.last_activity_at)}
        </p>
      </div>
      <ChevronRight size={17} className="push" />
    </Link>
  );
}
export function External({
  url,
  children,
}: {
  url: string;
  children: ReactNode;
}) {
  const href = externalUrl(url);
  return href ? (
    <a
      className="text-link"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
    >
      {children} ↗
    </a>
  ) : (
    <span>{children}</span>
  );
}
export function Dialog({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const d = ref.current;
    d?.showModal();
    return () => d?.close();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={close}
      onClick={(e) => {
        if (e.target === ref.current) close();
      }}
      aria-label={title}
    >
      <div className="dialog-body">
        <div className="section-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={close} aria-label="Fechar">
            <X size={19} />
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
}
export function LoginGate({ action }: { action: string }) {
  const here = useLocation();
  return (
    <div className="panel gate">
      <Check className="large-icon" />
      <h2>Entre para {action}</h2>
      <p>
        Sua conta permite acompanhar as contribuições enviadas ao observatório.
      </p>
      <Link
        className="btn primary"
        to={"/entrar?voltar=" + encodeURIComponent(here.pathname + here.search)}
      >
        Entrar na plataforma <ArrowRight size={16} />
      </Link>
    </div>
  );
}
export function ReportButton() {
  return (
    <Link className="btn primary" to="/relatar">
      <Plus size={17} /> Novo relato
    </Link>
  );
}
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: boolean }
> {
  state = { error: false };
  static getDerivedStateFromError() {
    return { error: true };
  }
  render() {
    return this.state.error ? (
      <main className="panel">
        <h1>Não foi possível abrir esta página</h1>
        <a href="/">Voltar ao painel</a>
      </main>
    ) : (
      this.props.children
    );
  }
}
