export const categories = {
  infrastructure: "Infraestrutura",
  sanitation: "Saneamento",
  mobility: "Mobilidade",
  education: "Educação",
  health: "Saúde",
  environment: "Meio ambiente",
} as const;
export const statuses = {
  reported: "Relatado",
  corroborated: "Corroborado",
  in_progress: "Em andamento",
  declared_resolved: "Resolução declarada",
  verified_resolved: "Resolução verificada",
  contested: "Contestado",
  open: "Em aberto",
  unresolved: "Não resolvido",
  resolved: "Resolvido",
  pending: "Em análise",
  approved: "Aprovado",
  rejected: "Rejeitado",
  clarification_requested: "Esclarecimento solicitado",
  community: "Relato comunitário",
  official: "Informação oficial",
  documented: "Documentado",
  unverified: "Sem verificação",
  community_report: "Relato comunitário",
  community_reported: "Relato comunitário",
  documentary: "Evidência documental",
  under_review: "Em análise",
  community_evidence: "Evidência comunitária",
  descriptive_complement: "Complemento descritivo",
  repeated_information: "Informação repetida",
  initial_report: "Relato inicial",
  initial: "Relato inicial",
  new_report: "Novo relato",
  strong: "Semelhança forte",
  review: "Correspondência a revisar",
  distinct: "Possível problema distinto",
  location_boundary_unavailable: "Limite municipal indisponível",
  possible_personal_data: "Possíveis dados pessoais",
  sensitive_content: "Conteúdo sensível",
  possible_spam: "Possível envio repetitivo",
  published: "Publicado",
  contribution_approved: "Contribuição aprovada",
  status_changed: "Situação alterada",
  merged: "Dossiês unificados",
  restored: "Versão restaurada",
  report_rejected: "Relato rejeitado",
};
export type Category = keyof typeof categories;
export type User = {
  id: string;
  email: string;
  display_name: string;
  role: "citizen" | "admin";
};
export type State = { code: string; name: string; abbreviation: string };
export type City = {
  code: string;
  name: string;
  state_code: string;
  state_abbreviation: string;
  center: [number, number] | null;
};
export type Neighborhood = {
  id: string;
  name: string;
  geometry_status: string;
  source_url: string | null;
};
export type Indicator = {
  id: string;
  name: string;
  sector: string;
  value: number | null;
  unit: string;
  year: string | null;
  source_name: string;
  source_url: string;
  granularity: string;
  quality: string;
  fetched_at: string | null;
};
export type Summary = {
  municipality: City;
  counts: {
    total: number;
    unresolved: number;
    resolved: number;
    reports: number;
    evidence: number;
  };
  indicators: Indicator[];
  coverage: { neighborhoods: number; boundaries_available: boolean };
  assessment: { score: number | null; reason: string };
};
export type Evidence = {
  id: string;
  url: string;
  caption: string;
  verification_status: string;
};
export type SourceInput = {
  title: string;
  url: string;
  publisher: string;
  source_type: "official" | "journalistic" | "community";
  published_at: string | null;
};
export type Source = SourceInput & { id: string; checked_at: string | null };
export type Vote = "RESOLVED" | "UNRESOLVED";
export type Votes = {
  resolved: number;
  unresolved: number;
  my_vote: Vote | null;
};
export type Issue = {
  id: string;
  title: string;
  summary: string;
  category: Category;
  municipality_code: string;
  municipality_name: string;
  state_abbreviation: string;
  neighborhood: string;
  latitude: number;
  longitude: number;
  verification_status: string;
  operational_status: string;
  first_reported_at: string;
  last_activity_at: string;
  is_demo: boolean;
  reports_count: number;
  evidence_count: number;
  votes: Votes;
  priority: { score: number | null; reason: string };
  version: number;
};
export type IssueDetail = Issue & {
  reports: {
    id: string;
    description: string;
    display_name: string;
    created_at: string;
    contribution_type: string;
  }[];
  sources: Source[];
  updates: {
    id: string;
    version: number;
    update_type: string;
    description: string;
    created_at: string;
    reason: string;
  }[];
  evidence: Evidence[];
};
export type IssuePage = {
  items: Issue[];
  total: number;
  page: number;
  page_size: number;
};
export type ReportInput = {
  title: string;
  description: string;
  category: Category;
  state_code: string;
  municipality_code: string;
  neighborhood: string;
  latitude: number;
  longitude: number;
  occurrence_date: string | null;
  anonymous: boolean;
  evidence_ids: string[];
  sources: SourceInput[];
  existing_issue_id: string | null;
  is_demo: boolean;
};
export type Duplicate = {
  issue: Issue;
  score: number;
  distance_meters: number | null;
  interpretation: string;
};
export type ModerationItem = {
  id: string;
  tracking_code: string;
  title: string;
  description: string;
  category: Category;
  municipality_code: string;
  municipality_name: string;
  neighborhood: string;
  latitude: number;
  longitude: number;
  created_at: string;
  moderation_status: string;
  flags: string[];
  is_demo: boolean;
  existing_issue_id: string | null;
  evidence: Evidence[];
  sources: Source[];
  duplicates: Duplicate[];
  clarifications?: {description: string; created_at: string}[];
};
export type Intervention = {
  id: string;
  name: string;
  category: Category;
  unit: string;
  default_unit_cost: number;
  assumption: string;
};
export type Simulation = {
  id: string;
  demo?: boolean;
  municipality_code: string;
  category: Category;
  budget: number;
  unit_cost: number;
  strategy: string;
  capacity: number;
  selected_count: number;
  spent: number;
  balance: number;
  issue_ids: string[];
  issues: Issue[];
  disclaimer: string;
  assumptions: string[];
  created_at: string;
};
export type DataSource = {
  stale?: boolean;
  id: string;
  name: string;
  organization: string;
  url: string;
  description: string;
  status: string;
  last_synced: string | null;
  reference: string | null;
  granularity: string | null;
  records: number | null;
  notes: string | null;
};
export const number = (value: number) =>
  new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 }).format(value);
export const money = (value: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    value,
  );
export function date(value: string | null | undefined) {
  if (!value) return "Sem data";
  const d = new Date(value.length === 10 ? value + "T12:00:00" : value);
  return Number.isNaN(d.valueOf())
    ? value
    : new Intl.DateTimeFormat("pt-BR").format(d);
}
export const label = (s: string) =>
  statuses[s as keyof typeof statuses] ||
  s?.replaceAll("_", " ") ||
  "Sem classificação";
export function externalUrl(value: string) {
  try {
    const u = new URL(value);
    return ["https:", "http:"].includes(u.protocol) ? u.href : undefined;
  } catch {
    return undefined;
  }
}
export function formatIndicator(
  i: Pick<Indicator, "value" | "quality" | "unit">,
) {
  return i.value == null || i.quality === "unavailable"
    ? "Dado não disponível"
    : number(i.value) + " " + i.unit;
}
export function validCoordinates(lat: string, lng: string) {
  return (
    lat.trim() !== "" &&
    lng.trim() !== "" &&
    Number.isFinite(Number(lat)) &&
    Number.isFinite(Number(lng)) &&
    Number(lat) >= -34 &&
    Number(lat) <= 6 &&
    Number(lng) >= -74 &&
    Number(lng) <= -28
  );
}
export function localDate() {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 10);
}
export function safeReturn(path: string | null) {
  return path?.startsWith("/") && !path.startsWith("//") && !path.includes("\\")
    ? path
    : "/";
}
