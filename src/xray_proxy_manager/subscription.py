import requests
import base64
import json
from loguru import logger

def parse_vmess(vmess_url):
    if not vmess_url.startswith("vmess://"):
        return None
    try:
        b64 = vmess_url[8:]
        padding = len(b64) % 4
        if padding > 0:
            b64 += "=" * (4 - padding)
        json_str = base64.b64decode(b64).decode('utf-8')
        return json.loads(json_str)
    except Exception:
        return None

def fetch_nodes(url):
    logger.info(f"Downloading subscription: {url}...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        
        content = resp.text.strip()
        try:
            decoded = base64.b64decode(content).decode('utf-8')
        except Exception:
            decoded = content

        nodes = []
        for line in decoded.splitlines():
            line = line.strip()
            if line.startswith("vmess://"):
                info = parse_vmess(line)
                if info:
                    nodes.append(info)
        logger.info(f"Parsed {len(nodes)} nodes")
        return nodes
    except Exception as e:
        logger.error(f"Subscription parsing failed: {e}")
        return []
