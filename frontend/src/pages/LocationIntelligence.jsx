import React, { useState, useEffect } from 'react';
import { MapPin, Search, CloudRain, Wind, Thermometer, PlusCircle, Globe, ShieldAlert } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import api, { extractErrorMessage } from '../services/api';
import UrbanLeafletMap from '../maps/UrbanLeafletMap';
import { LoadingSkeleton, AlertBanner } from '../components/LoadingSkeleton';

const LocationIntelligence = () => {
  const [locations, setLocations] = useState([]);
  const [selectedLoc, setSelectedLoc] = useState(null);
  const [locDetails, setLocDetails] = useState(null);
  const [liveTelemetry, setLiveTelemetry] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [useNominatim, setUseNominatim] = useState(false);
  const [externalMatches, setExternalMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Custom coordinate form
  const [newLocName, setNewLocName] = useState('');
  const [newLocCity, setNewLocCity] = useState('Chennai');
  const [newLat, setNewLat] = useState(13.0827);
  const [newLng, setNewLng] = useState(80.2707);

  const fetchLocations = async (query = '') => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/locations/search', {
        params: { q: query || undefined, include_external_geocoding: useNominatim },
      });
      const list = res.data.locations || [];
      setLocations(list);
      setExternalMatches(res.data.external_geocoding_results || []);
      if (list.length > 0 && !selectedLoc) {
        selectLocation(list[0]);
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const selectLocation = async (loc) => {
    setSelectedLoc(loc);
    setLiveTelemetry(null);
    try {
      const res = await api.get(`/locations/${loc.id}`);
      setLocDetails(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleFetchLiveAPIs = async () => {
    if (!selectedLoc) return;
    setError('');
    try {
      const res = await api.post(`/locations/${selectedLoc.id}/live-weather`);
      setLiveTelemetry(res.data);
      setSuccess('Retrieved Open-Meteo & OpenAQ telemetry metadata for selected coordinates.');
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  const handleAddLocation = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await api.post('/locations', {
        name: newLocName,
        city: newLocCity,
        latitude: parseFloat(newLat),
        longitude: parseFloat(newLng),
        geographical_resolution: 'coordinate_pin',
        zone_type: 'Custom Monitored Locality',
      });
      setNewLocName('');
      setSuccess(`Added monitored locality: ${res.data.name}`);
      await fetchLocations();
      selectLocation(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  };

  useEffect(() => {
    fetchLocations();
  }, []);

  if (loading && locations.length === 0) {
    return <LoadingSkeleton rows={5} label="Loading geospatial intelligence & OpenStreetMap layers..." />;
  }

  const latest = locDetails?.latest_measurements || {};
  const trends = locDetails?.historical_trends || {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Hyperlocal Location Intelligence</h1>
        <p className="text-xs text-slate-400 mt-1">
          Interactive OpenStreetMap geospatial explorer with explicit geographical resolution and source attribution.
        </p>
      </div>

      <AlertBanner type="error" message={error} onClose={() => setError('')} />
      <AlertBanner type="success" message={success} onClose={() => setSuccess('')} />

      {/* Search & Coordinate Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            fetchLocations(searchQuery);
          }}
          className="lg:col-span-7 p-4 rounded-2xl border border-slate-800 bg-slate-900/60 flex flex-wrap items-center gap-3"
        >
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search city, locality, or corridor..."
              className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
            />
          </div>
          <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={useNominatim}
              onChange={(e) => setUseNominatim(e.target.checked)}
              className="rounded border-slate-700"
            />
            <span>Query OSM Nominatim</span>
          </label>
          <button
            type="submit"
            className="px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-xs transition"
          >
            Search Localities
          </button>
        </form>

        {/* Add Coordinate Form */}
        <form
          onSubmit={handleAddLocation}
          className="lg:col-span-5 p-4 rounded-2xl border border-slate-800 bg-slate-900/60 grid grid-cols-2 sm:grid-cols-4 gap-2 items-center"
        >
          <input
            type="text"
            required
            placeholder="Locality Name"
            value={newLocName}
            onChange={(e) => setNewLocName(e.target.value)}
            className="px-2.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
          />
          <input
            type="number"
            step="any"
            required
            placeholder="Lat"
            value={newLat}
            onChange={(e) => setNewLat(e.target.value)}
            className="px-2.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
          />
          <input
            type="number"
            step="any"
            required
            placeholder="Lng"
            value={newLng}
            onChange={(e) => setNewLng(e.target.value)}
            className="px-2.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
          />
          <button
            type="submit"
            className="flex items-center justify-center gap-1 px-3 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Pin</span>
          </button>
        </form>
      </div>

      {/* Map & Locality Selector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 space-y-3">
          <UrbanLeafletMap
            locations={locations}
            selectedLocationId={selectedLoc?.id}
            onSelectLocation={(loc) => selectLocation(loc)}
            onMapClick={({ lat, lng }) => {
              setNewLat(lat.toFixed(4));
              setNewLng(lng.toFixed(4));
            }}
          />
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>
              Tip: Click any marker to inspect locality telemetry, or click anywhere on the map to pre-fill coordinates.
            </span>
            <span>Map tiles © OpenStreetMap contributors (ODbL)</span>
          </div>
        </div>

        {/* Locality Directory List */}
        <div className="lg:col-span-4 p-4 rounded-2xl border border-slate-800 bg-slate-900/50 flex flex-col max-h-[430px]">
          <h3 className="text-sm font-semibold mb-3">Monitored Urban Localities ({locations.length})</h3>
          <div className="space-y-2 overflow-y-auto flex-1 pr-1">
            {locations.map((loc) => {
              const active = selectedLoc?.id === loc.id;
              return (
                <button
                  key={loc.id}
                  onClick={() => selectLocation(loc)}
                  className={`w-full text-left p-3 rounded-xl border transition text-xs ${
                    active
                      ? 'bg-sky-500/15 border-sky-500/50 text-sky-200'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-semibold flex items-center justify-between">
                    <span>{loc.name}</span>
                    <MapPin className="w-3.5 h-3.5 text-sky-400 shrink-0" />
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1">
                    {loc.city} | {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}
                  </div>
                  <div className="mt-1 inline-block px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">
                    Resolution: {loc.geographical_resolution}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Selected Location Detail Panel */}
      {locDetails && (
        <div className="space-y-6">
          <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/60">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
              <div>
                <h2 className="text-lg font-bold text-white">{locDetails.location.name}</h2>
                <p className="text-xs text-slate-400">
                  City: {locDetails.location.city} | Coordinates: ({locDetails.location.latitude}, {locDetails.location.longitude}) |
                  Elevation: {locDetails.location.elevation_m ?? 'N/A'}m | Resolution:{' '}
                  <span className="text-sky-400 font-semibold">{locDetails.location.geographical_resolution}</span>
                </p>
              </div>
              <button
                onClick={handleFetchLiveAPIs}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 border border-sky-400/40 text-sky-300 text-xs font-semibold transition"
              >
                <Globe className="w-4 h-4" />
                <span>Query Open-Meteo & OpenAQ Live Telemetry</span>
              </button>
            </div>

            {/* Latest Measurements Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
              {Object.entries(latest).map(([ind, obj]) => (
                <div key={ind} className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                  <div className="text-[11px] text-slate-400 uppercase">{ind}</div>
                  <div className="text-lg font-bold text-sky-400 mt-1">
                    {obj.value} <span className="text-xs font-normal text-slate-400">{obj.unit}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1 truncate">
                    {obj.observed_at ? obj.observed_at.slice(0, 10) : ''}
                  </div>
                </div>
              ))}
            </div>

            {/* Live External API Telemetry Box */}
            {liveTelemetry && (
              <div className="mt-4 p-4 rounded-xl bg-sky-950/30 border border-sky-500/30 text-xs space-y-2">
                <div className="font-semibold text-sky-300">
                  External API Integration Snapshot ({liveTelemetry.open_meteo?.status})
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-300">
                  <div>
                    <div>Source: {liveTelemetry.open_meteo?.source_name}</div>
                    <div>Resolution: {liveTelemetry.open_meteo?.geographical_resolution}</div>
                    <div>Retrieved: {liveTelemetry.open_meteo?.retrieved_at}</div>
                    {liveTelemetry.open_meteo?.current?.temperature_2m !== undefined && (
                      <div className="text-sky-400 font-semibold mt-1">
                        Live Grid Temp: {liveTelemetry.open_meteo.current.temperature_2m} °C |
                        Wind: {liveTelemetry.open_meteo.current.wind_speed_10m} km/h
                      </div>
                    )}
                    {liveTelemetry.open_meteo?.error_note && (
                      <div className="text-amber-300 mt-1">{liveTelemetry.open_meteo.error_note}</div>
                    )}
                  </div>
                  <div>
                    <div>Air Quality Source: {liveTelemetry.openaq?.source_name}</div>
                    <div>Attribution: {liveTelemetry.openaq?.attribution}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Historical Trend Charts for Selected Location */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-sky-400" />
                <span>Locality Temperature History (°C)</span>
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trends.temperature_c || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={10} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                    <Line type="monotone" dataKey="value" stroke="#38bdf8" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="p-5 rounded-2xl border border-slate-800 bg-slate-900/50">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Wind className="w-4 h-4 text-amber-400" />
                <span>Locality PM2.5 History (µg/m³)</span>
              </h3>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trends.pm25 || []}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="timestamp" stroke="#94a3b8" fontSize={10} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: 12 }} />
                    <Line type="monotone" dataKey="value" stroke="#f59e0b" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LocationIntelligence;

