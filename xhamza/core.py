import re
import json
import argparse
import sys
import random
from curl_cffi import requests as cffi_requests

class ExtractionError(Exception):
    pass

def extract_video(page_url):
    stream_url = None
    mp4_url = None

    # Generate a random IP to spoof the X-Forwarded-For header just like your Flask app did
    fake_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "X-Forwarded-For": fake_ip,
        "X-Real-IP": fake_ip
    }

    try:
        resp = cffi_requests.get(page_url, impersonate="chrome120", headers=headers, timeout=15)
        
        # DEBUGGING: If the site blocks you, this will tell you exactly why!
        if resp.status_code != 200:
            raise ExtractionError(f"HTTP Error {resp.status_code}: The website blocked the request. If running in Colab, the Google IP is likely banned.")

        html = resp.text

        data = {}
        json_match = re.search(r'window\.initials\s*=\s*({.+?});\s*</script>', html, re.DOTALL)
        if json_match:
            try: data = json.loads(json_match.group(1))
            except: pass

        if data:
            sources = data.get("videoModel", {}).get("sources", {})
            
            if "mp4" in sources:
                mp4_data = sources["mp4"]
                if isinstance(mp4_data, dict):
                    if "url" in mp4_data: mp4_url = mp4_data["url"]
                    else:
                        for key, val in mp4_data.items():
                            if isinstance(val, dict) and "url" in val:
                                mp4_url = val["url"]
                                break
                elif isinstance(mp4_data, str): mp4_url = mp4_data
            
            if "hls" in sources: stream_url = sources["hls"].get("url")

        if not stream_url and not mp4_url:
            m3u8_matches = re.findall(r'https?:\/\/[^\s<>"\'\\]+\.m3u8[^\s<>"\'\\]*', html)
            if m3u8_matches:
                valid = [m.replace('\\/', '/') for m in m3u8_matches if 'tsyndicate' not in m]
                if valid: stream_url = valid[0]

        if not stream_url and not mp4_url:
            raise ExtractionError("Could not extract link. The page loaded, but the JSON data was missing.")

        return {
            "m3u8": stream_url,
            "mp4": mp4_url
        }

    except Exception as e:
        raise ExtractionError(f"Error during extraction: {str(e)}")

# ... (Keep your main() function below this exactly the same)
