"""Haversine distance and travel-time estimates from Leafy Cave cabana."""

import math


class DistanceCalculator:
    """Offline distance and drive-time helpers for attractions near Wellawaya."""

    AVERAGE_SPEED_KMH = 40  # Sri Lankan rural roads average

    def haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate straight-line distance between two coordinates in km."""
        earth_radius_km = 6371
        lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        return round(earth_radius_km * c, 1)

    def estimate_travel_time(self, distance_km: float) -> dict[str, int | str]:
        """Estimate travel time from distance."""
        minutes = int((distance_km / self.AVERAGE_SPEED_KMH) * 60)
        if minutes < 60:
            return {"minutes": minutes, "formatted": f"{minutes} min drive"}
        hours = minutes // 60
        remaining = minutes % 60
        if remaining == 0:
            return {"minutes": minutes, "formatted": f"{hours} hr drive"}
        return {"minutes": minutes, "formatted": f"{hours} hr {remaining} min drive"}

    def enrich_with_distance(
        self,
        places: list[dict],
        from_lat: float,
        from_lon: float,
    ) -> list[dict]:
        """Add distance_km and travel_time to each place dict."""
        for place in places:
            lat = place.get("lat")
            lon = place.get("lon")
            if lat is not None and lon is not None:
                dist = self.haversine_distance(from_lat, from_lon, float(lat), float(lon))
                place["distance_km"] = dist
                place["travel_time"] = self.estimate_travel_time(dist)
            else:
                place["distance_km"] = None
                place["travel_time"] = None
        return sorted(places, key=lambda item: item.get("distance_km") or 9999)


distance_calculator = DistanceCalculator()
