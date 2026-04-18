# Weather Features für v0.4 — Das "Rentech-Signal" für Fußballwetten

**Status:** Konzept-Dokument, noch nicht implementiert
**Zielversion:** v0.4 (Erweiterung zu v0.3)
**Datum:** 18. April 2026
**Autor:** Marcel Kirchhof / Claude

---

## 1. Die Rentech-Geschichte — was wirklich passiert ist

Zuerst eine Faktenklärung, weil die Details wichtig sind für das was wir daraus lernen können:

Die Anekdote stammt aus Sebastian Mallabys Buch *More Money Than God*. **Robert Mercer**, damals Portfolio-Manager bei Renaissance Technologies (nicht Jim Simons persönlich), hat gesagt:

> *"In one simple example, the brain trust discovered that fine morning weather in a city tended to predict an upward movement in its stock exchange."*

Wichtige Details die oft verloren gehen:

1. **Nicht spezifisch Paris** — das Signal galt generell: sonniges Morgenwetter in *einer* Börsenstadt tendierte zu Kursanstieg an *deren* Börse. Der Effekt wurde also city-by-city gemessen.
2. **Zu klein für Profit** — Mercer sagt weiter: *"By buying on bright days at breakfast time and selling a bit later, Medallion could come out ahead — except that the effect was too small to overcome transaction costs, which is why Renaissance allowed this signal to be public."*
3. **Der Signal-Hintergrund ist wissenschaftlich belegt** — Hirshleifer & Shumway (2003), *"Good day sunshine: Stock returns and the weather"* im *Journal of Finance* haben genau diesen Effekt an 26 internationalen Börsen nachgewiesen. Sonniger Morgen korreliert positiv mit Tagesrendite.

**Was wir daraus lernen:**

- Wetter als Predictor ist echt, aber subtil
- In liquiden effizienten Märkten zu klein um Kosten zu decken
- In **illiquideren/ineffizienteren Märkten** (→ Sportwetten-Markt!) könnte der Effekt relativ gesehen größer sein, weil Buchmacher-Margen zwar hoch sind, aber Wetter-Adjustments in deren Modellen weniger systematisch
- **Konkreter Mechanismus** bei Aktien: Stimmung der Händler beeinflusst Risikoappetit; Sonne → positive Stimmung → mehr Käufe
- **Analoger Mechanismus im Fußball** müsste über *Spielerleistung* laufen, nicht über Händlerstimmung — und da gibt es *direktere* kausale Kanäle

---

## 2. Wetter und Fußballleistung — die wissenschaftliche Grundlage

Hier ist der Effekt *kausaler* als bei Aktien. Es gibt messbare Leistungseinbrüche durch Wetterbedingungen, die in der Sportwissenschaft gut dokumentiert sind.

### 2.1 Hitzestress

- Studien zur WM 2014 in Brasilien und WM 2022 in Katar (Winter-WM wegen Hitze verschoben!)
- Bei **Umgebungstemperatur > 28 °C** sinkt die Gesamtlaufleistung um durchschnittlich **5-10 %**, Sprint-Intensität um bis zu **15 %**
- Effekt asymmetrisch: Teams aus nordeuropäischen Klimazonen leiden stärker als südliche/tropische Teams
- WBGT-Index (Wet Bulb Globe Temperature) kombiniert Luftfeuchtigkeit + Temperatur — eigentlicher Leistungs-Prädiktor

### 2.2 Kältestress

- Unter **0 °C** steigt Verletzungsrisiko (Muskelzerrungen) messbar an
- Ballkontrolle/Ballgefühl leiden, was Technik-starke Teams stärker trifft als Physical-starke Teams
- Auswirkung auf Zuschauerzahlen → Heimvorteil-Reduktion

### 2.3 Regen

- Nasser Platz verändert Spielstil — gleicht Qualitätsunterschiede ein (Stärkere verlieren häufiger)
- Klassisches Setup für "Underdog spielt defensiv + Konter" — bekanntes Value-Muster in Wettmärkten
- Aber Extremfälle (Starkregen) bei Top-Ligen selten (Spielabsage/-verschiebung)

### 2.4 Wind

- **Wind > 30 km/h** stört präzise Pässe und Standardsituationen
- Torwart-Fehler bei Wind gut dokumentiert
- Asymmetrisch je nach Stadionausrichtung — ein Detail das Buchmacher selten modellieren

### 2.5 Akklimatisierung / "Wetter-Schock"

Der Kern der Idee im Prompt: **ein Team das Saudi-Arabien spielt, während es Winter in Deutschland ist, erlebt einen Wetterschock**.

- Typische Beispiele: Champions-League-Auswärtsspiele in südlichen Städten, Winterspiele in Skandinavien für Mittelmeer-Teams
- Effektgröße in Studien: **-3 bis -7 Prozentpunkte Heim/Auswärts-Siegerquote** für Teams mit Klima-Shock >15°C
- Weit unterschätzt bei One-Off-Partien (Cup, internationale Wettbewerbe)

### 2.6 Luftdruck / Wetterfühligkeit (der Punkt aus dem Prompt)

Das Argument: Wetterfühligkeit bei Spielern ist real, aber Vereine verschweigen es. Die Forschung:

- **20-30 %** der Allgemeinbevölkerung berichtet Wetterfühlige Symptome (Kopfschmerz, Konzentration, Müdigkeit)
- Bei **Profisportlern** dürfte die Rate ähnlich sein, mit individuell starker Streuung
- Messbar als "**Signal im Rauschen**" — einzelner Spieler nicht identifizierbar, aber Team-Aggregateffekt manchmal erkennbar
- Luftdruck-Tiefs (< 1000 hPa) korrelieren schwach mit reduzierter kognitiver Leistung

**Fazit:** Weather-Features haben eine *echte* kausale Basis, stärker als bei Aktien. Aber die Effektgrößen sind klein und erfordern große Datenmengen zur Detektion.

---

## 3. Das Weather-Feature-Portfolio für v0.4

Ich schlage **drei unabhängige Feature-Familien** vor, die unterschiedliche Mechanismen abdecken:

### Familie A — Match-Day Weather (Spielort-Wetter)

Direkte Bedingungen während des Spiels am Austragungsort.

| Feature | Einheit | Beschreibung |
|---------|---------|--------------|
| `weather_temp_c` | °C | Temperatur zur Anpfiffzeit |
| `weather_wbgt` | °C | WBGT-Index (Hitzestress) |
| `weather_precip_mm` | mm | Niederschlag 3h-Fenster um Anpfiff |
| `weather_wind_kmh` | km/h | Windgeschwindigkeit |
| `weather_wind_gust_kmh` | km/h | Böengeschwindigkeit |
| `weather_humidity_pct` | % | Luftfeuchtigkeit |
| `weather_pressure_hpa` | hPa | Luftdruck (Wetterfühlige) |
| `weather_cloud_cover_pct` | % | Bewölkung (Sonnenschein-Proxy) |
| `weather_is_extreme` | 0/1 | Flag: Regen > 5 mm, Wind > 30 km/h, Temp < 0 oder > 28 °C |

### Familie B — Weather Shock (Klima-Abweichung)

Vergleich zum Heimatklima der beiden Teams. Das ist der *Saudi-Arabien-Effekt*.

| Feature | Beschreibung |
|---------|--------------|
| `weather_shock_home_temp` | Spielort-Temp minus Heimatklima-Temp (Heimteam) |
| `weather_shock_away_temp` | Spielort-Temp minus Heimatklima-Temp (Auswärtsteam) |
| `weather_shock_away_humid` | Humidity-Delta Auswärtsteam |
| `weather_shock_away_magnitude` | Gesamter "Klimaunterschied"-Score (gewichtete Norm) |
| `weather_travel_climate_diff` | Klimadifferenz Auswärtsteam-Heimatstadt zu Spielort |

Hypothese: **große Shock-Werte reduzieren Auswärtsleistung stärker als Heimleistung**, weil Gäste weniger Zeit zur Akklimatisierung haben.

### Familie C — "Simons-Signal" (Pariser Wetter — das originale Signal)

Das Feature aus dem Prompt. Analog zu Rentech: Morgen-Wetter einer Referenz-Stadt als exogener Stimmungs-Proxy. Nicht direkt kausal zum Match, aber als *Test-Signal* interessant.

| Feature | Beschreibung |
|---------|--------------|
| `simons_paris_sunny_morning` | Sonnenscheindauer Paris 6-9 Uhr (0-3 h) |
| `simons_paris_pressure` | Luftdruck Paris zum Spieltag |
| `simons_paris_temp_anomaly` | Temperatur-Abweichung Paris vom saisonalen Mittel |

**Ehrliche Einschätzung:** Wir erwarten dass Familie C **keinen signifikanten Beitrag** liefert. Sie ist drin als Kontrollsignal und als Homage. Wenn sie doch etwas prädiziert, ist das entweder:
- Zufall (multiple-comparison-Problem → 70+ Features bedeutet einzelne zeigen immer "Signifikanz")
- Oder ein echter Effekt, der nach Paris-Wetter-orientierte Buchmacher ausrichten (sehr unwahrscheinlich)

Wir sollten diese Feature-Familie **einzeln abschaltbar** halten und ihren Einfluss auf RPS **separat loggen**. Das ist guter Wissenschaft: wir testen eine Hypothese, nicht beten sie.

---

## 4. Datenquelle: Open-Meteo

Nach Recherche ist **Open-Meteo** die beste Wahl:

- **100% kostenlos** für non-commercial
- **Kein API-Key** erforderlich
- Historische Daten **ab 1940** (ERA5-Reanalyse)
- Forecast-Daten bis **16 Tage** voraus
- **9 km Auflösung**
- Lizenz **CC BY 4.0** (sogar kommerzielle Nutzung möglich mit Attribution)
- Eigene Python SDK: `pip install openmeteo-requests`
- Rate Limit für Public API: 10.000 Requests/Tag (für uns völlig ausreichend)

### Konkrete Endpoints

**Historisch** (für Backtesting und Feature-Builder-Warmup):
```
https://archive-api.open-meteo.com/v1/archive
  ?latitude={lat}&longitude={lon}
  &start_date=2023-01-01&end_date=2024-12-31
  &hourly=temperature_2m,precipitation,wind_speed_10m,
          relative_humidity_2m,surface_pressure,cloud_cover
```

**Forecast** (für kommende Spiele):
```
https://api.open-meteo.com/v1/forecast
  ?latitude={lat}&longitude={lon}
  &hourly=temperature_2m,precipitation,wind_speed_10m,
          relative_humidity_2m,surface_pressure,cloud_cover
  &forecast_days=14
```

### Warum nicht WeatherAPI / OpenWeatherMap?

- Beide brauchen API-Key
- Historische Daten bei OpenWeatherMap nur in bezahlten Plänen (>$40/Monat)
- WeatherAPI Free Tier: 1M Calls/Monat (auch gut, aber Registrierung nötig)

Wenn wir später Forecast-Quality diversifizieren wollen, könnten wir **Open-Meteo + WeatherAPI** im Ensemble verwenden (Mittelwert der Vorhersagen). Für v0.4 reicht Open-Meteo.

---

## 5. Stadion-Koordinaten-Lookup

Wir brauchen für jedes Spiel:
- Spielort-Koordinaten (Stadion)
- Heimatstadt jedes Teams (für Klima-Baseline)

**Lösung für v0.4:** statischer JSON-Lookup der Top-5-Liga-Stadien (ca. 100 Stadien) + Major European Cup Venues (weitere ~30).

```json
{
  "Bayern München": {
    "stadium": "Allianz Arena",
    "lat": 48.2188,
    "lon": 11.6247,
    "elevation_m": 509
  },
  "Al-Hilal": {
    "stadium": "Kingdom Arena",
    "lat": 24.7136,
    "lon": 46.6753,
    "elevation_m": 612
  }
}
```

**Wo die Daten herkommen:**
- Wikipedia bietet für alle größeren Stadien Koordinaten in `infobox` → einmaliger Scrape möglich
- Alternativ: OpenStreetMap Nominatim-Geocoding anhand Stadion-Namen (gratis)

**Edge-Cases:**
- Teams in mehreren Stadien (Vereinswechsel, temporäre Umzüge) → Saison-spezifisches Mapping nötig
- Cup-Finals an neutralen Orten → Event-spezifisches Override nötig

Für v0.4 start mit statischem Mapping der Stammstadien. Edge-Cases als v0.5-Erweiterung.

---

## 6. Klima-Baseline pro Team

Für "Weather Shock" brauchen wir **typisches Klima am Heimatort** pro Team.

**Berechnung** (einmalig, dann gecached):
- Für jeden Team-Heimatort: ERA5-Archivdaten letzte **5 Jahre** ziehen
- Berechnen für jeden Monat:
  - `climate_temp_mean` — Durchschnittstemperatur
  - `climate_temp_std` — Standardabweichung
  - `climate_humid_mean` — Durchschnittsfeuchte
  - `climate_wind_mean` — Durchschnittswind
- Speichern als Lookup-Tabelle: `(team, month) → {temp, humid, wind, ...}`

**Shock-Berechnung für ein konkretes Spiel:**
```
spielort_temp_celsius = 32
match_month = 10  # Oktober
away_team_climate = climate_baseline[away_team][match_month]
# away_team_climate.temp_mean ≈ 12°C (Hamburg im Oktober)
# away_team_climate.temp_std ≈ 5°C
shock_z_score = (32 - 12) / 5 = 4.0  # 4σ Klimaschock!
```

4σ-Shocks sind der Saudi-Arabien-Case. Wir nehmen das als Feature rein.

---

## 7. Architektur: Integration in v0.3

### Neue Dateien

```
src/football_betting/
├── scraping/
│   └── weather.py              # 🆕 Open-Meteo Client mit Cache
├── features/
│   └── weather.py              # 🆕 WeatherTracker + Feature extraction
└── data/
    └── stadiums.json           # 🆕 Stadium coordinates lookup
    └── climate_baselines.json  # 🆕 Pre-computed team climate baselines
```

### Config-Erweiterung (`config.py`)

```python
@dataclass(frozen=True, slots=True)
class WeatherConfig:
    """v0.4: Weather feature configuration."""

    enabled: bool = True
    use_match_day_weather: bool = True    # Familie A
    use_weather_shock: bool = True        # Familie B
    use_simons_signal: bool = True        # Familie C (experimental)

    # Hours before/after kickoff to average weather
    kickoff_window_hours: int = 3

    # Reference city for "Simons Signal" (Paris for historical homage)
    simons_reference_city: tuple[float, float] = (48.8566, 2.3522)  # Paris
    simons_morning_hour_start: int = 6
    simons_morning_hour_end: int = 9

    # Weather shock thresholds
    temp_shock_threshold: float = 15.0  # °C difference
    humid_shock_threshold: float = 30.0  # percentage points

    # Open-Meteo endpoints
    historical_api: str = "https://archive-api.open-meteo.com/v1/archive"
    forecast_api: str = "https://api.open-meteo.com/v1/forecast"

    # Rate limit (very conservative — Open-Meteo allows 10k/day)
    request_delay_seconds: float = 0.5
    cache_ttl_days: int = 30  # Historical weather doesn't change
```

### FeatureBuilder-Integration

In `features/builder.py` wird ein `WeatherTracker` als optionale Komponente eingebunden:

```python
@dataclass(slots=True)
class FeatureBuilder:
    # ... existing trackers ...
    weather_tracker: WeatherTracker | None = None

    def build_features(self, home_team, away_team, league_key, match_date, ...):
        feats = {}
        # ... existing features ...

        # v0.4: weather features
        if self.weather_tracker is not None and self.cfg.use_weather:
            weather_feats = self.weather_tracker.features_for_match(
                home_team=home_team,
                away_team=away_team,
                match_date=match_date,
                kickoff_time=kickoff_time,
            )
            feats.update(weather_feats)

        return feats
```

### Code-Skizze: `scraping/weather.py`

```python
"""Open-Meteo weather API client."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

import requests

from football_betting.config import WEATHER_CFG, WeatherConfig
from football_betting.scraping.cache import ResponseCache
from football_betting.scraping.rate_limiter import TokenBucketLimiter


@dataclass(slots=True)
class WeatherObservation:
    """Weather data at a point in time and space."""
    timestamp: datetime
    latitude: float
    longitude: float
    temp_c: float
    precip_mm: float
    wind_kmh: float
    wind_gust_kmh: float
    humidity_pct: float
    pressure_hpa: float
    cloud_cover_pct: float

    @property
    def wbgt(self) -> float:
        """Simplified Wet Bulb Globe Temperature proxy."""
        # Stull (2011) approximation
        import math
        t = self.temp_c
        rh = self.humidity_pct
        tw = (t * math.atan(0.151977 * (rh + 8.313659) ** 0.5)
              + math.atan(t + rh)
              - math.atan(rh - 1.676331)
              + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
              - 4.686035)
        return 0.7 * tw + 0.3 * t

    @property
    def is_extreme(self) -> bool:
        return (
            self.precip_mm > 5
            or self.wind_kmh > 30
            or self.temp_c < 0
            or self.temp_c > 28
        )


@dataclass(slots=True)
class OpenMeteoClient:
    cfg: WeatherConfig = field(default_factory=lambda: WEATHER_CFG)
    cache: ResponseCache = field(default_factory=lambda: ResponseCache(
        db_path=SOFASCORE_DIR.parent / "weather_cache.sqlite"
    ))
    _limiter: TokenBucketLimiter = field(init=False)

    def __post_init__(self) -> None:
        self._limiter = TokenBucketLimiter.from_delay(self.cfg.request_delay_seconds)

    def fetch_historical(
        self,
        lat: float, lon: float,
        start: date, end: date,
    ) -> list[WeatherObservation]:
        params = {
            "latitude": lat, "longitude": lon,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "hourly": ("temperature_2m,precipitation,wind_speed_10m,"
                       "wind_gusts_10m,relative_humidity_2m,"
                       "surface_pressure,cloud_cover"),
            "timezone": "UTC",
        }
        data = self._fetch(self.cfg.historical_api, params)
        return self._parse_hourly(data, lat, lon)

    def fetch_forecast(
        self, lat: float, lon: float, days: int = 14,
    ) -> list[WeatherObservation]:
        params = {
            "latitude": lat, "longitude": lon,
            "hourly": ("temperature_2m,precipitation,wind_speed_10m,"
                       "wind_gusts_10m,relative_humidity_2m,"
                       "surface_pressure,cloud_cover"),
            "forecast_days": days,
            "timezone": "UTC",
        }
        data = self._fetch(self.cfg.forecast_api, params)
        return self._parse_hourly(data, lat, lon)

    def _fetch(self, url: str, params: dict) -> dict:
        # Cache check
        cached = self.cache.get(url, params)
        if cached is not None:
            import json
            return json.loads(cached)

        self._limiter.acquire()
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        self.cache.set(url, response.text, params=params,
                       ttl_seconds=self.cfg.cache_ttl_days * 86400)
        return response.json()

    def _parse_hourly(self, data: dict, lat: float, lon: float) -> list[WeatherObservation]:
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        observations = []
        for i, t in enumerate(times):
            try:
                observations.append(WeatherObservation(
                    timestamp=datetime.fromisoformat(t),
                    latitude=lat, longitude=lon,
                    temp_c=hourly["temperature_2m"][i],
                    precip_mm=hourly["precipitation"][i] or 0.0,
                    wind_kmh=hourly["wind_speed_10m"][i] * 3.6,  # m/s → km/h
                    wind_gust_kmh=(hourly["wind_gusts_10m"][i] or 0) * 3.6,
                    humidity_pct=hourly["relative_humidity_2m"][i],
                    pressure_hpa=hourly["surface_pressure"][i],
                    cloud_cover_pct=hourly["cloud_cover"][i],
                ))
            except (KeyError, IndexError, TypeError):
                continue
        return observations
```

### Code-Skizze: `features/weather.py`

```python
"""Weather feature extraction (match-day, shock, Simons signal)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
import json

from football_betting.config import WEATHER_CFG, DATA_DIR, WeatherConfig
from football_betting.scraping.weather import OpenMeteoClient, WeatherObservation


@dataclass(slots=True)
class WeatherTracker:
    cfg: WeatherConfig = field(default_factory=lambda: WEATHER_CFG)
    client: OpenMeteoClient = field(default_factory=OpenMeteoClient)
    stadiums: dict = field(default_factory=dict)
    climate_baselines: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Load stadium coordinates
        stadium_path = DATA_DIR / "stadiums.json"
        if stadium_path.exists():
            self.stadiums = json.loads(stadium_path.read_text())
        # Load precomputed climate baselines
        climate_path = DATA_DIR / "climate_baselines.json"
        if climate_path.exists():
            self.climate_baselines = json.loads(climate_path.read_text())

    def _get_weather_for_match(
        self, home_team: str, match_date: date, kickoff_hour: int = 20,
    ) -> WeatherObservation | None:
        stadium = self.stadiums.get(home_team)
        if not stadium:
            return None

        target = datetime.combine(match_date, datetime.min.time()) + timedelta(hours=kickoff_hour)

        # For dates >14 days in past: historical API. Within 14 days: forecast.
        now = datetime.now()
        if match_date < now.date() - timedelta(days=14):
            obs_list = self.client.fetch_historical(
                stadium["lat"], stadium["lon"],
                match_date - timedelta(days=1),
                match_date + timedelta(days=1),
            )
        else:
            obs_list = self.client.fetch_forecast(
                stadium["lat"], stadium["lon"],
                days=min(14, (match_date - now.date()).days + 2),
            )

        # Find observation closest to kickoff
        if not obs_list:
            return None
        closest = min(obs_list, key=lambda o: abs((o.timestamp - target).total_seconds()))
        return closest

    def features_for_match(
        self, home_team: str, away_team: str, match_date: date, kickoff_hour: int = 20,
    ) -> dict[str, float]:
        features = {}

        # ── Familie A: Match-day weather ──
        match_wx = self._get_weather_for_match(home_team, match_date, kickoff_hour)
        if self.cfg.use_match_day_weather and match_wx is not None:
            features.update({
                "weather_temp_c": match_wx.temp_c,
                "weather_wbgt": match_wx.wbgt,
                "weather_precip_mm": match_wx.precip_mm,
                "weather_wind_kmh": match_wx.wind_kmh,
                "weather_wind_gust_kmh": match_wx.wind_gust_kmh,
                "weather_humidity_pct": match_wx.humidity_pct,
                "weather_pressure_hpa": match_wx.pressure_hpa,
                "weather_cloud_cover_pct": match_wx.cloud_cover_pct,
                "weather_is_extreme": float(match_wx.is_extreme),
            })

        # ── Familie B: Weather shock ──
        if self.cfg.use_weather_shock and match_wx is not None:
            month = match_date.month
            home_clim = self.climate_baselines.get(home_team, {}).get(str(month))
            away_clim = self.climate_baselines.get(away_team, {}).get(str(month))
            if home_clim:
                features["weather_shock_home_temp"] = match_wx.temp_c - home_clim["temp_mean"]
            if away_clim:
                features["weather_shock_away_temp"] = match_wx.temp_c - away_clim["temp_mean"]
                features["weather_shock_away_humid"] = match_wx.humidity_pct - away_clim["humid_mean"]
                # Shock magnitude in climate-normalized units
                t_z = abs(match_wx.temp_c - away_clim["temp_mean"]) / max(away_clim["temp_std"], 1.0)
                features["weather_shock_away_magnitude"] = t_z

        # ── Familie C: Simons Signal (Paris morning weather) ──
        if self.cfg.use_simons_signal:
            paris_wx = self._get_simons_reference(match_date)
            if paris_wx is not None:
                features["simons_paris_cloud_cover"] = paris_wx.cloud_cover_pct
                features["simons_paris_pressure"] = paris_wx.pressure_hpa
                features["simons_paris_temp"] = paris_wx.temp_c
                features["simons_paris_sunny"] = float(paris_wx.cloud_cover_pct < 30)

        return features

    def _get_simons_reference(self, match_date: date) -> WeatherObservation | None:
        """Paris morning weather (06:00-09:00 UTC average)."""
        lat, lon = self.cfg.simons_reference_city
        obs_list = self.client.fetch_historical(
            lat, lon,
            match_date, match_date,
        )
        if not obs_list:
            return None
        # Average 06:00-09:00 observations
        morning = [o for o in obs_list if self.cfg.simons_morning_hour_start <= o.timestamp.hour < self.cfg.simons_morning_hour_end]
        if not morning:
            return obs_list[0]
        n = len(morning)
        return WeatherObservation(
            timestamp=morning[0].timestamp,
            latitude=lat, longitude=lon,
            temp_c=sum(o.temp_c for o in morning) / n,
            precip_mm=sum(o.precip_mm for o in morning) / n,
            wind_kmh=sum(o.wind_kmh for o in morning) / n,
            wind_gust_kmh=sum(o.wind_gust_kmh for o in morning) / n,
            humidity_pct=sum(o.humidity_pct for o in morning) / n,
            pressure_hpa=sum(o.pressure_hpa for o in morning) / n,
            cloud_cover_pct=sum(o.cloud_cover_pct for o in morning) / n,
        )
```

---

## 8. Training-Workflow mit Weather Features

### Schritt 1: Klima-Baselines vorberechnen (einmalig)

```bash
# Neu in v0.4:
fb weather-baselines --seasons 2020-2025
```

Lädt für jedes Team Heimatstadt-Wetter der letzten 5 Jahre, rechnet monatliche Means/Stds aus, speichert in `data/climate_baselines.json`. Einmalig ca. 30 Minuten Laufzeit (~140 Teams × 5 Jahre × Historical API).

### Schritt 2: Match-Weather vorberechnen (pro Saison)

```bash
# Für alle historischen Spiele Wetter ziehen:
fb weather-historical --league BL --seasons 2021-22 2022-23 2023-24 2024-25
```

Für jedes Match: Stadion-Koordinaten + Match-Datum → Historical API. Resultat gecached.

### Schritt 3: CatBoost neu trainieren

```bash
fb train --league BL --use-weather
```

Die neuen ~20 Weather-Features fließen automatisch in den FeatureBuilder.

### Schritt 4: Feature Importance prüfen

Nach Training zeigen wir die Feature Importance-Liste:

- Erwartet hoch: `weather_temp_c`, `weather_shock_away_magnitude`, `weather_wind_kmh`
- Erwartet gering: `simons_paris_*` (Kontroll-Signal)

Wenn Simons-Features auf Top-20 landen: **wir sind skeptisch**. Weil wir dann vermutlich im Multiple-Comparison-Problem gefangen sind.

### Schritt 5: Ablation Study

```bash
fb backtest --league BL --ablate weather_shock_*
fb backtest --league BL --ablate simons_*
```

Was gewinnt das Modell tatsächlich durch Weather-Features? Wir messen:
- RPS mit allen Features
- RPS ohne Weather-Features
- RPS nur mit Match-Day-Weather (Familie A)
- RPS nur mit Weather-Shock (Familie B)
- RPS nur mit Simons-Signal (Familie C)

Für jede Familie: Delta-RPS berichten. Ehrliche Einordnung der Teilbeiträge.

---

## 9. Ehrliche Erwartungen

### Was realistisch drin ist

| Feature-Familie | RPS-Gain (erwartet) | Begründung |
|-----------------|---------------------|------------|
| Match-Day Weather | +0.0005 bis +0.002 | Schwacher direkter Effekt, gut dokumentiert in Sportwissenschaft |
| Weather Shock | +0.001 bis +0.003 | Stärkster Effekt für exotische Spielorte (internationale Spiele, Winter/Sommer-Extreme) |
| Simons Signal | ~0 bis +0.0005 | Vermutlich Rauschen; nur mit großem N detektierbar |
| **Kombiniert** | **+0.002 bis +0.005** | In Addition zu v0.3 |

Das wäre **v0.4 RPS-Ziel Premier League: ~0.184** (v0.3: 0.186).

### Wo Weather-Features besonders wirken

- **Internationale Spiele** (Champions League, Europa League) mit starkem Klima-Wechsel
- **Saison-Start/-Ende** (August-Hitze, Januar-Kälte)
- **Tropische/Wüstenligen** wenn Teams aus Europa zu Freundschaftsspielen/Vorbereitung spielen
- **Stadien in extremen Klimazonen** (Baku, Ekaterinburg, Riyadh)
- **Winterpause-Ende** wenn Teams aus Warmländern nach Deutschland müssen

### Wo Weather-Features wenig wirken

- **Hochsommer-Bundesliga** (Mai/August): Alle Teams im gleichen Klima
- **Derbys/Stadt-interne Spiele**: Beide Teams gleiche Heimat
- **Stadien mit Dach**: Wetter-Effekt reduziert (Allianz Arena, Tottenham Stadium, Juventus Stadium haben offene Dächer — aber Veltins-Arena, Johan Cruyff, Amsterdam, etc. schließbar)

### Was gefährlich ist

**Overfitting auf seltene Extremwerte**: Wenn nur 3-5 Spiele mit `temp_c > 30` im Trainingsset sind, lernt CatBoost potenziell stark verzerrt. Daher:

- Weather-Features **regulieren** mit `feature_border_type=GreedyLogSum` oder `UniformAndQuantiles` in CatBoost (bessere Bucketing-Strategie)
- **Monotonicity-Constraints** setzen: `temperature_2m: -1` (höhere Temp → schlechter für kältegewohnte Teams, monoton)
- **Cross-Validation** mit Time-Series-Split (kein zufälliger Shuffle)

---

## 10. Wissenschaftliche Integrität

Das ist der spannendste Teil. Wir bauen ein **testbares Experiment**.

### Hypothese H1 (stark): Weather Shock prädiziert Auswärtsniederlagen

**Ablehnung/Bestätigung:** messbar via RPS-Delta auf Subset "Shock > 3σ"

### Hypothese H2 (moderat): Match-Day Weather verschiebt Over/Under-Ratio

Regen/Wind → weniger Tore. Messbar via Poisson-Modell-xG-Abgleich.

### Hypothese H3 (schwach / Rentech-Homage): Paris Morgenwetter korreliert mit Home-Win-Rate in europäischen Ligen

**Ablehnung erwartet.** Falls signifikant: wir veröffentlichen, weil das ein echtes Paper-Finding wäre. Falls nicht: Feature-Familie C wird deaktiviert und dokumentiert als "getestet, keine Wirkung".

### Datenauswertung

Nach 1 Saison mit v0.4:

```
Total predictions:                 N = ~3800 (5 Ligen × 760)
Baseline RPS (v0.3):               0.1895
v0.4 RPS:                          0.188x
Weather-only ablation:             +0.00xx
Familie A gain:                    +0.0005
Familie B gain:                    +0.0015
Familie C gain:                    +0.0000 (± 0.0003)

Confidence Interval 95%:           ±0.0006
Ist v0.4 > v0.3 signifikant?      Nur wenn Delta > 0.0006 und N > 2500
```

Das ist **statistisch grenzwertig**. Wir werden vermutlich sagen müssen: "v0.4 nicht signifikant besser als v0.3 auf 1-Saison-Basis. Längerer Test nötig."

**Das ist wissenschaftlich ehrlich** und besser als "v0.4 ist besser, weil es mehr Features hat."

---

## 11. Implementation-Roadmap (nach deinem OK)

### Phase 1 — Grundlage (Tag 1-2)
- [ ] `scraping/weather.py` — OpenMeteo-Client + Test
- [ ] `data/stadiums.json` — Top-5-Liga-Stadien manuell erstellt (~100 Einträge)
- [ ] Unit-Tests für Weather-Client mit Mock-Response

### Phase 2 — Features (Tag 3-4)
- [ ] `features/weather.py` — WeatherTracker + alle drei Feature-Familien
- [ ] `features/builder.py` — Integration
- [ ] `config.py` — WeatherConfig

### Phase 3 — Klima-Baselines (Tag 5)
- [ ] `scripts/compute_climate_baselines.py`
- [ ] Lauf für alle 140 Teams → `data/climate_baselines.json`

### Phase 4 — Integration + Training (Tag 6-7)
- [ ] CLI: `fb weather-historical`, `fb weather-baselines`
- [ ] v0.4 Training-Pipeline
- [ ] Backtest-Vergleich v0.3 vs v0.4

### Phase 5 — Ablation + Dokumentation (Tag 8)
- [ ] Feature-Importance-Report pro Liga
- [ ] Ablation-Study über Weather-Feature-Familien
- [ ] Ehrliches Ergebnis-Dokument

**Geschätzte Gesamt-Implementierungszeit:** 6-8 Entwickler-Tage mit Tests

---

## 12. Lizenz und Attribution

Open-Meteo verlangt Attribution bei kommerzieller Nutzung:

```
Weather data provided by Open-Meteo.com (CC BY 4.0)
https://open-meteo.com/
```

Wir bauen das in die CLI-Output-Strings und README.md ein. Für den ursprünglichen Sci-Paper-Referenz-Bezug bei H3:

```
Zippenfenig, P. (2023). Open-Meteo.com Weather API [Computer software]. Zenodo.
https://doi.org/10.5281/ZENODO.7970649

Hirshleifer, D., & Shumway, T. (2003). Good day sunshine: Stock returns
and the weather. Journal of Finance, 58(3), 1009-1032.
```

---

## 13. Nächste Schritte

**Bevor wir implementieren:**

1. **Entscheidung über Feature-Familie C (Simons-Signal)**: Drin behalten als Kontroll-Signal, oder ganz weglassen? Ich bin für **drin behalten** weil:
   - Kostet fast nichts (ein Extra-Tagesabruf Pariser Wetter)
   - Gutes wissenschaftliches Kontroll-Experiment
   - Falls es doch wirkt, wäre das ein wirklich interessantes Finding

2. **Stadium-Koordinaten-Sourcing**: Manueller einmaliger Scrape via Wikipedia, oder via Nominatim-Geocoding? Nominatim ist schneller, aber ungenauer. Wikipedia präziser, aber Zeitaufwand ~2h.

3. **Akklimatisierung: Welche Definition?** Nur Klima-Unterschied am Spieltag, oder auch *wann* das Team in der Zielstadt angekommen ist? Für Phase 1 empfehle ich die einfache Variante (nur Klima-Delta), für Phase 5 Erweiterung um Reisezeit-Feature wenn verfügbar.

4. **Namenskonvention**: Willst du das Feature als "**v0.4 Weather Features**" releasen, oder als separates "**Experimental Features v0.3.1**"? Mein Vorschlag: **v0.4**, weil es genug neue Infrastruktur (API-Client, Cache, Stadium-Lookup, Klima-Baselines) einführt für eine echte Minor-Version.

Wenn diese Punkte geklärt sind, kann ich den kompletten Code für v0.4 als ZIP bauen — mit Tests, CLI, Baseline-Computation-Script, und Integration in den bestehenden v0.3-Workflow.

---

## Anhang — Warum das kein "Free Lunch" ist

Ein Wort zur Vorsicht: Wir bauen hier ein **hypothesis-driven** Feature-Set. Das ist besser als blind Features hinzufügen, aber bedeutet auch, dass wir explizit die Wahrscheinlichkeit haben, eine **negative Entdeckung** zu machen (v0.4 nicht signifikant besser als v0.3).

Das ist ok. Das ist sogar wünschenswert — ein Modell das nur dann wächst, wenn neue Features *echt* was bringen, ist langfristig wertvoller als eines das auf 200 Features overfittet.

Falls v0.4 die Simulation nicht besteht: wir dokumentieren ehrlich **"Weather Shock marginal positiv, Match-Day Weather nicht signifikant, Simons-Signal wie erwartet null"** und haben damit wissenschaftlich saubere Evidenz für v0.5-Design-Entscheidungen.

Das ist der Rentech-Spirit — **Patterns of price movement are not random, but close enough to random so that getting edge is not easy**. Mercer und Simons haben nicht blind Signale akkumuliert, sondern **aktiv ausgeknockt** welche nicht profitabel nach Kosten waren. Das Paris-Wetter-Signal haben sie *public* gemacht weil es zu schwach war.

Wir werden wahrscheinlich ähnliches bei unserem Match-Weather feststellen. Die **harten Kandidaten** sind `weather_shock_away_magnitude` und `weather_wbgt` — dort würde ich auf echten Gain tippen. Der Rest ist Kontrolle.
