import re
import json
import argparse
import sys
from curl_cffi import requests as cffi_requests

class ExtractionError(Exception):
    """Custom exception for extraction failures."""
    pass

def extract_video(page_url):
    """
    Takes a video URL, scrapes the page, and returns a dictionary 
    with the direct 'mp4' and 'm3u8' (hls) links.
    """
    stream_url = None
    mp4_url = None

    try:
        # Impersonate Chrome to bypass basic bot protections
        resp = cffi_requests.get(page_url, impersonate="chrome120", timeout=15)
        html = resp.text

        data = {}
        # 1. Look for the JSON payload in the script tags
        json_match = re.search(r'window\.initials\s*=\s*({.+?});\s*</script>', html, re.DOTALL)
        if json_match:
            try: 
                data = json.loads(json_match.group(1))
            except json.JSONDecodeError: 
                pass

        if data:
            sources = data.get("videoModel", {}).get("sources", {})
            
            # Extract MP4
            if "mp4" in sources:
                mp4_data = sources["mp4"]
                if isinstance(mp4_data, dict):
                    if "url" in mp4_data: 
                        mp4_url = mp4_data["url"]
                    else:
                        for key, val in mp4_data.items():
                            if isinstance(val, dict) and "url" in val:
                                mp4_url = val["url"]
                                break
                elif isinstance(mp4_data, str): 
                    mp4_url = mp4_data
            
            # Extract HLS (.m3u8)
            if "hls" in sources: 
                stream_url = sources["hls"].get("url")

        # 2. Regex Fallback for .m3u8
        if not stream_url and not mp4_url:
            m3u8_matches = re.findall(r'https?:\/\/[^\s<>"\'\\]+\.m3u8[^\s<>"\'\\]*', html)
            if m3u8_matches:
                valid = [m.replace('\\/', '/') for m in m3u8_matches if 'tsyndicate' not in m]
                if valid: stream_url = valid[0]

        if not stream_url and not mp4_url:
            raise ExtractionError("Could not extract link. Video might be strictly premium-locked.")

        return {
            "m3u8": stream_url,
            "mp4": mp4_url
        }

    except Exception as e:
        raise ExtractionError(f"Error during extraction: {str(e)}")


def main():
    """Command Line Interface entry point."""
    parser = argparse.ArgumentParser(description="Extract raw MP4 and m3u8 links from a video URL.")
    parser.add_argument("url", help="The URL of the video page")
    parser.add_argument("--format", choices=["m3u8", "mp4", "all"], default="m3u8", 
                        help="Specify which link to output (default: m3u8)")
    
    args = parser.parse_args()

    try:
        links = extract_video(args.url)
        
        if args.format == "all":
            print(json.dumps(links, indent=2))
        elif args.format == "m3u8" and links["m3u8"]:
            print(links["m3u8"])
        elif args.format == "mp4" and links["mp4"]:
            print(links["mp4"])
        else:
            print(f"Error: {args.format} link not found for this video.", file=sys.stderr)
            sys.exit(1)
            
    except ExtractionError as e:
        print(f"Failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
