import { describe, expect, it } from "vitest";
import {
  formatIndicator,
  safeReturn,
  validCoordinates,
  externalUrl,
} from "./models";
describe("escala, localização e navegação", () => {
  it("preserva a diferença entre zero medido e valor ausente", () => {
    expect(
      formatIndicator({ value: 0, quality: "official", unit: "pessoas" }),
    ).toBe("0 pessoas");
    expect(
      formatIndicator({ value: null, quality: "unavailable", unit: "%" }),
    ).toBe("Dado não disponível");
  });
  it("formata números conforme pt-BR e preserva a unidade", () => {
    expect(
      formatIndicator({ value: 98.34, quality: "official", unit: "%" }),
    ).toBe("98,34 %");
  });
  it("exige um ponto nos limites de entrada do território brasileiro", () => {
    expect(validCoordinates("-20.21", "-40.28")).toBe(true);
    for (const [lat, lng] of [
      ["", "-40"],
      ["-20", ""],
      ["90", "-40"],
      ["0", "0"],
      ["NaN", "-40"],
    ])
      expect(validCoordinates(lat, lng)).toBe(false);
  });
  it("aceita somente retorno para uma rota interna", () => {
    expect(safeReturn("/relatar?problema=123")).toBe("/relatar?problema=123");
    expect(safeReturn("//externo.test")).toBe("/");
    expect(safeReturn("/\\externo.test")).toBe("/");
    expect(safeReturn("https://externo.test")).toBe("/");
  });
  it("mantém referências navegáveis em HTTP(S)", () => {
    expect(externalUrl("javascript:alert(1)")).toBeUndefined();
    expect(externalUrl("https://www.ibge.gov.br")).toBe(
      "https://www.ibge.gov.br/",
    );
  });
});
