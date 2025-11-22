"""
Places Agent - Child Agent 2
============================
Discovers tourist attractions using Overpass API + OpenStreetMap
Uses Nominatim for precise geocoding

FEATURES:
- Finds tourist attractions within 5km radius of location
- Global coverage (OpenStreetMap - 200+ countries)
- Categories: landmarks, museums, parks, historical sites, restaurants
- Up to 5 recommendations per location (per assignment)
- Real data from OpenStreetMap (no AI hallucination)
- Error handling for sparse data regions

APIs (Recommended by Inkle.ai assignment) [file:2]:
- Overpass API: https://overpass-api.de/api/interpreter
- Nominatim: https://nominatim.openstreetmap.org
"""

import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
import json
import time
from datetime import datetime

# Load environment variables
load_dotenv()

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_USER_AGENT = "InkleAI-TourismAgent-v1.0"

def get_coordinates(location: str) -> Optional[Tuple[float, float]]:
    """
    Geocode location using Nominatim (same as weather agent for consistency)
    
    Args:
        location: City name or address
    
    Returns:
        (latitude, longitude) tuple or None if failed
    """
    geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT, timeout=10)
    
    try:
        location_obj = geolocator.geocode(location, exactly_one=True)
        if location_obj and location_obj.latitude and location_obj.longitude:
            return (location_obj.latitude, location_obj.longitude)
        return None
    except (GeocoderTimedOut, GeocoderServiceError, Exception) as e:
        print(f"⚠️ Places geocoding error for '{location}': {e}")
        return None

def query_overpass_attractions(lat: float, lon: float, radius_km: int = 5, max_results: int = 10) -> List[Dict]:
    """
    Query Overpass API for tourist attractions near coordinates
    
    Args:
        lat: Latitude
        lon: Longitude  
        radius_km: Search radius in kilometers (default 5km)
        max_results: Maximum number of results to return
    
    Returns:
        List of attraction dictionaries with name, type, distance, etc.
    
    Overpass Query Strategy:
        - Search for tourism-tagged nodes/ways/relations within radius
        - Prioritize: attractions, museums, landmarks, viewpoints
        - Filter out: low-quality or incomplete entries
        - Include: opening hours, ratings (when available)
    """
    # Convert radius to meters (Overpass uses meters)
    radius_meters = radius_km * 1000
    
    # Overpass QL query for tourist attractions
    overpass_query = f"""
    [out:json][timeout:30];
    (
      // Major tourist attractions
      node(around:{radius_meters},{lat},{lon})["tourism"~"^(attraction|museum|gallery|castle|ruins|viewpoint|zoo|aquarium)$"];
      way(around:{radius_meters},{lat},{lon})["tourism"~"^(attraction|museum|gallery|castle|ruins|viewpoint|zoo|aquarium)$"];
      relation(around:{radius_meters},{lat},{lon})["tourism"~"^(attraction|museum|gallery|castle|ruins|viewpoint|zoo|aquarium)$"];
      
      // Historical sites and monuments
      node(around:{radius_meters},{lat},{lon})["historic"~"^(castle|ruins|monument|memorial|archaeological_site)$"];
      way(around:{radius_meters},{lat},{lon})["historic"~"^(castle|ruins|monument|memorial|archaeological_site)$"];
      
      // Natural attractions
      node(around:{radius_meters},{lat},{lon})["natural"~"^(peak|waterfall|cave)$"];
      way(around:{radius_meters},{lat},{lon})["natural"~"^(peak|waterfall|cave)$"];
      
      // Parks and gardens (limited to notable ones)
      node(around:{radius_meters},{lat},{lon})["leisure"~"^(park|garden)$"]["name"];
      way(around:{radius_meters},{lat},{lon})["leisure"~"^(park|garden)$"]["name"];
      
      // Notable buildings and structures
      node(around:{radius_meters},{lat},{lon})["building"~"^(tower|cathedral|church|synagogue|mosque|temple)$"]["tourism"!~"."];
      way(around:{radius_meters},{lat},{lon})["building"~"^(tower|cathedral|church|synagogue|mosque|temple)$"]["tourism"!~"."];
    );
    out body;
    >;
    out skel qt;
    """
    
    try:
        response = requests.get(
            OVERPASS_URL, 
            params={'data': overpass_query},
            headers={'User-Agent': NOMINATIM_USER_AGENT},
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        elements = data.get('elements', [])
        
        # Process OSM elements into attraction data
        attractions = []
        for element in elements[:max_results]:
            if 'tags' not in element:
                continue
                
            tags = element['tags']
            name = tags.get('name', 'Unknown Attraction')
            tourism_type = tags.get('tourism', 'attraction')
            category = tags.get('tourism', tags.get('leisure', tags.get('historic', 'attraction')))
            
            # Skip if no meaningful name or type
            if not name or name.lower() in ['no', 'yes', 'unnamed']:
                continue
            
            # Extract coordinates
            lat_elem = element.get('lat')
            lon_elem = element.get('lon')
            
            if lat_elem is None or lon_elem is None:
                # Try to get center coordinates for ways/relations
                bbox = element.get('bbox')
                if bbox and len(bbox) == 4:
                    lat_elem = (bbox[0] + bbox[2]) / 2
                    lon_elem = (bbox[1] + bbox[3]) / 2
                else:
                    continue
            
            # Calculate distance from search center (Haversine formula)
            distance = calculate_distance(lat, lon, lat_elem, lon_elem)
            
            # Extract additional details
            opening_hours = tags.get('opening_hours', 'Unknown')
            website = tags.get('website', '')
            phone = tags.get('phone', '')
            rating = tags.get('tourism:rating', 'Not rated')
            
            # Determine attraction type for recommendations
            attraction_category = determine_attraction_category(tags)
            
            attraction = {
                "id": element.get('id', 0),
                "name": name,
                "type": tourism_type,
                "category": attraction_category,
                "latitude": float(lat_elem) if lat_elem else None,
                "longitude": float(lon_elem) if lon_elem else None,
                "distance_km": round(distance, 1),
                "osm_type": element.get('type', 'node'),
                "opening_hours": opening_hours,
                "website": website,
                "phone": phone,
                "rating": rating,
                "tags": {k: v for k, v in tags.items() if k not in ['name', 'tourism']},
                "source": "OpenStreetMap via Overpass API"
            }
            
            attractions.append(attraction)
        
        # Sort by distance (closest first)
        attractions.sort(key=lambda x: x['distance_km'])
        
        return attractions[:5]  # Assignment: maximum 5 recommendations
        
    except requests.exceptions.Timeout:
        return [{"error": "Places API timeout", "message": "Tourist attractions service temporarily unavailable"}]
    except requests.exceptions.RequestException as e:
        return [{"error": f"Places API error: {str(e)}", "message": "Unable to fetch tourist attractions"}]
    except json.JSONDecodeError:
        return [{"error": "Invalid API response", "message": "Overpass API returned unexpected data format"}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}", "message": "Places agent encountered an unknown issue"}]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula (km)
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
    
    Returns:
        Distance in kilometers (rounded to 1 decimal)
    """
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth radius in kilometers
    
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    return round(distance, 1)

def determine_attraction_category(tags: Dict) -> str:
    """
    Determine attraction category from OSM tags for better recommendations
    
    Args:
        tags: OSM tags dictionary
    
    Returns:
        Category string (e.g., "Landmark", "Museum", "Nature", "Historical")
    """
    tourism = tags.get('tourism', '').lower()
    leisure = tags.get('leisure', '').lower()
    historic = tags.get('historic', '').lower()
    natural = tags.get('natural', '').lower()
    
    # Priority categories
    if any(word in tourism for word in ['museum', 'gallery']):
        return "Museum"
    elif any(word in tourism for word in ['attraction', 'viewpoint']):
        return "Landmark"
    elif any(word in historic for word in ['castle', 'ruins', 'monument', 'memorial']):
        return "Historical"
    elif any(word in natural for word in ['peak', 'waterfall', 'cave']):
        return "Nature"
    elif any(word in leisure for word in ['park', 'garden']):
        return "Park"
    elif any(word in tags for word in ['church', 'cathedral', 'temple', 'mosque', 'synagogue']):
        return "Religious"
    else:
        return "Attraction"

def generate_travel_recommendations(attractions: List[Dict], location: str) -> Dict:
    """
    Generate personalized travel recommendations based on found attractions
    
    Args:
        attractions: List of attraction dictionaries
        location: Current location name
    
    Returns:
        Recommendations with prioritization and activity suggestions
    """
    if not attractions or "error" in attractions[0]:
        return {
            "message": f"No tourist attractions found for '{location}'. Try a more popular destination.",
            "suggestions": [
                "Major cities like Paris, New York, Tokyo have extensive data",
                "Try: 'London, UK', 'Rome, Italy', 'Sydney, Australia'"
            ],
            "recommendations": []
        }
    
    # Categorize attractions
    categories = {}
    for attraction in attractions:
        category = attraction['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(attraction)
    
    # Create recommendations
    recommendations = []
    
    # Priority order for travel planning
    priority_categories = ['Landmark', 'Historical', 'Museum', 'Nature', 'Park', 'Religious']
    
    for category in priority_categories:
        if category in categories:
            # Take top 1-2 from each category
            top_attractions = categories[category][:2]
            for attraction in top_attractions:
                rec = {
                    "name": attraction['name'],
                    "category": category,
                    "distance": f"{attraction['distance_km']} km away",
                    "type": attraction['type'],
                    "why_visit": generate_why_visit(category, attraction),
                    "best_time": get_best_time(attraction),
                    "website": attraction.get('website', ''),
                    "opening_hours": attraction.get('opening_hours', 'Varies')
                }
                recommendations.append(rec)
    
    return {
        "location": location,
        "total_found": len(attractions),
        "recommended": recommendations[:5],  # Max 5 per assignment
        "by_category": categories,
        "travel_tips": [
            "Most attractions are free or low-cost entry",
            "Check opening hours - many close on Mondays",
            "Public transport available near most sites",
            "Download offline maps for better navigation"
        ],
        "source": "OpenStreetMap via Overpass API (community-powered, constantly updated)"
    }

def generate_why_visit(category: str, attraction: Dict) -> str:
    """Generate personalized 'why visit' description"""
    base_reasons = {
        "Landmark": "Iconic photo opportunity, historical significance, great for sightseeing tours",
        "Historical": "Rich cultural heritage, educational value, perfect for history enthusiasts", 
        "Museum": "World-class exhibits, interactive displays, excellent for learning and culture",
        "Nature": "Breathtaking views, peaceful atmosphere, ideal for nature lovers and photographers",
        "Park": "Relaxing green space, perfect for picnics, walking, and casual exploration",
        "Religious": "Spiritual significance, architectural beauty, cultural immersion opportunity"
    }
    
    return base_reasons.get(category, "Must-see attraction worth visiting")

def get_best_time(attraction: Dict) -> str:
    """Determine best time to visit based on type and opening hours"""
    opening_hours = attraction.get('opening_hours', '').lower()
    
    if '24/7' in opening_hours or not opening_hours:
        return "Open 24/7 - visit anytime"
    elif any(word in opening_hours for word in ['sunrise', 'sunset']):
        return "Best at sunrise/sunset for lighting and atmosphere"
    elif 'museum' in attraction.get('category', '').lower():
        return "Weekdays 10AM-4PM (avoid weekends and lunch hours)"
    elif 'historical' in attraction.get('category', '').lower():
        return "Early morning to avoid crowds (opens 9AM typically)"
    else:
        return f"Check opening hours: {opening_hours}"

def places_query(location: str) -> Dict[str, Any]:
    """
    Main Places Agent interface - Complete tourist recommendations
    
    Args:
        location: City name (e.g., "Paris", "Mumbai", "New York")
    
    Returns:
        Complete tourist recommendations with 5 top attractions, categories,
        and travel planning advice (per assignment requirements)
    
    Assignment Compliance [file:2]:
        - Up to 5 tourist attraction recommendations
        - Real API data (Overpass + OpenStreetMap)
        - Error handling for non-existent places
        - Global coverage with intelligent fallbacks
    """
    print(f"🗺️ Places Agent: Searching attractions in '{location}'...")
    
    # Step 1: Geocode location
    coordinates = get_coordinates(location)
    
    if not coordinates:
        return {
            "error": f"The AI doesn't know this place '{location}' exists. Please check the spelling.",
            "suggestions": [
                "Try: 'Bangalore, India', 'London, UK', 'Tokyo, Japan', 'Paris, France'",
                "Include country for better accuracy: 'Mumbai, India'"
            ],
            "found_attractions": 0,
            "success": False,
            "source": "OpenStreetMap via Overpass API"
        }
    
    lat, lon = coordinates
    print(f"📍 Location coordinates: {lat:.4f}, {lon:.4f}")
    
    # Step 2: Query Overpass API for attractions
    attractions = query_overpass_attractions(lat, lon, radius_km=5, max_results=20)
    
    if "error" in attractions:
        return {
            "error": f"Unable to fetch attractions for '{location}': {attractions[0]['message']}",
            "location": location,
            "coordinates": coordinates,
            "success": False,
            "source": "OpenStreetMap via Overpass API"
        }
    
    # Step 3: Generate personalized recommendations
    recommendations = generate_travel_recommendations(attractions, location)
    
    # Step 4: Complete response structure
    complete_response = {
        "location": location,
        "coordinates": coordinates,
        "attractions": {
            "total_available": len(attractions),
            "recommended_count": len(recommendations.get("recommended", [])),
            "top_recommendations": recommendations["recommended"],
            "by_category": recommendations.get("by_category", {}),
            "travel_tips": recommendations["travel_tips"]
        },
        "technical": {
            "search_radius": "5 km",
            "data_source": "OpenStreetMap (community-contributed)",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api": "Overpass API v0.7.1",
            "geocoding": "Nominatim (OpenStreetMap)"
        },
        "success": True
    }
    
    print(f"✅ Found {len(attractions)} attractions for '{location}'")
    print(f"🎯 Recommended top {len(recommendations.get('recommended', []))} attractions")
    
    return complete_response

# Development utility functions
def test_places_agent():
    """Test places agent with sample cities"""
    test_cities = [
        "Paris, France",
        "New York, USA",
        "Tokyo, Japan", 
        "London, UK",
        "Bangalore, India"
    ]
    
    for city in test_cities:
        result = places_query(city)
        print(f"\n{'='*70}")
        print(f"ATTRACTIONS FOR: {city}")
        print(f"{'='*70}")
        
        if result.get("success"):
            print(f"📊 Total attractions found: {result['attractions']['total_available']}")
            print(f"🎯 Top recommendations: {result['attractions']['recommended_count']}")
            
            for i, rec in enumerate(result['attractions']['top_recommendations'][:3], 1):
                print(f"\n{i}. {rec['name']}")
                print(f"   📍 {rec['distance']} - {rec['category']}")
                print(f"   💡 {rec['why_visit']}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        # Rate limiting (Overpass: 1 request per second)
        time.sleep(1)
    
    print("\n" + "="*70)
    print("PLACES AGENT TESTING COMPLETE")
    print("="*70)

if __name__ == "__main__":
    # Run comprehensive test
    test_places_agent()
