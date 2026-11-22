import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, expect, it, vi } from "vitest";
import TerritoryMap from "./TerritoryMap";
import type { Issue } from "./models";
vi.mock("maplibre-gl", () => ({ Map: class {constructor() { throw new Error("WebGL unavailable"); }} }));
vi.mock("./api", async () => ({
  ...(await vi.importActual<typeof import("./api")>("./api")),
  api: async (path: string) => path.endsWith("/geometry") ? {type: "Feature", properties: {}, geometry: {type: "Polygon", coordinates: [[[-40.4, -20.3], [-40.1, -20.3], [-40.1, -20], [-40.4, -20.3]]]}} : {type: "FeatureCollection", features: []},
}));
afterEach(cleanup);
it("keeps unlocated and municipality-only official records out of fallback markers", async () => {
  const base = {id: "municipality-only", title: "Dossiê municipal", latitude: -20.2, longitude: -40.2, location_precision: "municipality", origin: "official"} as Issue;
  const issues = [base, {...base, id: "missing", title: "Sem coordenadas", latitude: null, longitude: null}, {...base, id: "community", title: "Ponto comunitário", origin: "community", location_precision: "point"}] as Issue[];
  const {container} = render(<MemoryRouter><QueryClientProvider client={new QueryClient({defaultOptions: {queries: {retry: false}}})}><TerritoryMap city={{code: "3205002", name: "Serra", state_code: "32", state_abbreviation: "ES", center: [-40.3, -20.2]}} issues={issues}/></QueryClientProvider></MemoryRouter>);
  await screen.findByRole("link", {name: "Ponto comunitário"});
  expect(screen.queryByRole("link", {name: "Dossiê municipal"})).toBeNull();
  expect(screen.queryByRole("link", {name: "Sem coordenadas"})).toBeNull();
  expect(container.querySelectorAll(".map-fallback circle").length).toBe(1);
  expect(screen.getByText(/2 dossiê\(s\) com localização apenas municipal/)).toBeTruthy();
});
