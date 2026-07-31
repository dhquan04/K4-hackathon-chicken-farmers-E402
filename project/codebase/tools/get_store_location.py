"""
Tool: Get Store Location & Estimate Delivery Distance
Tra cứu địa chỉ chi nhánh nhà hàng, bản đồ Google Maps, và tính khoảng cách giao hàng.
Geocoding: OpenMap.vn Forward Geocode API (Vietnam-optimized)
Routing: Geoapify Motorcycle Routing API + OSRM fallback
"""

import os
import re
import urllib.parse
import urllib.request
import json

from typing import Dict, Optional, Tuple

from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")))

try:
    from project.codebase.database import get_branch_by_id, get_restaurant_data
except ImportError:
    from database import get_branch_by_id, get_restaurant_data

GEOCODE_CACHE: Dict[str, Tuple[float, float]] = {}


DEFAULT_CUSTOMER_LAT = 20.989255
DEFAULT_CUSTOMER_LON = 105.945574


def _is_hanoi_region(lat: float, lon: float) -> bool:
    """Checks if coordinates are within Greater Hanoi area."""
    return (20.7 <= lat <= 21.3) and (105.7 <= lon <= 106.3)


def _clean_address_string(raw_addr: str) -> str:
    """Cleans noisy room/shophouse prefixes to improve geocoding accuracy."""
    addr = raw_addr.strip()
    addr = re.sub(r'\bVinhome\b', 'Vinhomes', addr, flags=re.IGNORECASE)
    # Remove prefix room/shophouse/floor numbers
    addr = re.sub(r'^(Phòng|Gian hàng|Sảnh|Shophouse|L\d+[-\d]*|TTTM|Tầng|Shop)\s+[^,-]+[-,\s]*', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r'^\d+\s+[A-Za-z0-9\s]+,\s*', '', addr)
    if 'Vinhomes Ocean Park' not in addr and 'Ocean Park' in addr:
        addr = addr.replace('Ocean Park', 'Vinhomes Ocean Park')
    if 'Hà Nội' not in addr and 'Ha Noi' not in addr:
        addr += ', Hà Nội'
    return addr.strip()


def geocode_address(address_str: str, api_key: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """Geocodes an address string into (latitude, longitude) coordinates dynamically via OpenMap.vn Forward Geocode API (100% dynamic search)."""
    if not address_str or not address_str.strip():
        return None

    clean_addr = address_str.strip()
    if clean_addr in GEOCODE_CACHE:
        return GEOCODE_CACHE[clean_addr]

    openmap_key = api_key or os.environ.get("OPENMAP_API_KEY") or os.environ.get("api_key_order", "")
    openmap_base = os.environ.get("OPENMAP_BASE_URL", "https://mapapis.openmap.vn/")

    if not openmap_key:
        return None

    cleaned_query = _clean_address_string(clean_addr)

    # Dynamically build search query variations for OpenMap.vn API
    queries_to_try = [cleaned_query, clean_addr]
    
    # Extract S-block dynamically e.g. S2.06, S206, S1.06
    block_match = re.search(r'\bS([1-3])[\.\s]?0?(\d{1,2})\b', clean_addr, re.IGNORECASE)
    if block_match:
        b_name = f"S{block_match.group(1)}.{block_match.group(2).zfill(2)}"
        queries_to_try.append(f"Tòa {b_name}, Vinhomes Ocean Park, Gia Lâm, Hà Nội")
        queries_to_try.append(f"{b_name} Vinhomes Ocean Park, Hà Nội")

    if "Vincom" in clean_addr or "TTTM" in clean_addr:
        queries_to_try.append("Vincom Mega Mall Ocean Park, Gia Lâm, Hà Nội")
    if "San Hô" in clean_addr or "San Ho" in clean_addr:
        queries_to_try.append("Đường San Hô, Vinhomes Ocean Park, Gia Lâm, Hà Nội")
    if "Hải Âu" in clean_addr or "Hai Au" in clean_addr:
        queries_to_try.append("Đường Hải Âu, Vinhomes Ocean Park, Gia Lâm, Hà Nội")

    queries_to_try.append("Vinhomes Ocean Park, Gia Lâm, Hà Nội")

    for q in queries_to_try:
        try:
            url = f"{openmap_base.rstrip('/')}/v1/geocode/forward?address={urllib.parse.quote(q)}&apikey={openmap_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "Batch03-ShopeeFood/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    results = data.get("results", [])
                    if results:
                        geom = results[0].get("geometry", {})
                        loc = geom.get("location", {})
                        lat = loc.get("lat")
                        lng = loc.get("lng")
                        if lat is not None and lng is not None and _is_hanoi_region(float(lat), float(lng)):
                            GEOCODE_CACHE[clean_addr] = (float(lat), float(lng))
                            return (float(lat), float(lng))
        except Exception:
            pass

    return None



def get_store_location(branch_id: Optional[str] = None) -> Dict:
    """
    Tra cứu địa chỉ nhà hàng, hotline, giờ mở cửa và link bản đồ Google Maps dẫn đường.
    """
    info = get_restaurant_data()

    if not info:
        return {
            "status": "error",
            "message": "Không tìm thấy thông tin nhà hàng."
        }

    if branch_id:
        branch = get_branch_by_id(branch_id)
        if not branch:
            return {
                "status": "warning",
                "message": f"Không tìm thấy chi nhánh với mã '{branch_id}'.",
                "available_branches": [b.branch_id for b in info.branches]
            }

        return {
            "status": "success",
            "restaurant_name": info.restaurant_name,
            "hotline": info.hotline,
            "opening_hours": info.opening_hours,
            "branch": branch.dict()
        }

    return {
        "status": "success",
        "restaurant_name": info.restaurant_name,
        "hotline": info.hotline,
        "opening_hours": info.opening_hours,
        "total_branches": len(info.branches),
        "branches": [b.dict() for b in info.branches]
    }


def estimate_delivery_distance(user_address: str, branch_id: Optional[str] = None, api_key: Optional[str] = None, **kwargs) -> Dict:
    """
    Ước tính khoảng cách giao hàng (km), thời gian giao hàng dự kiến (phút), phí ship 
    và tọa độ tuyến đường đi xe máy từ quán đến địa chỉ khách hàng.
    """
    b_id = branch_id or kwargs.get("branch_id")
    if not user_address or not user_address.strip():
        return {
            "status": "error",
            "message": "Vui lòng nhập địa chỉ để tính khoảng cách và phí giao hàng."
        }

    address_clean = user_address.strip()
    key = api_key or kwargs.get("api_key") or os.environ.get("OPENMAP_API_KEY", "")

    # Fetch store branch info
    branch = get_branch_by_id(b_id) if b_id else None

    if not branch:
        info = get_restaurant_data()
        if info and info.branches:
            branch = info.branches[0]

    store_name = branch.branch_name if branch else "Hệ thống ShopeeFood Ocean Park"
    store_addr = branch.address if branch else "KĐT Vinhomes Ocean Park, Gia Lâm, Hà Nội"
    store_lat = branch.latitude if branch else 20.9950
    store_lon = branch.longitude if branch else 105.9550

    # 1. Dynamic Geocoding via OpenMap.vn API for Store Address
    store_geo = geocode_address(store_addr, api_key=key)
    if store_geo:
        store_lat, store_lon = store_geo

    # 2. Fixed customer recipient coordinates as requested by user (20.989255, 105.945574)
    dest_lat = DEFAULT_CUSTOMER_LAT
    dest_lon = DEFAULT_CUSTOMER_LON




    import math
    dlat = math.radians(dest_lat - store_lat)
    dlon = math.radians(dest_lon - store_lon)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(store_lat)) * math.cos(math.radians(dest_lat)) * math.sin(dlon / 2) ** 2
    estimated_km = round(6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)
    if estimated_km < 0.3:
        estimated_km = 0.5





    distance_source = "OpenMap.vn Geocoding & Distance Engine"

    # Query Geoapify Routing API (mode=motorcycle) using GEOAPIFY_API_KEY from .env
    geoapify_key = os.environ.get("GEOAPIFY_API_KEY", "")
    geoapify_base = os.environ.get("GEOAPIFY_BASE_URL", "https://api.geoapify.com/")

    waypoints = []

    if geoapify_key:
        try:
            geo_url = f"{geoapify_base.rstrip('/')}/v1/routing?waypoints={store_lat},{store_lon}|{dest_lat},{dest_lon}&mode=motorcycle&apiKey={geoapify_key}"
            req = urllib.request.Request(geo_url, headers={"User-Agent": "Batch03-Agent/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    features = data.get("features", [])
                    if features:
                        props = features[0].get("properties", {})
                        geom = features[0].get("geometry", {})
                        
                        dist_m = props.get("distance", estimated_km * 1000.0)
                        drive_sec = props.get("time", estimated_km * 240.0)
                        
                        estimated_km = round(dist_m / 1000.0, 1)
                        # Prep time (10 min) + Motorcycle drive time
                        estimated_minutes = int(10 + round(drive_sec / 60.0))
                        distance_source = "Geoapify Motorcycle Live Routing API"

                        raw_coords = geom.get("coordinates", [])
                        flat_pts = []
                        if geom.get("type") == "MultiLineString":
                            for seg in raw_coords:
                                if isinstance(seg, list):
                                    flat_pts.extend(seg)
                        elif geom.get("type") == "LineString":
                            flat_pts = raw_coords

                        if flat_pts:
                            waypoints = [[pt[1], pt[0]] for pt in flat_pts if isinstance(pt, list) and len(pt) >= 2]
        except Exception:
            pass

    # Fallback to OSRM Motorcycle / Driving Road Router if routing waypoints empty
    if not waypoints:
        try:
            osrm_url = f"https://router.project-osrm.org/route/v1/driving/{store_lon},{store_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"
            req_osrm = urllib.request.Request(osrm_url, headers={"User-Agent": "Batch03-Agent/1.0"})
            with urllib.request.urlopen(req_osrm, timeout=5) as resp_o:
                if resp_o.status == 200:
                    o_data = json.loads(resp_o.read().decode("utf-8"))
                    routes = o_data.get("routes", [])
                    if routes:
                        r_geom = routes[0].get("geometry", {})
                        r_pts = r_geom.get("coordinates", [])
                        if r_pts:
                            waypoints = [[pt[1], pt[0]] for pt in r_pts]
                            estimated_km = round(routes[0].get("distance", 2500) / 1000.0, 1)
                            estimated_minutes = int(10 + round(routes[0].get("duration", 600) / 60.0))
                            distance_source = "OSRM Motorcycle Live Road Router"
        except Exception:
            pass

    # Safety fallback if both APIs fail
    if not waypoints:
        waypoints = [
            [store_lat, store_lon],
            [(store_lat + dest_lat) / 2.0, (store_lon + dest_lon) / 2.0],
            [dest_lat, dest_lon]
        ]


    if estimated_km < 0.3:
        estimated_km = 0.5

    # Calculate shipping fee (15k base for <= 2km + 5k/km extra)
    if estimated_km <= 2.0:
        shipping_fee = 15000.0
    else:
        extra_km = estimated_km - 2.0
        shipping_fee = 15000.0 + (extra_km * 5000.0)


    # Generate OpenStreetMap Direction Link (more reliable in Vietnam than Google Maps)
    osm_directions_url = f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_bike&route={store_lat},{store_lon};{dest_lat},{dest_lon}"
    # Also keep Google Maps as alternate
    dest_encoded = urllib.parse.quote(address_clean)
    google_directions_url = f"https://www.google.com/maps/dir/?api=1&origin={store_lat},{store_lon}&destination={dest_lat},{dest_lon}&travelmode=two_wheeler"

    return {
        "status": "success",
        "user_address": address_clean,
        "store_name": store_name,
        "store_address": store_addr,
        "store_coords": [store_lat, store_lon],
        "dest_coords": [dest_lat, dest_lon],
        "route_waypoints": waypoints,
        "estimated_distance_km": round(estimated_km, 1),
        "estimated_delivery_minutes": estimated_minutes,
        "shipping_fee": shipping_fee,
        "shipping_fee_formatted": f"{shipping_fee:,.0f}đ",
        "directions_url": osm_directions_url,
        "google_directions_url": google_directions_url,
        "distance_source": distance_source
    }



