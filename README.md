# Xray Proxy Manager

A simple Python proxy module that supports the Vmess protocol. It automatically manages the V2Ray/Xray core process, eliminating the need for users to manually install or configure external proxy software.

## Workflow Overview

1.  **Initialization**: The user provides a subscription URL and optionally a path for static files.
2.  **Core Management**: The module checks if the Xray core is present in the specified (or default) directory. If not, it automatically downloads and unzips the appropriate version for the platform.
3.  **Subscription Parsing**: It fetches the subscription URL, decodes the content, and parses the Vmess nodes.
4.  **Latency Testing**: It generates a multi-port configuration to test all nodes concurrently against a target URL (e.g., Google) to find the fastest node.
5.  **Proxy Execution**: Once the best node is selected, it generates a specific configuration for that node and starts the Xray core process.
6.  **Context Management**: The proxy runs within a context manager, ensuring the process is cleanly terminated when the block exits.

## Directory Structure

```text
xray-proxy-manager/
├── src/
│   └── xray_proxy_manager/       # Core package
│       ├── __init__.py
│       ├── manager.py    # Core process management
│       ├── core.py       # Xray core download and management
│       ├── subscription.py # Subscription parsing
│       ├── config.py     # Configuration generation
│       └── static/       # Directory for automatically downloaded xray core and config files
├── examples/
│   └── demo.py           # Demo script
├── pyproject.toml        # Project configuration
└── README.md
```

## Installation

```bash
pip install .
```

Or

```bash
pip install xray-proxy-manager
```

## Quick Start

### 1. Import Module

```python
from xray_proxy_manager import XrayProxyManager
```

### 2. Initialize and Use

```python
import requests
from loguru import logger
from xray_proxy_manager import XrayProxyManager

# Your subscription URL
SUB_URL = "https://example.com/subscribe"

def main():
    # Initialize manager
    # By default, core files are downloaded to ~/.xray_proxy_manager
    manager = XrayProxyManager(SUB_URL)
    
    # Or specify a custom path
    # manager = XrayProxyManager(SUB_URL, static_path="./my_xray_core")

    # Method 1: Automatically test speed and use the fastest node (Recommended)
    logger.info("Finding the fastest node and starting proxy...")
    try:
        # start_fastest will automatically download core, parse subscription, test speed, and start proxy
        with manager.start_fastest(test_url="https://www.google.com", timeout=2) as proxies:
            logger.info(f"Proxy ready: {proxies}")
            
            logger.info("Accessing ipinfo.io ...")
            resp = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)
            logger.success(f"Success: {resp.json()}")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
```

## Notes

- This project automatically downloads the Xray core file. The default storage path is `~/.xray_proxy_manager`.
- You can specify a custom storage path via the `static_path` parameter during initialization.
- Only supports Vmess protocol subscriptions.
