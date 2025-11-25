import os
import json
import time
import subprocess
import requests
import concurrent.futures
from contextlib import contextmanager
from loguru import logger
from .core import CoreManager
from .config import ConfigGenerator
from .subscription import fetch_nodes

class XrayProxyManager:
    def __init__(self, sub_url=None, static_path=None):
        self.sub_url = sub_url
        self.nodes = []
        
        if static_path:
            self.static_dir = os.path.abspath(static_path)
        else:
            self.static_dir = os.path.join(os.path.expanduser("~"), ".xray_proxy_manager")
            
        self.core = CoreManager(self.static_dir)
        self.process = None
        self.local_http = 10809
        self.local_socks = 10808

    def get_nodes(self):
        if not self.nodes and self.sub_url:
            self.nodes = fetch_nodes(self.sub_url)
        return self.nodes

    def _run_process(self, config_data):
        self.core.ensure_installed()
            
        env = os.environ.copy()
        env["XRAY_LOCATION_ASSET"] = self.static_dir
        
        self.process = subprocess.Popen(
            [self.core.xray_path, "-c", "stdin:"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
        
        try:
            self.process.stdin.write(json.dumps(config_data).encode('utf-8'))
            self.process.stdin.close()
        except Exception:
            pass

        time.sleep(1) # Wait for startup
        if self.process.poll() is not None:
            raise RuntimeError("Xray failed to start")

    def _stop_process(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def find_fastest(self, test_url="https://www.google.com", timeout=2):
        nodes = self.get_nodes()
        if not nodes:
            raise ValueError("No available nodes")
            
        logger.info(f"Starting speed test (Benchmark: {test_url}, Timeout: {timeout}s)...")
        
        config, base_port = ConfigGenerator.generate_multi(nodes)
        
        try:
            self._run_process(config)
            
            def check(i):
                port = base_port + i
                proxies = {"http": f"http://127.0.0.1:{port}", "https": f"http://127.0.0.1:{port}"}
                start = time.time()
                try:
                    requests.get(test_url, proxies=proxies, timeout=timeout)
                    return i, (time.time() - start) * 1000
                except:
                    return i, float('inf')

            best_idx = -1
            min_latency = float('inf')
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(check, i) for i in range(len(nodes))]
                for f in concurrent.futures.as_completed(futures):
                    idx, lat = f.result()
                    if lat < min_latency:
                        min_latency = lat
                        best_idx = idx
                        
            if best_idx != -1:
                node = nodes[best_idx]
                logger.success(f"Fastest node: {node.get('ps')} ({min_latency:.0f}ms)")
                return node
            else:
                logger.warning("All nodes failed speed test")
                return None
                
        finally:
            self._stop_process()

    @contextmanager
    def start(self, node):
        """Start proxy for a specific node"""
        try:
            config = ConfigGenerator.generate_single(node, self.local_http, self.local_socks)
            self._run_process(config)
            yield {
                "http": f"http://127.0.0.1:{self.local_http}",
                "https": f"http://127.0.0.1:{self.local_http}",
                "socks5": f"socks5://127.0.0.1:{self.local_socks}"
            }
        finally:
            self._stop_process()

    @contextmanager
    def start_fastest(self, test_url="https://www.google.com", timeout=2):
        """Automatically find the fastest node and start the proxy"""
        node = self.find_fastest(test_url, timeout)
        if not node:
            raise RuntimeError("Unable to find available node")
        
        with self.start(node) as proxies:
            yield proxies
