import openrouteservice
import traceback
from .config import ORS_API_KEY

# Initialize the client with your API key
client = openrouteservice.Client(key=ORS_API_KEY)

def get_route(coordinates: list):
    """
    Get route information from openrouteservice.

    :param coordinates: A list of [longitude, latitude] pairs.
    :return: The route object from the API response.
    """
    # Note: openrouteservice expects coordinates in (longitude, latitude) format.
    # Ensure the coordinates passed to this function are in the correct order.
    
    try:
        routes = client.directions(
            coordinates=coordinates,
            profile='driving-car',
            format='json',
            validate=False, # Set to False to improve performance, as we trust our data
            geometry=True, # We need the geometry to draw the route on the map
        )
        return routes
    except openrouteservice.exceptions.ApiError as e:
        # Handle API errors (e.g., invalid key, quota exceeded)
        print(f"ORS API Error: {e}")
        return None
    except Exception as e:
        # Handle other potential errors (e.g., network issues)
        print(f"An unexpected error occurred: {e}")
        return None


def geocode(address: str, focus_point: tuple = None):
    """
    Convert an address string to coordinates using openrouteservice geocoding.

    :param address: The address string to geocode.
    :param focus_point: A (longitude, latitude) tuple to focus the search.
    :return: A tuple of (longitude, latitude) or None if not found.
    """
    try:
        search_params = {
            'text': address,
            'size': 1
        }
        if focus_point:
            # Pass the focus_point tuple directly as a parameter.
            search_params['focus_point'] = focus_point

        geocode_result = client.pelias_search(**search_params)
        
        if geocode_result and 'features' in geocode_result and geocode_result['features']:
            # Extract coordinates from the first feature
            # The coordinates are in [longitude, latitude] format
            coords = geocode_result['features'][0]['geometry']['coordinates']
            return tuple(coords)
        else:
            return None
    except openrouteservice.exceptions.ApiError as e:
        print(f"ORS Geocoding API Error - Status: {e.status_code}, Message: {e.message}")
        return None
    except Exception as e:
        print("An unexpected error occurred during geocoding. Full traceback:")
        traceback.print_exc()
        return None


def get_distance_matrix(coordinates: list):
    """
    Get a distance matrix from openrouteservice.

    :param coordinates: A list of [longitude, latitude] pairs.
    :return: The distance matrix from the API response.
    """
    try:
        matrix = client.distance_matrix(
            locations=coordinates,
            metrics=['distance'],
            units='km' # Get distance in kilometers
        )
        return matrix
    except openrouteservice.exceptions.ApiError as e:
        print(f"ORS Matrix API Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during matrix calculation: {e}")
        return None


def autocomplete(text: str):
    """
    Get address suggestions from openrouteservice autocomplete API.

    :param text: The partial address string.
    :return: A list of suggestions or None.
    """
    try:
        # Use pelias_autocomplete for suggestions
        suggestions = client.pelias_autocomplete(
            text=text
        )
        
        if suggestions and 'features' in suggestions:
            # Format the results for easier use in the frontend
            return [
                {
                    "label": feature['properties']['label'],
                    "coordinates": feature['geometry']['coordinates']
                }
                for feature in suggestions['features']
            ]
        else:
            return []
    except openrouteservice.exceptions.ApiError as e:
        print(f"ORS Autocomplete API Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during autocomplete: {e}")
        return None
