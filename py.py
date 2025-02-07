import tkinter as tk
from tkinter import ttk, messagebox
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import folium
import webbrowser
import os
import sqlite3
from datetime import datetime
import requests
from typing import Tuple, List, Optional, Dict
import json

# -------------------- Database Operations -------------------- #
class GeolocationDatabase:
    """Handles all database operations for the geolocation app."""
    
    def __init__(self):
        self.conn = sqlite3.connect('geolocation_history.db')
        self.create_tables()
    
    def create_tables(self):
        """Creates the necessary database tables if they don't exist."""
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    result TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def add_search(self, query: str, result: str):
        """Adds a new search record to the history."""
        with self.conn:
            self.conn.execute(
                'INSERT INTO search_history (query, result) VALUES (?, ?)',
                (query, result)
            )
    
    def get_recent_searches(self, limit: int = 5) -> List[tuple]:
        """Retrieves the most recent searches from the database."""
        cursor = self.conn.execute(
            'SELECT query, result, timestamp FROM search_history ORDER BY timestamp DESC LIMIT ?',
            (limit,)
        )
        return cursor.fetchall()

# -------------------- Geolocation Service -------------------- #
class GeolocationService:
    """Provides core geolocation functionality including geocoding and distance calculations."""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="my_geolocation_app")
        self.db = GeolocationDatabase()
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Converts an address into geographic coordinates."""
        try:
            location = self.geolocator.geocode(address)
            if location:
                self.db.add_search(address, f"{location.latitude}, {location.longitude}")
                return (location.latitude, location.longitude)
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            raise Exception(f"Geocoding error: {str(e)}")
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Converts geographic coordinates into an address."""
        try:
            location = self.geolocator.reverse((lat, lon))
            if location:
                self.db.add_search(f"{lat}, {lon}", location.address)
                return location.address
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            raise Exception(f"Reverse geocoding error: {str(e)}")
    
    def calculate_distance(self, coords1: Tuple[float, float], coords2: Tuple[float, float]) -> float:
        """Calculates the distance between two points (in kilometers)."""
        return geodesic(coords1, coords2).kilometers
    
    def get_nearby_pois(self, lat: float, lon: float, radius: int = 1000) -> List[Dict]:
        """Retrieves nearby points of interest using OpenStreetMap's Overpass API."""
        overpass_url = "http://overpass-api.de/api/interpreter"
        query = f"""
        [out:json];
        (
          node["amenity"](around:{radius},{lat},{lon});
          way["amenity"](around:{radius},{lat},{lon});
          relation["amenity"](around:{radius},{lat},{lon});
        );
        out center;
        """
        try:
            response = requests.post(overpass_url, data=query)
            data = response.json()
            return [
                {
                    'type': element.get('tags', {}).get('amenity', 'unknown'),
                    'name': element.get('tags', {}).get('name', 'unnamed'),
                    'lat': element.get('lat', element.get('center', {}).get('lat')),
                    'lon': element.get('lon', element.get('center', {}).get('lon'))
                }
                for element in data.get('elements', [])
                if element.get('tags', {}).get('name')
            ]
        except Exception as e:
            print(f"Error fetching POIs: {str(e)}")
            return []

# -------------------- Map Visualization -------------------- #
class MapVisualizer:
    """Creates and visualizes maps using Folium."""
    
    @staticmethod
    def create_map(lat: float, lon: float, pois: List[Dict] = None) -> str:
        """Creates an interactive map for the given location and points of interest."""
        m = folium.Map(location=[lat, lon], zoom_start=15)
        
        # Add marker for the main location
        folium.Marker(
            [lat, lon],
            popup="Selected Location",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
        # Add markers for nearby POIs if provided
        if pois:
            for poi in pois:
                if poi.get('lat') and poi.get('lon'):
                    folium.Marker(
                        [poi['lat'], poi['lon']],
                        popup=f"{poi['name']} ({poi['type']})",
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)
        
        # Save map to a temporary HTML file
        map_file = "temp_map.html"
        m.save(map_file)
        return map_file

# -------------------- Application GUI -------------------- #
class GeolocationApp(tk.Tk):
    """Main application window and UI implementation."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Geolocation Application")
        self.geometry("800x600")
        self.configure(bg="#B3E5FC")  # Set background to a light blue tone
        
        # Configure ttk styles
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#B3E5FC")
        style.configure("TLabel", background="#B3E5FC", font=("Helvetica", 12))
        style.configure("TButton", background="#0288D1", foreground="white", font=("Helvetica", 10, "bold"))
        style.configure("TNotebook", background="#B3E5FC")
        style.configure("TNotebook.Tab", background="#0288D1", foreground="white", font=("Helvetica", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#01579B")])
        # When a button is hovered (active), change its text color to black
        style.map("TButton", foreground=[("active", "black"), ("!active", "white")])
        
        self.geo_service = GeolocationService()
        self.setup_ui()
    
    def setup_ui(self):
        """Sets up the UI components."""
        # Create a notebook (tabbed interface)
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        geocoding_frame = self.create_geocoding_frame()
        distance_frame = self.create_distance_frame()
        history_frame = self.create_history_frame()
        
        notebook.add(geocoding_frame, text="Geocoding")
        notebook.add(distance_frame, text="Distance Calculator")
        notebook.add(history_frame, text="Search History")
    
    def create_geocoding_frame(self) -> ttk.Frame:
        """Creates the geocoding tab interface."""
        frame = ttk.Frame(self)
        
        # Address or coordinates entry
        ttk.Label(frame, text="Enter address or coordinates:").pack(pady=5)
        self.address_entry = ttk.Entry(frame, width=50)
        self.address_entry.pack(pady=5)
        
        # Frame for buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Geocode",
            command=self.handle_geocoding
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Reverse Geocode",
            command=self.handle_reverse_geocoding
        ).pack(side='left', padx=5)
        
        ttk.Button(
            button_frame,
            text="Show on Map",
            command=self.show_map
        ).pack(side='left', padx=5)
        
        # Text widget to display results with a custom background and font
        self.result_text = tk.Text(frame, height=10, width=50, bg="#E1F5FE", fg="black", font=("Helvetica", 11))
        self.result_text.pack(pady=10)
        
        return frame
    
    def create_distance_frame(self) -> ttk.Frame:
        """Creates the distance calculator tab interface."""
        frame = ttk.Frame(self)
        
        # First location entry
        ttk.Label(frame, text="First Location:").pack(pady=5)
        self.loc1_entry = ttk.Entry(frame, width=50)
        self.loc1_entry.pack(pady=5)
        
        # Second location entry
        ttk.Label(frame, text="Second Location:").pack(pady=5)
        self.loc2_entry = ttk.Entry(frame, width=50)
        self.loc2_entry.pack(pady=5)
        
        # Calculate distance button
        ttk.Button(
            frame,
            text="Calculate Distance",
            command=self.calculate_distance
        ).pack(pady=10)
        
        # Label to display the calculated distance
        self.distance_result = ttk.Label(frame, text="", font=("Helvetica", 12, "bold"))
        self.distance_result.pack(pady=10)
        
        return frame
    
    def create_history_frame(self) -> ttk.Frame:
        """Creates the search history tab interface."""
        frame = ttk.Frame(self)
        
        # Text widget to display search history
        self.history_text = tk.Text(frame, height=20, width=50, bg="#E1F5FE", fg="black", font=("Helvetica", 11))
        self.history_text.pack(pady=10)
        
        # Refresh history button
        ttk.Button(
            frame,
            text="Refresh History",
            command=self.refresh_history
        ).pack(pady=5)
        
        return frame
    
    def handle_geocoding(self):
        """Handles the Geocode button click."""
        address = self.address_entry.get().strip()
        try:
            coords = self.geo_service.geocode(address)
            if coords:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(
                    tk.END,
                    f"Coordinates: {coords[0]}, {coords[1]}\n"
                )
            else:
                messagebox.showerror("Error", "Location not found")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def handle_reverse_geocoding(self):
        """Handles the Reverse Geocode button click."""
        try:
            coords = self.address_entry.get().strip().split(',')
            if len(coords) != 2:
                raise ValueError("Invalid coordinate format. Please use 'latitude,longitude'")
            
            lat, lon = float(coords[0]), float(coords[1])
            address = self.geo_service.reverse_geocode(lat, lon)
            
            if address:
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(tk.END, f"Address: {address}\n")
            else:
                messagebox.showerror("Error", "Address not found")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def show_map(self):
        """Handles the Show on Map button click."""
        try:
            # First, try to geocode the input
            address = self.address_entry.get().strip()
            coords = self.geo_service.geocode(address)
            
            if coords:
                # Retrieve nearby points of interest
                pois = self.geo_service.get_nearby_pois(coords[0], coords[1])
                
                # Create and display the map
                map_file = MapVisualizer.create_map(coords[0], coords[1], pois)
                webbrowser.open('file://' + os.path.realpath(map_file))
            else:
                messagebox.showerror("Error", "Location not found")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def calculate_distance(self):
        """Handles the Calculate Distance button click."""
        try:
            # Geocode both locations
            coords1 = self.geo_service.geocode(self.loc1_entry.get().strip())
            coords2 = self.geo_service.geocode(self.loc2_entry.get().strip())
            
            if coords1 and coords2:
                distance = self.geo_service.calculate_distance(coords1, coords2)
                self.distance_result.config(
                    text=f"Distance: {distance:.2f} km"
                )
            else:
                messagebox.showerror("Error", "One or both locations not found")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def refresh_history(self):
        """Refreshes and displays the search history."""
        try:
            searches = self.geo_service.db.get_recent_searches()
            self.history_text.delete(1.0, tk.END)
            for query, result, timestamp in searches:
                self.history_text.insert(
                    tk.END,
                    f"Query: {query}\nResult: {result}\nTime: {timestamp}\n\n"
                )
        except Exception as e:
            messagebox.showerror("Error", f"Error loading history: {str(e)}")

def main():
    """Application entry point."""
    app = GeolocationApp()
    app.mainloop()

if __name__ == "__main__":
    main()
