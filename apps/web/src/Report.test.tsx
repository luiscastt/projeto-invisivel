import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Report from "./Report";
import type { ReportInput } from "./models";
const { postMock } = vi.hoisted(() => ({ postMock: vi.fn() }));
vi.mock("./api", async () => ({
  ...(await vi.importActual<typeof import("./api")>("./api")),
  useApi: (path: string) => ({
    data: path.includes("neighborhoods") ? [] : undefined,
  }),
  post: postMock,
}));
vi.mock("./TerritoryMap", () => ({
  default: () => <div>Mapa territorial</div>,
}));
vi.mock("./context", () => ({
  useApp: () => ({
    user: { data: { id: "user", role: "citizen" }, isLoading: false },
    city: {
      code: "3205002",
      name: "Serra",
      state_code: "32",
      state_abbreviation: "ES",
      center: null,
    },
    demo: false,
  }),
}));
afterEach(cleanup);
beforeEach(() => {
  postMock.mockReset();
});
it("revisa correspondência sugerida e mantém o vínculo escolhido no envio pendente", async () => {
  postMock.mockImplementation(async (path: string) =>
    path.endsWith("check-duplicates")
      ? [
          {
            issue: { id: "similar", title: "Iluminação na praça" },
            distance_meters: 100,
            score: 0.9,
            interpretation: "strong",
          },
        ]
      : { id: "r", tracking_code: "INV-123", moderation_status: "pending" },
  );
  render(
    <MemoryRouter>
      <QueryClientProvider client={new QueryClient()}>
        <Report />
      </QueryClientProvider>
    </MemoryRouter>,
  );
  fireEvent.change(screen.getByLabelText("Latitude"), {
    target: { value: "-20.2" },
  });
  fireEvent.change(screen.getByLabelText("Longitude"), {
    target: { value: "-40.27" },
  });
  const next = () =>
    fireEvent.click(screen.getByRole("button", { name: "Continuar" }));
  next();
  fireEvent.change(await screen.findByLabelText("Título"), {
    target: { value: "Iluminação na praça" },
  });
  fireEvent.change(screen.getByLabelText("Descrição"), {
    target: { value: "Relato de teste descrevendo a iluminação da praça." },
  });
  next();
  await screen.findByText("Há imagens ou referências?");
  next();
  fireEvent.click(
    await screen.findByRole("radio", { name: /Iluminação na praça/ }),
  );
  next();
  await screen.findByText("Revise seu relato");
  fireEvent.click(
    screen.getByRole("button", { name: "Enviar para moderação" }),
  );
  await screen.findByText("INV-123");
  const submission = postMock.mock.calls.find(
    (c) => c[0] === "/reports",
  )?.[1] as ReportInput;
  expect(submission).toMatchObject({
    existing_issue_id: "similar",
    is_demo: false,
    anonymous: true,
    state_code: "32",
    municipality_code: "3205002",
    longitude: -40.27,
    evidence_ids: [],
    sources: [],
  });
  expect(postMock.mock.calls.map((c) => c[0])).toEqual([
    "/reports/check-duplicates",
    "/reports",
  ]);
});
