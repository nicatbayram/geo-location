# Geolocation App

## Description
The **Geolocation App** is a Python-based desktop application that allows users to retrieve and display geographical coordinates (latitude and longitude) of a given location. It also provides functionalities to visualize locations on an interactive map and store searched locations in an SQLite database.

## Features
- **Retrieve Location Coordinates:** Get latitude and longitude of any given place.
- **Interactive Map Visualization:** Display searched locations on an interactive map using **Folium**.
- **Database Storage:** Save searched locations in an **SQLite** database for future reference.
- **User-Friendly GUI:** Built with **Tkinter** for a simple and intuitive user experience.

## Technologies Used
- **Python 3.x**
- **Tkinter** (GUI development)
- **Geopy** (Geolocation services)
- **Folium** (Map visualization)
- **SQLite3** (Database management)

## Installation
### Prerequisites
Ensure you have Python installed on your system. You can install the required dependencies using:
```sh
pip install geopy folium sqlite3
```

### Running the Application
1. Clone this repository:
```sh
git clone https://github.com/nicatbayram/geo-location.git
cd geolocation-app
```
2. Run the application:
```sh
python app.py
```

## Usage
1. Enter a location name in the input field.
2. Click the **Search** button to retrieve the latitude and longitude.
3. Click **Show on Map** to visualize the location.
4. The searched location will be saved in the database for later use.

## Future Improvements
- Add support for multiple geolocation providers.
- Implement a feature to export locations as CSV or JSON.
- Enhance UI/UX with additional styling.

## ScreenShots

https://github.com/user-attachments/assets/1210ea98-31f2-4056-9f3d-657376798de9
