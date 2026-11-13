"""Real interactive OpenFreeMap map (MapLibre GL) as a Reflex custom component.

The map stays flat (pitch is always 0 and touch pitch is disabled) but it may be
rotated with two fingers. One-finger drag rotation and keyboard rotation stay
off. The stock MapLibre compass is hidden; instead a custom 40x40 navigation
instrument appears at the bottom-left, just above the map/list toggle, and only
while the bearing is meaningfully away from north. Markers are rendered purely
from data props, so a caller decides what information — if any — reaches the
browser.
"""

from typing import TypedDict

import reflex as rx

OPENFREEMAP_LIBERTY = "https://tiles.openfreemap.org/styles/liberty"


class ViewportPoint(TypedDict):
    id: str
    lat: float
    lng: float


class MapMarker(TypedDict, total=False):
    """Marker data. `icon`, `color`, `ink` and `image_url` are optional extras.

    Older callers that only provide id/lng/lat/label/kind/selected keep working:
    the renderer falls back to the basic dot pin when the extras are absent.
    """

    id: str
    lng: float
    lat: float
    label: str
    kind: str
    selected: bool
    icon: str
    color: str
    ink: str
    image_url: str
    draggable: bool
    pulse_token: int


_MAP_COMPONENT = """
const GO_AND_HELP_ICON_PATHS = {
  waves: ["M2 6q3-4 6 0t6 0t8 0", "M2 12q3-4 6 0t6 0t8 0", "M2 18q3-4 6 0t6 0t8 0"],
  music: ["M9 18V5l12-2v13", "M9 18a3 3 0 1 1-3-3h3", "M21 16a3 3 0 1 1-3-3h3"],
  "calendar-heart": ["M3 5h18v16H3z", "M7 2v6M17 2v6M3 10h18", "M12 19l-4-4q-1-4 4-2q5-2 4 2z"],
  house: ["M3 10l9-8 9 8", "M5 9v13h14V9M9 22v-8h6v8"],
  trees: ["M8 3L2 14h12zM8 14v8", "M17 2l-5 9h3l-3 6h10l-3-6h3zM17 17v5"],
  blocks: ["M3 3h8v8H3zM13 13h8v8h-8zM3 13h8v8H3z"],
  bug: ["M8 8h8v10a4 4 0 0 1-8 0z", "M9 8V5h6v3M3 10h5M16 10h5M3 15h5M16 15h5M4 21l4-3M16 18l4 3M12 8v14"],
  landmark: ["M2 8l10-6 10 6zM4 11v8M9 11v8M15 11v8M20 11v8M2 22h20"],
  "chef-hat": ["M6 14a5 5 0 1 1 2-9a5 5 0 0 1 8 0a5 5 0 1 1 2 9v8H6zM6 18h12"],
  trophy: ["M7 3h10v8a5 5 0 0 1-10 0zM7 5H3v4a4 4 0 0 0 4 4M17 5h4v4a4 4 0 0 1-4 4M12 16v6M7 22h10"],
  compass: ["M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20", "M16 8l-3 5-5 3 3-5z"],
  "flower-2": ["M12 8C4-5-3 12 8 12C-3 20 14 28 12 16C20 28 28 10 16 12C28 4 10-3 12 8Z", "M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6"],
  "circle-ellipsis": ["M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20", "M7 12h.01M12 12h.01M17 12h.01"],
  "party-popper": ["M3 21l4-14 10 10zM12 3l1 3M18 2l-2 6M22 7l-5 3M21 13h-2"],
  star: ["m12 2 3.1 6.3 6.9 1-5 4.9 1.2 6.8-6.2-3.2-6.2 3.2 1.2-6.8-5-4.9 6.9-1Z"],
  "users-round": ["M9 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8M2 22v-4a7 7 0 0 1 14 0v4M17 3a4 4 0 0 1 0 8M19 15a5 5 0 0 1 3 5v2"],
  hammer: [
    "m15 12-8.5 8.5a2.12 2.12 0 1 1-3-3L12 9",
    "M17.64 15 22 10.64",
    "m20.91 11.7-1.25-1.25c-.6-.6-.93-1.4-.93-2.25v-.86L16.01 4.6a5.56 5.56 0 0 0-3.94-1.64H9l.92.82A6.18 6.18 0 0 1 12 8.4v1.56l2 2h2.47l2.26 1.91",
  ],
  package: [
    "m7.5 4.27 9 5.15",
    "M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z",
    "m3.3 7 8.7 5 8.7-5",
    "M12 22V12",
  ],
  "hard-hat": [
    "M2 18a1 1 0 0 0 1 1h18a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1H3a1 1 0 0 0-1 1z",
    "M10 10V5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5",
    "M4 15v-3a6 6 0 0 1 6-6",
    "M14 6a6 6 0 0 1 6 6v3",
  ],
  car: [
    "M19 17h2v-5l-3-7H6l-3 7v5h2",
    "M7 17h10",
    "M3 12h18",
    "M7 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z",
    "M17 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z",
  ],
  music: [
    "M9 18V5l12-2v13",
    "M9 18a3 3 0 1 1-3-3 3 3 0 0 1 3 3Z",
    "M21 16a3 3 0 1 1-3-3 3 3 0 0 1 3 3Z",
  ],
  wrench: [
    "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z",
  ],
  "graduation-cap": [
    "M21.42 10.92a1 1 0 0 0-.02-1.84L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.83l8.57 3.91a2 2 0 0 0 1.66 0z",
    "M22 10v6",
    "M6 12.5V16a6 3 0 0 0 12 0v-3.5",
  ],
  "heart-pulse": [
    "M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z",
    "M3.22 13H9.5l.5-1 2 4.5 2-7 1.5 3.5h5.27",
  ],
  baby: [
    "M9 12h.01",
    "M15 12h.01",
    "M10 16c.5.3 1.2.5 2 .5s1.5-.2 2-.5",
    "M19 6.3a9 9 0 0 1 1.8 3.9 2 2 0 0 1 0 3.6 9 9 0 0 1-17.6 0 2 2 0 0 1 0-3.6A9 9 0 0 1 12 3c2 0 3.5 1.1 3.5 2.5S14.6 8 13.5 8c-.8 0-1.5-.4-1.5-1",
  ],
  "hand-heart": [
    "M11 14h2a2 2 0 1 0 0-4h-3c-.6 0-1.1.2-1.4.6L3 16",
    "m7 20 1.6-1.4c.3-.4.8-.6 1.4-.6h4c1.1 0 2.1-.4 2.8-1.2l4.6-4.4a2 2 0 0 0-2.75-2.91l-4.2 3.9",
    "m2 15 6 6",
    "M19.5 8.5c.7-.7 1.5-1.6 1.5-2.7A2.73 2.73 0 0 0 16 4a2.78 2.78 0 0 0-5 1.8c0 1.2.8 2 1.5 2.8L16 12Z",
  ],
  "hand-helping": [
    "M11 12h2a2 2 0 1 0 0-4h-3c-.6 0-1.1.2-1.4.6L3 14",
    "m7 18 1.6-1.4c.3-.4.8-.6 1.4-.6h4c1.1 0 2.1-.4 2.8-1.2l4.6-4.4a2 2 0 0 0-2.75-2.91l-4.2 3.9",
    "m2 13 6 6",
    "M22 5 20 7",
  ],
  palette: [
    "M12 22a1 1 0 0 1 0-20 10 9 0 0 1 10 9 5 5 0 0 1-5 5h-2.25a1.75 1.75 0 0 0-1.4 2.8l.3.4a1.75 1.75 0 0 1-1.4 2.8z",
    "M7.5 10.5h.01",
    "M12 7.5h.01",
    "M16.5 10.5h.01",
  ],
  sprout: [
    "M7 20h10",
    "M10 20c5.5-2.5.8-6.4 3-10",
    "M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z",
    "M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z",
  ],
  "cooking-pot": [
    "M2 12h20",
    "M20 12v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8",
    "m4 8 16-4",
    "m8.86 6.78-.45-1.81a2 2 0 0 1 1.45-2.43l1.94-.48a2 2 0 0 1 2.43 1.46l.45 1.8",
  ],
  brush: [
    "m9.06 11.9 8.07-8.06a2.85 2.85 0 1 1 4.03 4.03l-8.06 8.08",
    "M7.07 14.94c-1.66 0-3 1.35-3 3.02 0 1.33-2.5 1.52-2 2.02 1.08 1.1 2.49 2.02 4 2.02 2.2 0 4-1.8 4-4.04a3.01 3.01 0 0 0-3-3.02z",
  ],
  scale: [
    "m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z",
    "m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z",
    "M7 21h10",
    "M12 3v18",
    "M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2",
  ],
  camera: [
    "M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z",
    "M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  ],
  "shopping-bag": [
    "M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z",
    "M3 6h18",
    "M16 10a4 4 0 0 1-8 0",
  ],
  sparkles: [
    "m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3L12 3Z",
    "M5 3v4",
    "M19 17v4",
    "M3 5h4",
    "M17 19h4",
  ],
  dumbbell: [
    "m6.5 6.5 11 11",
    "m21 21-1-1",
    "m3 3 1 1",
    "m18 22 4-4",
    "m2 6 4-4",
    "m3 10 7-7",
    "m14 21 7-7",
  ],
  cpu: [
    "M12 20v2",
    "M12 2v2",
    "M17 20v2",
    "M17 2v2",
    "M2 12h2",
    "M2 17h2",
    "M2 7h2",
    "M20 12h2",
    "M20 17h2",
    "M20 7h2",
    "M7 20v2",
    "M7 2v2",
    "M15 9a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z",
    "M8 4a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V5a1 1 0 0 0-1-1z",
  ],
  map: [
    "M14.106 5.553a2 2 0 0 0 1.788 0l3.659-1.83A1 1 0 0 1 21 4.619v12.764a1 1 0 0 1-.553.894l-4.553 2.277a2 2 0 0 1-1.788 0l-4.212-2.106a2 2 0 0 0-1.788 0l-3.659 1.83A1 1 0 0 1 3 19.381V6.618a1 1 0 0 1 .553-.894l4.553-2.277a2 2 0 0 1 1.788 0z",
    "M15 5.764v15",
    "M9 3.236v15",
  ],
};

function goAndHelpIconSvg(iconName, size = 15, ink = "#ffffff") {
  const stroke = /^#[0-9a-f]{6}$/i.test(ink) ? ink : "#ffffff";
  const paths =
    GO_AND_HELP_ICON_PATHS[iconName] || GO_AND_HELP_ICON_PATHS["hand-helping"];
  const body = paths.map((d) => '<path d="' + d + '"></path>').join("");
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + size + '" height="' + size + '" ' +
    'fill="none" stroke="' + stroke + '" stroke-width="2.2" stroke-linecap="round" ' +
    'stroke-linejoin="round" aria-hidden="true">' +
    body +
    "</svg>"
  );
}

// Custom compass: helping-green north, white south, and a cobalt dial.
const GO_AND_HELP_COMPASS_SVG =
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30" width="30" height="30" aria-hidden="true" focusable="false">' +
  '<polygon points="15,0.5 19.4,16 15,12.6 10.6,16" fill="#fba922"></polygon>' +
  '<polygon points="15,29.5 10.6,14 15,17.4 19.4,14" fill="#ffffff"></polygon>' +
  '<text x="15" y="10.2" text-anchor="middle" font-size="7.5" font-weight="700" font-family="Inter, system-ui, sans-serif" fill="#111827">N</text>' +
  "</svg>";

function goAndHelpCompass(map, onControl) {
  const button = document.createElement("button");
  button.type = "button";
  button.setAttribute(
    "aria-label",
    "Compass — the map is rotated away from north. Activate to face north again."
  );
  button.title = "Face north";
  button.style.cssText =
    "position:absolute;left:12px;bottom:125px;z-index:25;width:40px;height:40px;" +
    "padding:0;margin:0;box-sizing:border-box;border:5px solid #ffffff;" +
    "border-radius:999px;background:#e08b12;display:none;align-items:center;" +
    "justify-content:center;cursor:pointer;overflow:hidden;";
  const rose = document.createElement("span");
  rose.style.cssText =
    "display:block;width:30px;height:30px;transform-origin:50% 50%;";
  rose.innerHTML = GO_AND_HELP_COMPASS_SVG;
  button.appendChild(rose);
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    if (onControl.current) { onControl.current(); return; }
    map.easeTo({ bearing: 0, duration: 350 });
  });
  const sync = () => {
    const bearing = map.getBearing();
    const normalized = ((bearing % 360) + 360) % 360;
    const meaningful = normalized > 2 && normalized < 358;
    button.style.display = meaningful ? "flex" : "none";
    rose.style.transform = "rotate(" + -bearing + "deg)";
  };
  sync();
  return { element: button, sync: sync };
}

const GO_AND_HELP_MARKER_COLORS = {
  guest: { dot: "#fba922", ring: "rgba(251, 169, 34, 0.18)", ink: "#ffffff" },
  job: { dot: "#e08b12", ring: "rgba(35, 98, 239, 0.18)", ink: "#ffffff" },
  event: { dot: "#dca126", ring: "rgba(220, 161, 38, 0.18)", ink: "#ffffff" },
  helper: { dot: "#e08b12", ring: "rgba(35, 98, 239, 0.20)", ink: "#ffffff" },
  selected: { dot: "#e08b12", ring: "rgba(251, 169, 34, 0.35)", ink: "#ffffff" },
};

function goAndHelpMarkerElement(marker, onSelect) {
  const theme = marker.selected
    ? GO_AND_HELP_MARKER_COLORS.selected
    : GO_AND_HELP_MARKER_COLORS[marker.kind] || GO_AND_HELP_MARKER_COLORS.job;
  const el = document.createElement("button");
  el.type = "button";
  const name = marker.label && marker.label.length > 0 ? marker.label : "Map marker";
  el.setAttribute("aria-label", name);
  el.title = name;
  // Markers are glyph-only: the readable name stays in aria-label/title so the
  // map never carries a text label beneath the circle.
  el.style.cssText =
    "display:flex;align-items:center;justify-content:center;background:none;border:0;padding:0;cursor:pointer;";
  const pin = document.createElement("span");
  const fill = marker.color && marker.color.length > 0 ? marker.color : theme.dot;
  pin.style.cssText =
    "display:flex;align-items:center;justify-content:center;overflow:hidden;width:26px;height:26px;border-radius:999px;border:3px solid #ffffff;box-sizing:content-box;background:" +
    fill +
    ";box-shadow:0 0 0 8px " +
    theme.ring +
    ";color:#ffffff;font-size:11px;font-weight:700;";
  if (marker.id === "onboarding-private-profile" || marker.kind === "onboarding-private-profile") {
    el.className = "gah-segment-control";
pin.style.cssText = "display:flex;align-items:center;justify-content:center;width:48px;height:48px;border-radius:999px;border:0;box-shadow:none;background:#e08b12;color:white;";
    pin.innerHTML = goAndHelpIconSvg("hand-helping", 23);
  } else if (marker.kind === "helper") {
    el.className = "gah-segment-control";
    el.style.borderRadius = "999px";
    el.style.boxShadow = "none";
    pin.style.cssText = "display:flex;align-items:center;justify-content:center;width:45px;height:45px;border-radius:999px;border:0;box-sizing:content-box;background:#fba922;box-shadow:none;";
    if (marker.selected) pin.style.outline = "2px solid #e08b12";
    if (marker.image_url && marker.image_url.length > 0) {
      const photo = document.createElement("img");
      photo.src = marker.image_url;
      photo.alt = "";
      photo.style.cssText = "width:100%;height:100%;object-fit:cover;border-radius:999px;";
      photo.onerror = () => {
        if (photo.parentNode === pin) pin.innerHTML = goAndHelpIconSvg("hand-helping", 30);
      };
      pin.appendChild(photo);
    } else {
      pin.innerHTML = goAndHelpIconSvg("hand-helping", 30);
    }
  } else if (marker.kind === "job") {
    el.className = "gah-segment-control";
    const jobFill = marker.color && marker.color.length > 0 ? marker.color : "#fba922";
    const jobGradient = "linear-gradient(180deg, color-mix(in srgb, " + jobFill + " 92%, white) 0%, " + jobFill + " 52%, color-mix(in srgb, " + jobFill + " 88%, black) 100%)";
    pin.style.cssText = "display:flex;align-items:center;justify-content:center;width:39px;height:39px;border-radius:999px;border:0;box-sizing:content-box;background:" + jobGradient + ";box-shadow:none;";
    if (marker.selected) pin.style.outline = "2px solid #e08b12";
    pin.innerHTML = goAndHelpIconSvg(marker.icon, 27, "#ffffff");
  } else if (marker.kind === "event") {
    el.className = "gah-segment-control";
    pin.style.cssText = "display:flex;align-items:center;justify-content:center;width:39px;height:39px;border-radius:999px;background:#dca126;border:0;box-shadow:none;color:#ffffff;";
    if (marker.selected) pin.style.outline = "2px solid #e08b12";
    pin.innerHTML = goAndHelpIconSvg("star", 27, "#ffffff");
    pin.querySelector("svg").setAttribute("fill", "#ffffff");
  } else if (marker.image_url && marker.image_url.length > 0) {
    const photo = document.createElement("img");
    photo.src = marker.image_url;
    photo.alt = "";
    photo.style.cssText = "width:100%;height:100%;object-fit:cover;border-radius:999px;";
    pin.appendChild(photo);
  } else if (marker.icon && marker.icon.length > 0) {
    pin.innerHTML = goAndHelpIconSvg(marker.icon);
  } else {
    pin.textContent = marker.kind === "helper" ? "\\u2665" : "\\u25CF";
  }
  el.appendChild(pin);
  if (marker.pulse_token) {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
      pin.style.outline = '4px solid #e08b12';
      pin.style.outlineOffset = '5px';
    } else {
      pin.animate(
        [{boxShadow:'0 0 0 0 rgba(224,139,18,.65)'}, {boxShadow:'0 0 0 24px rgba(224,139,18,0)'}],
        {duration: 950, iterations: 5, easing: 'ease-out'}
      );
    }
  }
  el.addEventListener("click", (event) => {
    event.stopPropagation();
    if (onSelect.current) {
      onSelect.current(marker.id);
    }
  });
  return el;
}

function GoAndHelpMapLibre({
  markers = [],
  center = [10, 48],
  zoom = 4,
  styleUrl = "https://tiles.openfreemap.org/styles/liberty",
  className = "",
  onMarkerSelect = null,
  onGuestControl = null,
  onInteractionStart = null,
  onMapClick = null,
  onMarkerDrag = null,
  viewportPoints = [],
  onVisiblePointsChange = null,
  showNavigationControl = true,
  navigationPosition = "top-left",
  attributionVisible = true,
  cameraUpdates = true,
  cameraDuration = 0,
  ...rest
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  // Keyed reconciliation store: marker id -> { marker, signature }. Keeping a
  // Map (instead of a plain array) lets dense maps of hundreds of pins update
  // without full marker churn: unchanged ids keep their existing DOM element
  // and click listener, so nothing is detached or leaked on every render.
  const markersRef = useRef(new Map());
  const selectRef = useRef(onMarkerSelect);
  selectRef.current = onMarkerSelect;
  const guestControlRef = useRef(onGuestControl);
  guestControlRef.current = onGuestControl;
  const interactionRef = useRef(onInteractionStart);
  interactionRef.current = onInteractionStart;
  const mapClickRef = useRef(onMapClick);
  mapClickRef.current = onMapClick;
  const interactionLockRef = useRef(0);
  const markerDragRef = useRef(onMarkerDrag);
  markerDragRef.current = onMarkerDrag;
  const viewportPointsRef = useRef(viewportPoints);
  viewportPointsRef.current = viewportPoints;
  const visibleCallbackRef = useRef(onVisiblePointsChange);
  visibleCallbackRef.current = onVisiblePointsChange;
  const viewportReadyRef = useRef(false);
  const visibleSignatureRef = useRef(null);
  const reportVisibleRef = useRef(null);
  reportVisibleRef.current = () => {
    const map = mapRef.current;
    if (!map || !viewportReadyRef.current || !visibleCallbackRef.current) return;
    const canvas = map.getCanvas();
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!width || !height) return;
    const ids = (viewportPointsRef.current || []).filter((point) => {
      if (!point || typeof point.id !== "string" ||
          !Number.isFinite(point.lng) || !Number.isFinite(point.lat)) return false;
      const pixel = map.project([point.lng, point.lat]);
      return Number.isFinite(pixel.x) && Number.isFinite(pixel.y) &&
        pixel.x >= -16 && pixel.x <= width + 16 &&
        pixel.y >= -16 && pixel.y <= height + 16;
    }).map((point) => point.id).sort();
    const signature = JSON.stringify(ids);
    if (signature === visibleSignatureRef.current) return;
    visibleSignatureRef.current = signature;
    visibleCallbackRef.current(ids);
  };

  useEffect(() => {
    if (mapRef.current || !containerRef.current) {
      return;
    }
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: center,
      zoom: cameraDuration > 0 ? Math.max(2, zoom - 3) : zoom,
      bearing: 0,
      pitch: 0,
      attributionControl: attributionVisible ? { compact: true } : false,
    });
    // Flat but rotatable: two-finger touch rotation only, never one-finger
    // drag rotation, and pitch stays disabled.
    map.dragRotate.disable();
    map.keyboard.disable();
    map.touchZoomRotate.enableRotation();
    map.touchPitch.disable();
    if (showNavigationControl) {
      map.addControl(
        new maplibregl.NavigationControl({
          showCompass: false,
          showZoom: true,
          visualizePitch: false,
        }),
        ["top-left", "top-right", "bottom-left", "bottom-right"].includes(navigationPosition) ? navigationPosition : "top-left"
      );
    }
    mapRef.current = map;
    const compass = goAndHelpCompass(map, guestControlRef);
    containerRef.current.appendChild(compass.element);
    map.on("rotate", compass.sync);
    map.on("move", compass.sync);
    map.on("load", compass.sync);
    const handleViewportLoad = () => {
      viewportReadyRef.current = true;
      reportVisibleRef.current?.();
    };
    const handleViewportChange = () => reportVisibleRef.current?.();
    map.on("load", handleViewportLoad);
    map.on("moveend", handleViewportChange);
    map.on("resize", handleViewportChange);
    // Only user gestures collapse the search: programmatic camera changes carry
    // no originalEvent, so they can never feed back into state.
    const handleInteraction = (event) => {
      if (!interactionRef.current) {
        return;
      }
      if (event && !event.originalEvent) {
        return;
      }
      const now = Date.now();
      if (now - interactionLockRef.current < 400) {
        return;
      }
      interactionLockRef.current = now;
      interactionRef.current();
    };
    const interactionEvents = [
      "mousedown",
      "touchstart",
      "dragstart",
      "wheel",
      "touchmove",
      "zoomstart",
      "rotatestart",
      "boxzoomstart",
    ];
    interactionEvents.forEach((name) => map.on(name, handleInteraction));
    // Optional point picking: a bare map click reports lng/lat to the server.
    const handleMapClick = (event) => {
      if (!mapClickRef.current || !event || !event.lngLat) {
        return;
      }
      mapClickRef.current(event.lngLat.lng, event.lngLat.lat);
    };
    map.on("click", handleMapClick);
    if (onMapClick) {
      map.getCanvas().style.cursor = "crosshair";
    }
    return () => {
      map.off("click", handleMapClick);
      map.off("load", handleViewportLoad);
      map.off("moveend", handleViewportChange);
      map.off("resize", handleViewportChange);
      viewportReadyRef.current = false;
      visibleSignatureRef.current = null;
      interactionEvents.forEach((name) => map.off(name, handleInteraction));
      map.off("rotate", compass.sync);
      map.off("move", compass.sync);
      map.off("load", compass.sync);
      compass.element.remove();
      // Cleanup: remove every retained marker (which detaches its element and
      // its click listener with it), then empty the keyed store.
      markersRef.current.forEach((entry) => entry.marker.remove());
      markersRef.current.clear();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) {
      return;
    }
    const store = markersRef.current;
    const next = markers || [];
    const seen = new Set();
    next.forEach((marker) => {
      const id = String(marker.id);
      if (seen.has(id)) {
        return;
      }
      seen.add(id);
      // Stable signature over every visual/location field the element and its
      // placement depend on: equal signature means the existing marker is
      // already correct and is reused untouched.
      const signature = [
        marker.lng,
        marker.lat,
        marker.label || "",
        marker.kind || "",
        marker.selected ? 1 : 0,
        marker.icon || "",
        marker.color || "",
        marker.ink || "",
        marker.image_url || "",
        marker.draggable ? 1 : 0,
        marker.pulse_token || 0,
      ].join("|");
      const existing = store.get(id);
      if (existing) {
        if (existing.signature === signature) {
          return;
        }
        existing.marker.remove();
        store.delete(id);
      }
      const instance = new maplibregl.Marker({
        element: goAndHelpMarkerElement(marker, selectRef),
        anchor: "center",
        draggable: marker.draggable === true,
      })
        .setLngLat([marker.lng, marker.lat])
        .addTo(map);
      if (marker.pulse_token) instance.getElement().style.zIndex = '1000';
      if (marker.draggable) {
        instance.on("dragend", () => {
          const point = instance.getLngLat();
          if (markerDragRef.current) markerDragRef.current(point.lng, point.lat);
        });
      }
      store.set(id, { marker: instance, signature: signature });
    });
    store.forEach((entry, id) => {
      if (!seen.has(id)) {
        entry.marker.remove();
        store.delete(id);
      }
    });
  }, [markers]);

  useEffect(() => {
    reportVisibleRef.current?.();
  }, [viewportPoints]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !cameraUpdates) return;
    const duration = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : cameraDuration;
    if (duration > 0) map.easeTo({center, zoom, duration});
    else map.jumpTo({center, zoom});
  }, [center[0], center[1], zoom, cameraUpdates, cameraDuration]);

  return <div ref={containerRef} className={className} {...rest} />;
}
"""


class OpenFreeMap(rx.Component):
    """MapLibre GL map rendered with the public OpenFreeMap Liberty style."""

    tag = "GoAndHelpMapLibre"

    markers: rx.Var[list[MapMarker]]
    viewport_points: rx.Var[list[ViewportPoint]]
    center: rx.Var[list[float]]
    zoom: rx.Var[float]
    style_url: rx.Var[str]
    show_navigation_control: rx.Var[bool] = True
    navigation_position: rx.Var[str] = "top-left"
    attribution_visible: rx.Var[bool] = True
    camera_updates: rx.Var[bool] = True
    camera_duration: rx.Var[int] = 0

    on_guest_control: rx.EventHandler[lambda: []]
    on_marker_select: rx.EventHandler[lambda marker_id: [marker_id]]
    on_interaction_start: rx.EventHandler[lambda: []]
    on_map_click: rx.EventHandler[lambda lng, lat: [lng, lat]]
    on_marker_drag: rx.EventHandler[lambda lng, lat: [lng, lat]]
    on_visible_points_change: rx.EventHandler[lambda ids: [ids]]

    def add_imports(self):
        return {
            "react": ["useEffect", "useRef"],
            "maplibre-gl@^5.6.0": [
                rx.ImportVar(tag="maplibregl", is_default=True)
            ],
        }

    def add_custom_code(self) -> list[str]:
        return [_MAP_COMPONENT]


open_free_map = OpenFreeMap.create
