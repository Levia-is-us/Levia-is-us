import sys
import requests


def get_current_location(ip_address: str = None) -> dict:
    """Get location information for a specific IP address"""
    try:
        print("Getting location information...", file=sys.stderr)

        # Set request headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Use HTTPS protocol with specific IP if provided
        url = (
            f"https://ipapi.co/{ip_address}/json/"
            if ip_address
            else "https://ipapi.co/json/"
        )
        response = requests.get(url, headers=headers, timeout=10)  # Use ipapi.co API

        if not response.ok:
            return {"error": f"Failed to get location: {response.status_code}"}

        location_data = response.json()
        print(f"API response data: {location_data}", file=sys.stderr)

        if "error" not in location_data:
            result = {
                "country": location_data.get("country_name", "Unknown"),
                "city": location_data.get("city", "Unknown"),
                "region": location_data.get("region", "Unknown"),
                "address": f"{location_data.get('city', 'Unknown')}, {location_data.get('region', 'Unknown')}, {location_data.get('country_name', 'Unknown')}",
            }
            print(f"Successfully got location info: {result}", file=sys.stderr)
            return result
        else:
            error_msg = f'Location service returned error: {location_data.get("error", "Unknown error")}'
            print(f"Error: {error_msg}", file=sys.stderr)
            return {"error": error_msg}

    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Network request error: {str(e)}"}
    except Exception as e:
        return {"error": f"Error getting location: {str(e)}"}
