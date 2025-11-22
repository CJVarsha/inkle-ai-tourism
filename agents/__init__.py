"""
Inkle.ai Multi-Agent Tourism Intelligence System
================================================
Assignment: Build multi-agent tourism recommendation system

ARCHITECTURE:
├── PARENT AGENT: Tourism Orchestrator (LangChain ReAct)
│   ├── Coordinates user queries to appropriate child agents
│   ├── Combines weather + places data into travel recommendations
│   └── Handles errors (unknown locations, API failures)
│
├── CHILD AGENT 1: Weather Specialist (Open-Meteo API)
│   ├── Real-time weather forecasts for any location worldwide
│   ├── Temperature, precipitation, wind conditions
│   └── Automatic timezone handling
│
└── CHILD AGENT 2: Places Curator (Overpass API + Nominatim)
    ├── Tourist attractions within 5km radius of location
    ├── Global coverage (OpenStreetMap data)
    └── Up to 5 recommendations per location

TECHNOLOGIES:
- LangChain ReAct Agent for orchestration
- OpenAI GPT-4o-mini for natural language processing
- Open-Meteo API for accurate weather data
- Overpass API for authentic tourism data (no hallucinations)
- Streamlit for professional web interface
- Geopy/Nominatim for precise geocoding

SECURITY:
- API keys stored in .env (never committed to GitHub)
- Rate limiting and error handling for all external APIs
- Graceful degradation for network failures

DEPLOYMENT:
- Streamlit Cloud for live demonstration
- Professional documentation and error reporting
"""

# Import all agents for easy access
from .weather_agent import weather_query
from .places_agent import places_query
from .orchestrator import orchestrate_tourism_query

__all__ = ["weather_query", "places_query", "orchestrate_tourism_query"]

# Version info for your portfolio
__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Multi-agent tourism system for Inkle.ai internship"
