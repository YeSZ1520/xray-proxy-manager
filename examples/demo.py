import requests
from loguru import logger
from xray_proxy_manager import XrayProxyManager

# Configuration
SUB_URL = "https://example.com/your_subscription_link"

def main():
    # Initialize manager
    # By default, core files are downloaded to ~/.xray_proxy_manager
    # You can also specify a custom path via the static_path parameter, for example:
    # manager = XrayProxyManager(SUB_URL, static_path="./xray_core")
    manager = XrayProxyManager(SUB_URL)

    # Method 1: Automatically test speed and use the fastest node (Recommended)
    logger.info("Finding the fastest node and starting proxy...")
    try:
        with manager.start_fastest(test_url="https://github.com", timeout=2) as proxies:
            logger.info(f"Proxy ready: {proxies}")
            
            logger.info("Accessing ipinfo.io ...")
            resp = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)
            logger.success(f"Success: {resp.json()}")
            
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
