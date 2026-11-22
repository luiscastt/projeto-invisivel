import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Detail from "./Detail";
import Report from "./Report";
import Dashboard from "./Dashboard";
import Simulator from "./Simulator";
import Explore from "./Explore";
import { IssueRow } from "./ui";
import { hasIssuePoint, type Issue, label } from "./models";
const { useApiMock, mapMock, cityMock } = vi.hoisted(() => ({ useApiMock: vi.fn(), mapMock: vi.fn(), cityMock: {code: "3205002", name: "Serra", state_abbreviation: "ES", center: null} }));
vi.mock("./api", async () => ({
  ...(await vi.importActual<typeof import("./api")>("./api")),
  useApi: useApiMock,
}));
vi.mock("./TerritoryMap", () => ({default: (props: unknown) => {mapMock(props); return <div>Mapa territorial</div>;}}));
vi.mock("./context", () => ({ useApp: () => ({
  user: {data: {id: "citizen", role: "citizen"}, isLoading: false},
  city: cityMock, demo: false,
})}));
const official = {
  id: "official-1", title: "Saneamento · órgão público · 2025", category: "sanitation",
  municipality_code: "3205002", municipality_name: "Serra", state_abbreviation: "ES",
  neighborhood: "", latitude: null, longitude: null, origin: "official",
  location_precision: "municipality", verification_status: "official_registered",
  operational_status: "not_assessed", official_records_count: 12,
  reports_count: 0, evidence_count: 0, last_activity_at: "2025-06-01", is_demo: false,
} as Issue;
afterEach(cleanup);
beforeEach(() => { Object.assign(cityMock, {code: "3205002", name: "Serra", state_abbreviation: "ES"}); useApiMock.mockClear(); mapMock.mockClear(); useApiMock.mockImplementation((path: string) => ({data:
  path.includes("/summary") ? {
    counts: {total: 1, official_records: 12, official_issues: 1, community_issues: 0, not_assessed: 1, unresolved: 0, resolved: 0, reports: 0, evidence: 0},
    indicators: [], assessment: {reason: "Sem avaliação"},
  } : path.includes("/issues?") ? {items: [official], total: 1, page: 1, page_size: 20} : [],
})); });
it("counts source records separately from dossiers and citizen reports on the dashboard", async () => {
  render(<MemoryRouter><Dashboard/></MemoryRouter>);
  expect(screen.getByText("Registros oficiais")).toBeTruthy();
  expect(screen.getByText("12")).toBeTruthy();
  expect(screen.getByText("Dossiês acompanhados")).toBeTruthy();
  expect(screen.getByText("Relatos na plataforma")).toBeTruthy();
  expect(screen.getByText("Resolução verificada")).toBeTruthy();
  expect(screen.queryByText("Em aberto")).toBeNull();
  expect(screen.getByText(/agrupamentos temáticos.*ocorrências físicas/i)).toBeTruthy();
});
it("marks an official dossier and its source count without claiming verified allegations", () => {
  render(<MemoryRouter><IssueRow issue={official}/></MemoryRouter>);
  expect(screen.getByText(/Fonte oficial/)).toBeTruthy();
  expect(screen.getByText(/12 registros oficiais/)).toBeTruthy();
  expect(screen.getByText(/Não avaliado/)).toBeTruthy();
});
it("offers origin filtering to keep imported complaints in the main list", () => {
  render(<MemoryRouter><Explore/></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("Origem"), {target: {value: "official"}});
  expect(useApiMock.mock.calls.some(([path]) => path.includes("origin=official"))).toBe(true);
  expect(screen.getByText(official.title)).toBeTruthy();
});
it("never treats municipality-only records or missing coordinates as map points", () => {
  expect(hasIssuePoint(official)).toBe(false);
  expect(hasIssuePoint({...official, latitude: -20.2, longitude: -40.2})).toBe(false);
  expect(hasIssuePoint({...official, location_precision: "point", latitude: null, longitude: null})).toBe(false);
  expect(hasIssuePoint({...official, location_precision: "point", latitude: -20.2, longitude: -40.2})).toBe(true);
});
it("explains that an empty local base is not the absence of municipal problems", () => {
  useApiMock.mockImplementation(() => ({data: {items: [], total: 0, page_size: 20}}));
  render(<MemoryRouter><Explore/></MemoryRouter>);
  expect(screen.getByText("Nenhum dossiê publicado nesta base; isso não indica ausência de problemas no município.")).toBeTruthy();
});

const detail = {...official, summary: "Manifestações recebidas na fonte oficial.", first_reported_at: "2025-01-01", reports: [], evidence: [], sources: [], updates: [], priority: {score: null, reason: "Não avaliado"}, votes: {resolved: 0, unresolved: 0, my_vote: null}, official_records_total: 12, official_records: [{id: "record-1", subject: "Saneamento", agency: "Órgão responsável", year: 2025, manifestation_type: "Reclamação", processing_status: "Encerrada", recorded_at: "2025-01-01", source_url: "https://example.org/oficial", municipality_code: "3205002"}]};
it("shows source metadata and processing status separately from resolution without a detail marker", async () => {
  useApiMock.mockImplementation((path: string) => ({data: path.endsWith("/indicators") ? [] : detail}));
  render(<MemoryRouter><QueryClientProvider client={new QueryClient()}><Detail/></QueryClientProvider></MemoryRouter>);
  expect(screen.getByText("Órgão responsável")).toBeTruthy();
  expect(screen.getByText("Encerrada")).toBeTruthy();
  expect(screen.getByText("Município informado pela fonte; endereço não disponível. Encerramento da manifestação não comprova solução.")).toBeTruthy();
  expect(screen.getByRole("link", {name: /Consultar fonte original/}).getAttribute("href")).toBe("https://example.org/oficial");
  expect(screen.getByText(/Exibindo 1 de 12 registros/)).toBeTruthy();
  await screen.findByText("Mapa territorial");
  expect(mapMock.mock.calls.at(-1)?.[0].picked).toBeNull();
});
it("starts a citizen complement with blank coordinates for an unlocated official dossier", async () => {
  useApiMock.mockImplementation((path: string) => ({data: path.includes("neighborhoods") ? [] : detail}));
  render(<MemoryRouter initialEntries={["/relatar?problema=official-1"]}><QueryClientProvider client={new QueryClient()}><Report/></QueryClientProvider></MemoryRouter>);
  expect((screen.getByLabelText("Latitude") as HTMLInputElement).value).toBe("");
  expect((screen.getByLabelText("Longitude") as HTMLInputElement).value).toBe("");
});

it("explains when municipal thematic dossiers are excluded from physical intervention costing", () => {
  useApiMock.mockImplementation(() => ({data: {id: "simulation-1", municipality_code: "3205002", category: "sanitation", budget: 10000, unit_cost: 1000, strategy: "priority", capacity: 10, selected_count: 0, spent: 0, balance: 10000, issues: [], assumptions: [], disclaimer: "Simulação hipotética", excluded_official_dossiers: 3}}));
  render(<MemoryRouter initialEntries={["/simulador/simulation-1"]}><Routes><Route path="/simulador/:id" element={<Simulator/>}/></Routes></MemoryRouter>);
  expect(screen.getByText(/3 dossiês oficiais.*excluídos.*custo por intervenção física/)).toBeTruthy();
});

it("states the limited Espírito Santo source scope on the non-demo dashboard", () => {
  render(<MemoryRouter><Dashboard/></MemoryRouter>);
  expect(screen.getByText(/Ouvidoria estadual do Espírito Santo · 2025–2026/)).toBeTruthy();
  expect(screen.getByText(/não inclui todas as manifestações nem todos os canais municipais e federais/)).toBeTruthy();
});
it("explains an archived source dossier without inferring resolution", () => {
  useApiMock.mockImplementation((path: string) => ({data: path.endsWith("/indicators") ? [] : {...detail, operational_status: "source_removed", official_records: [], official_records_total: 0}}));
  render(<MemoryRouter><QueryClientProvider client={new QueryClient()}><Detail/></QueryClientProvider></MemoryRouter>);
  expect(label("source_removed")).toBe("Arquivado por atualização da fonte");
  expect(screen.getByText(/não constam no recorte atual da fonte importada/)).toBeTruthy();
  expect(screen.getByText(/isso não comprova que o problema foi resolvido/)).toBeTruthy();
});

it("states that municipalities outside the initial source scope have no official coverage", () => {
  Object.assign(cityMock, {code: "3550308", name: "São Paulo", state_abbreviation: "SP"});
  render(<MemoryRouter><Dashboard/></MemoryRouter>);
  expect(screen.getByText(/não cobre este município; um resultado vazio não indica ausência de problemas/)).toBeTruthy();
});
