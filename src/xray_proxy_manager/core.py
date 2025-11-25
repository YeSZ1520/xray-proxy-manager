import os
import stat
import zipfile
import requests
import glob
from loguru import logger

class CoreManager:
    def __init__(self, static_dir):
        self.static_dir = static_dir
        self.xray_path = os.path.join(static_dir, "xray")

    def ensure_installed(self):
        if os.path.exists(self.xray_path):
            return True
        
        if not os.path.exists(self.static_dir):
            os.makedirs(self.static_dir)

        # Prioritize checking for local Xray*.zip
        local_zips = glob.glob(os.path.join(self.static_dir, "Xray*.zip"))
        zip_path = local_zips[0] if local_zips else os.path.join(self.static_dir, "xray.zip")
        downloaded = False

        if local_zips:
            logger.info(f"Found local core package: {zip_path}, preparing to unzip...")
        else:
            logger.info("Downloading Xray-core...")
            url = "https://gh-proxy.org/https://github.com/XTLS/Xray-core/releases/download/v1.8.4/Xray-linux-64.zip"
            try:
                with requests.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(zip_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                downloaded = True
            except Exception as e:
                logger.error(f"Core download failed: {e}")
                return False
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(self.static_dir)
                
            # Grant execution permissions
            if os.path.exists(self.xray_path):
                st = os.stat(self.xray_path)
                os.chmod(self.xray_path, st.st_mode | stat.S_IEXEC)
            else:
                logger.error("Xray executable not found after extraction")
                return False
            
            # Only delete downloaded file
            if downloaded and os.path.exists(zip_path):
                os.remove(zip_path)
                
            return True
        except Exception as e:
            logger.error(f"Core installation failed: {e}")
            return False
