import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from 'react-leaflet';

const MapClickHandler = ({ onMapClick }) => {
  useMapEvents({
    click(e) {
      if (onMapClick) {
        onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng });
      }
    },
  });
  return null;
};

const UrbanLeafletMap = ({
  locations = [],
  selectedLocationId = null,
  onSelectLocation,
  onMapClick,
  center = [13.0418, 80.2341],
  zoom = 11,
}) => {
  const activeLoc = locations.find((l) => l.id === selectedLocationId);
  const mapCenter = activeLoc ? [activeLoc.latitude, activeLoc.longitude] : center;

  return (
    <div className="w-full h-80 md:h-96 rounded-xl overflow-hidden border border-slate-800 relative">
      <MapContainer center={mapCenter} zoom={zoom} scrollWheelZoom={true} className="w-full h-full">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors (ODbL)'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapClickHandler onMapClick={onMapClick} />
        {locations.map((loc) => {
          const isSelected = loc.id === selectedLocationId;
          return (
            <CircleMarker
              key={loc.id}
              center={[loc.latitude, loc.longitude]}
              radius={isSelected ? 12 : 8}
              pathOptions={{
                color: isSelected ? '#38bdf8' : '#0284c7',
                fillColor: isSelected ? '#0ea5e9' : '#38bdf8',
                fillOpacity: isSelected ? 0.9 : 0.65,
                weight: isSelected ? 3 : 2,
              }}
              eventHandlers={{
                click: () => onSelectLocation && onSelectLocation(loc),
              }}
            >
              <Popup>
                <div className="text-slate-900 text-xs space-y-1">
                  <div className="font-bold text-sm">{loc.name}</div>
                  <div>City: {loc.city}</div>
                  <div>Coords: {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}</div>
                  <div>Resolution: <span className="font-semibold">{loc.geographical_resolution}</span></div>
                  <div>Zone: {loc.zone_type}</div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default UrbanLeafletMap;

