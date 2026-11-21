import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";
import { Empty, LoginGate } from "./ui";
afterEach(cleanup);
describe("participação", () => {
  it("oferece um primeiro relato em território vazio", () => {
    render(
      <MemoryRouter>
        <Empty />
      </MemoryRouter>,
    );
    expect(
      screen
        .getByRole("link", { name: "Enviar um relato" })
        .getAttribute("href"),
    ).toBe("/relatar");
  });
  it("mantém o vínculo com o problema após autenticação", () => {
    render(
      <MemoryRouter initialEntries={["/relatar?problema=abc"]}>
        <LoginGate action="complementar o problema" />
      </MemoryRouter>,
    );
    expect(
      screen
        .getByRole("link", { name: "Entrar na plataforma" })
        .getAttribute("href"),
    ).toBe("/entrar?voltar=%2Frelatar%3Fproblema%3Dabc");
  });
});
