import { useState } from "react";
import { MapPin, Search } from "lucide-react";
import { useApp } from "./context";
import { useApi } from "./api";
import type { City } from "./models";
import { Busy, Dialog, Err } from "./ui";
export default function TerritorySelect({ close }: { close: () => void }) {
  const { city, setCity, states } = useApp();
  const [state, setState] = useState(city.state_code),
    [search, setSearch] = useState(""),
    [selected, setSelected] = useState<City | null>(city);
  const list = useApi<City[]>("/states/" + state + "/municipalities");
  const norm = (s: string) =>
    s
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  return (
    <Dialog title="Selecionar território" close={close}>
      <div className="form-stack">
        <label>
          Estado
          <select
            value={state}
            onChange={(e) => {
              setState(e.target.value);
              setSelected(null);
              setSearch("");
            }}
          >
            {states.data?.map((s) => (
              <option key={s.code} value={s.code}>
                {s.name} ({s.abbreviation})
              </option>
            ))}
          </select>
        </label>
        {states.error && <Err error={states.error} retry={states.refetch} />}
        <label>
          Pesquisar município
          <div className="input-icon">
            <Search />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Nome do município"
            />
          </div>
        </label>
        {list.isLoading ? (
          <Busy />
        ) : list.error ? (
          <Err error={list.error} retry={list.refetch} />
        ) : (
          <div className="city-list">
            {(list.data || [])
              .filter((c) => norm(c.name).includes(norm(search)))
              .map((c) => (
                <label className="radio-row" key={c.code}>
                  <input
                    type="radio"
                    name="municipio"
                    checked={selected?.code === c.code}
                    onChange={() => setSelected(c)}
                  />
                  <MapPin size={15} />
                  {c.name}
                </label>
              ))}
            {!list.data?.some((c) => norm(c.name).includes(norm(search))) && (
              <p>Nenhum município encontrado.</p>
            )}
          </div>
        )}
        <button
          className="btn primary"
          disabled={!selected}
          onClick={() => {
            if (selected) {
              setCity(selected);
              close();
            }
          }}
        >
          Aplicar território
        </button>
      </div>
    </Dialog>
  );
}
