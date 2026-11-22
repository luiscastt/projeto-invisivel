import { useEffect, useMemo, useRef, useState } from "react";
import type {
  Feature,
  FeatureCollection,
  Geometry,
  GeoJsonProperties,
  Position,
} from "geojson";
import type { Map as MapInstance, GeoJSONSource } from "maplibre-gl";
import { Crosshair, Layers3, MapPin } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "./api";
import { hasIssuePoint, type City, type Issue } from "./models";
import "maplibre-gl/dist/maplibre-gl.css";
type Shape = Feature | FeatureCollection;
type Point = [number, number];
type Props = {
  city: City;
  issues?: Issue[];
  picked?: Point | null;
  onPick?: (point: Point) => void;
};
const empty: FeatureCollection = { type: "FeatureCollection", features: [] };
function shapes(shape?: Shape | null) {
  return shape?.type === "FeatureCollection"
    ? shape.features
    : shape
      ? [shape]
      : [];
}
function rings(g: Geometry): Position[][] {
  switch (g.type) {
    case "Polygon":
      return g.coordinates;
    case "MultiPolygon":
      return g.coordinates.flat();
    case "GeometryCollection":
      return g.geometries.flatMap(rings);
    default:
      return [];
  }
}
function pointsOf(shape?: Shape | null) {
  return shapes(shape)
    .flatMap((f) => rings(f.geometry))
    .flat();
}
function bounds(coords: Position[]) {
  if (!coords.length) return null;
  const b: [Point, Point] = [
    [Infinity, Infinity],
    [-Infinity, -Infinity],
  ];
  for (const [x, y] of coords) {
    b[0][0] = Math.min(x, b[0][0]);
    b[0][1] = Math.min(y, b[0][1]);
    b[1][0] = Math.max(x, b[1][0]);
    b[1][1] = Math.max(y, b[1][1]);
  }
  return b;
}
function point(coordinates: Point, properties: GeoJsonProperties): Feature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates },
    properties,
  };
}
function applyFit(
  map: MapInstance,
  shape: Shape | null | undefined,
  city: City,
  issues: Issue[],
  picked?: Point | null,
) {
  const located = issues.filter(hasIssuePoint);
  if (picked && located.length === 1) {
    map.jumpTo({ center: picked, zoom: 14 });
    return;
  }
  const b = bounds(pointsOf(shape));
  if (b && b[0][0] !== b[1][0])
    map.fitBounds(b, { padding: 28, duration: 0, maxZoom: 15 });
  else if (city.center) map.jumpTo({ center: city.center, zoom: 11 });
  else if (located.length || picked)
    map.jumpTo({
      center: picked || [located[0].longitude, located[0].latitude],
      zoom: 12,
    });
  else map.jumpTo({ center: [-52, -14], zoom: 2.7 });
}
export default function TerritoryMap({
  city,
  issues = [],
  picked,
  onPick,
}: Props) {
  const pointIssues = useMemo(() => issues.filter(hasIssuePoint), [issues]);
  const unlocatedCount = issues.length - pointIssues.length;
  const navigate = useNavigate(),
    element = useRef<HTMLDivElement>(null),
    mapRef = useRef<MapInstance | null>(null);
  const [layers, setLayers] = useState(false),
    [showAreas, setShowAreas] = useState(true),
    [showIssues, setShowIssues] = useState(true),
    [showFacilities, setShowFacilities] = useState(true);
  const [failed, setFailed] = useState(false),
    [loaded, setLoaded] = useState(false),
    [tilesFailed, setTilesFailed] = useState(false);
  const geometry = useQuery({
    queryKey: ["geometry", city.code],
    queryFn: async () => {
      try {
        return await api<Shape>("/territories/" + city.code + "/geometry");
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) return null;
        throw e;
      }
    },
  });
  const areasGeometry = useQuery({
    queryKey: ["neighborhood-geometries", city.code],
    queryFn: () =>
      api<FeatureCollection>(
        "/territories/" + city.code + "/neighborhood-geometries",
      ),
  });
  const officialPoints = useQuery({queryKey:["official-facilities",city.code],queryFn:()=>api<FeatureCollection>(`/territories/${city.code}/facilities`)});
  const propsRef = useRef({
    onPick,
    navigate,
    city,
    issues,
    picked,
    shape: geometry.data,
  });
  propsRef.current = {
    onPick,
    navigate,
    city,
    issues,
    picked,
    shape: geometry.data,
  };
  useEffect(() => {
    let cancelled = false;
    let resize: ResizeObserver | undefined;
    let instance: MapInstance | undefined;
    import("maplibre-gl")
      .then(({ Map, NavigationControl, AttributionControl, Popup }) => {
        if (cancelled || !element.current) return;
        instance = new Map({
          container: element.current,
          center: [-52, -14],
          zoom: 2.7,
          attributionControl: false,
          scrollZoom: false,
          style: {
            version: 8,
            sources: {
              osm: {
                type: "raster",
                tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
                tileSize: 256,
                attribution:
                  '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>',
              },
            },
            layers: [
              {
                id: "paper",
                type: "background",
                paint: { "background-color": "#e9eee7" },
              },
              {
                id: "cartography",
                type: "raster",
                source: "osm",
                paint: { "raster-opacity": 0.66, "raster-saturation": -0.8 },
              },
            ],
          },
        });
        const map = instance;
        mapRef.current = map;
        map.addControl(
          new NavigationControl({ showCompass: false }),
          "top-right",
        );
        map.addControl(
          new AttributionControl({ compact: false }),
          "bottom-right",
        );
        map.on("error", (event) => {
          if (
            (event as { sourceId?: string }).sourceId === "osm" ||
            /tile|fetch|network/i.test(event.error.message)
          )
            setTilesFailed(true);
        });
        map.once("style.load", () => {
          if (cancelled) return;
          for (const name of [
            "outline",
            "neighborhoods",
            "official-facilities",
            "issues",
            "selection",
          ])
            map.addSource(name, { type: "geojson", data: empty });
          map.addLayer({
            id: "municipal-fill",
            type: "fill",
            source: "outline",
            filter: ["==", "$type", "Polygon"],
            paint: { "fill-color": "#71a887", "fill-opacity": 0.17 },
          });
          map.addLayer({
            id: "neighborhood-boundaries",
            type: "line",
            source: "neighborhoods",
            paint: {
              "line-color": "#849b82",
              "line-width": 0.8,
              "line-opacity": 0.72,
            },
          });
          map.addLayer({
            id: "municipal-border",
            type: "line",
            source: "outline",
            filter: ["==", "$type", "Polygon"],
            paint: {
              "line-color": "#49876e",
              "line-width": 2.2,
              "line-dasharray": [3, 1],
            },
          });
          map.addLayer({
            id: "facilities",
            type: "circle",
            source: "official-facilities",
            paint: {
              "circle-color": [
                "match",
                ["coalesce", ["get", "category"], ["get", "sector"], ""],
                "health",
                "#aa5275",
                "education",
                "#9c681b",
                "#66748c",
              ],
              "circle-radius": 5,
              "circle-stroke-width": 1.5,
              "circle-stroke-color": "#ffffff",
            },
          });
          map.addLayer({
            id: "issue-points",
            type: "circle",
            source: "issues",
            paint: {
              "circle-color": [
                "match",
                ["get", "category"],
                "infrastructure",
                "#b96c30",
                "sanitation",
                "#26839c",
                "mobility",
                "#735eac",
                "health",
                "#aa5275",
                "education",
                "#9c681b",
                "#46815b",
              ],
              "circle-radius": 7,
              "circle-stroke-color": "#ffffff",
              "circle-stroke-width": 2.5,
            },
          });
          map.addLayer({
            id: "selected-point",
            type: "circle",
            source: "selection",
            paint: {
              "circle-color": "#123e36",
              "circle-radius": 9,
              "circle-stroke-width": 3,
              "circle-stroke-color": "#d0eb87",
            },
          });
          setLoaded(true);
        });
        map.on("click", (e) => {
          const latest = propsRef.current;
          if (latest.onPick) {
            latest.onPick([+e.lngLat.lng.toFixed(6), +e.lngLat.lat.toFixed(6)]);
            return;
          }
          if (map.getLayer("issue-points")) {
            const hit = map.queryRenderedFeatures(e.point, {
              layers: ["issue-points"],
            })[0];
            if (hit?.properties?.id)
              {latest.navigate("/problemas/" + hit.properties.id);return;}
          }
          if(map.getLayer("facilities")){
            const hit=map.queryRenderedFeatures(e.point,{layers:["facilities"]})[0];
            if(hit&&hit.geometry.type==='Point'){
              const text=(hit.properties?.kind==='work'?'Obrasgov':hit.properties?.category==='health'?'CNES':'Escola estadual')+' · '+String(hit.properties?.name||'Registro oficial');
              new Popup().setLngLat(hit.geometry.coordinates as Point).setText(text).addTo(map);
            }
          }
        });
        resize = new ResizeObserver(() => map.resize());
        resize.observe(element.current);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
      resize?.disconnect();
      instance?.remove();
      mapRef.current = null;
    };
  }, []);
  useEffect(() => {
    const m = mapRef.current;
    if (!loaded || !m) return;
    (m.getSource("official-facilities") as GeoJSONSource).setData(officialPoints.data || empty);
  },[loaded,officialPoints.data]);
  useEffect(() => {
    const m = mapRef.current;
    if (!loaded || !m) return;
    (m.getSource("outline") as GeoJSONSource).setData(geometry.data || empty);
    applyFit(
      m,
      geometry.data,
      city,
      propsRef.current.issues,
      propsRef.current.picked,
    );
  }, [loaded, geometry.data, city.code, city.center]);
  useEffect(() => {
    const m = mapRef.current;
    if (loaded && m)
      (m.getSource("issues") as GeoJSONSource).setData({
        type: "FeatureCollection",
        features: pointIssues
          .map((i) =>
            point([i.longitude, i.latitude], {
              id: i.id,
              category: i.category,
            }),
          ),
      });
  }, [loaded, pointIssues]);
  useEffect(() => {
    const m = mapRef.current;
    if (loaded && m)
      (m.getSource("selection") as GeoJSONSource).setData(
        picked ? point(picked, {}) : empty,
      );
  }, [loaded, picked]);
  useEffect(() => {
    const m = mapRef.current;
    if (!loaded || !m) return;
    (m.getSource("neighborhoods") as GeoJSONSource).setData(
      areasGeometry.data || empty,
    );
    for (const [id, visible] of [
      ["neighborhood-boundaries", showAreas],
      ["issue-points", showIssues],
      ["facilities", showFacilities],
    ] as const)
      m.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
  }, [loaded, areasGeometry.data, showAreas, showIssues, showFacilities]);
  const projected = useMemo(() => {
    if (loaded && !failed) return null;
    const polygons = shapes(geometry.data).flatMap((f) => rings(f.geometry));
    const b =
      bounds(polygons.flat()) ||
      bounds(pointIssues.map((i) => [i.longitude, i.latitude]));
    if (!b) return null;
    const sx = Math.max(0.015, b[1][0] - b[0][0]),
      sy = Math.max(0.015, b[1][1] - b[0][1]),
      scale = Math.min(600 / sx, 260 / sy);
    const cx = (b[0][0] + b[1][0]) / 2,
      cy = (b[0][1] + b[1][1]) / 2;
    const xy = ([x, y]: Position) => [
      320 + (x - cx) * scale,
      150 - (y - cy) * scale,
    ];
    return {
      xy,
      areaPaths: shapes(areasGeometry.data)
        .flatMap((f) => rings(f.geometry))
        .map((r) => "M" + r.map((p) => xy(p).join(",")).join("L") + "Z"),
      paths: polygons.map(
        (r) => "M" + r.map((p) => xy(p).join(",")).join("L") + "Z",
      ),
    };
  }, [geometry.data, areasGeometry.data, pointIssues, loaded, failed]);
  return (
    <div className={"territory-map" + (onPick ? " pick-map" : "")}>
      <div
        className="map-canvas"
        ref={element}
        role="region"
        aria-label={"Mapa de " + city.name}
      />
      {(!loaded || failed) && (
        <div className="map-fallback">
          {projected && (
            <svg viewBox="0 0 640 300" aria-label="Geometria do território">
              {projected.paths.map((d, i) => (
                <path key={i} d={d} />
              ))}
              {showAreas &&
                projected.areaPaths.map((d, i) => (
                  <path className="fallback-area" key={i} d={d} />
                ))}
              {showIssues &&
                pointIssues.map((i) => {
                  const [x, y] = projected.xy([i.longitude, i.latitude]);
                  return (
                    <Link
                      key={i.id}
                      to={"/problemas/" + i.id}
                      aria-label={i.title}
                    >
                      <circle cx={x} cy={y} r="5" />
                    </Link>
                  );
                })}
              {picked && (
                <circle
                  cx={projected.xy(picked)[0]}
                  cy={projected.xy(picked)[1]}
                  r="6"
                />
              )}
            </svg>
          )}
        </div>
      )}
      <span className="map-label">
        <MapPin size={14} />
        {city.name} · {city.state_abbreviation}
      </span>
      <button
        type="button"
        className="map-layers icon-btn"
        aria-label="Camadas do mapa"
        aria-expanded={layers}
        onClick={() => setLayers(!layers)}
      >
        <Layers3 size={16} />
      </button>
      {layers && (
        <div className="layer-menu">
          <strong>Camadas do mapa</strong>
          <label className="check-row">
            <input
              type="checkbox"
              checked={showIssues}
              onChange={(e) => setShowIssues(e.target.checked)}
            />
            Dossiês com localização pontual
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={showAreas}
              onChange={(e) => setShowAreas(e.target.checked)}
            />
            Limites dos bairros
          </label>
          {!!officialPoints.data?.features.length && (
            <label className="check-row">
              <input
                type="checkbox"
                checked={showFacilities}
                onChange={(e) => setShowFacilities(e.target.checked)}
              />
              Equipamentos e obras oficiais
            </label>
          )}
        </div>
      )}
      {!failed && (
        <button
          type="button"
          className="map-fit icon-btn"
          aria-label="Enquadrar território"
          onClick={() =>
            mapRef.current &&
            applyFit(mapRef.current, geometry.data, city, issues, picked)
          }
        >
          <Crosshair size={16} />
        </button>
      )}
      {!!unlocatedCount && (
        <small className="map-unlocated">{unlocatedCount} dossiê(s) com localização apenas municipal; consulte a lista.</small>
      )}
      {(failed || tilesFailed || geometry.isError) && (
        <small className="map-warning">
          {failed
            ? "Visualização simplificada"
            : tilesFailed
              ? "Base cartográfica indisponível"
              : "Limite municipal indisponível"}
          {onPick && failed ? " · Informe as coordenadas abaixo." : ""}
        </small>
      )}
    </div>
  );
}
