# network_monitor.py - Use this to find API calls
import browser_cookie3
import json

def get_browser_cookies():
    """Extract cookies from browser for authentication"""
    try:
        # Try Chrome first
        cookies = browser_cookie3.chrome(domain_name='bizbuysell.com')
        cookie_dict = {cookie.name: cookie.value for cookie in cookies}
        print(f"Found {len(cookie_dict)} cookies from Chrome")
        return cookie_dict
    except:
        try:
            # Try Firefox
            cookies = browser_cookie3.firefox(domain_name='bizbuysell.com')
            cookie_dict = {cookie.name: cookie.value for cookie in cookies}
            print(f"Found {len(cookie_dict)} cookies from Firefox")
            return cookie_dict
        except:
            print("Could not extract browser cookies")
            return {}

def analyze_network_traffic():
    """
    Instructions for manual API discovery:
    1. Open Chrome DevTools (F12)
    2. Go to Network tab
    3. Filter by XHR or Fetch
    4. Browse the site normally
    5. Look for JSON responses
    6. Copy as cURL command
    """
    
    instructions = """
    MANUAL API DISCOVERY STEPS:
    ---------------------------
    1. Open https://www.bizbuysell.com in Chrome
    2. Press F12 to open DevTools
    3. Go to Network tab
    4. Check 'Preserve log' checkbox
    5. Filter by XHR or Fetch
    6. Perform a search on the website
    7. Look for requests that return JSON data
    8. Right-click on the request → Copy → Copy as cURL
    9. Use the cURL command below to create Python code
    """
    
    print(instructions)

# Example cURL to Python converter
def curl_to_python(curl_command: str):
    """Convert cURL command to Python requests code"""
    import re
    
    # Parse headers
    headers = {}
    header_pattern = r"-H '([^:]+): ([^']+)'"
    headers_match = re.findall(header_pattern, curl_command)
    
    for name, value in headers_match:
        headers[name.strip()] = value.strip()
    
    # Parse URL
    url_pattern = r"curl ['\"]?([^ '\"]+)['\"]?"
    url_match = re.search(url_pattern, curl_command)
    
    if url_match:
        url = url_match.group(1)
        print(f"\nURL: {url}")
        print("\nHeaders:", json.dumps(headers, indent=2))
        
        # Generate Python code
        python_code = f'''
import requests

headers = {headers}

response = requests.get(
    "{url}",
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Success! Retrieved {{len(data)}} items")
else:
    print(f"Error: {{response.status_code}}")
        '''
        
        print("\nGenerated Python code:")
        print(python_code)
        
        return url, headers
    
    return None, None

# Run the analysis
if __name__ == "__main__":
    analyze_network_traffic()
    
    # Example cURL command (replace with one you find)
    example_curl = """curl 'https://api.bizbuysell.com/v1/listings?location=California&page=1' \
  -H 'authority: www.bizbuysell.com' \
  -H 'accept: application/json' \
  -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' \
  --compressed"""
    
    print("\nExample conversion:")
    curl_to_python(example_curl)