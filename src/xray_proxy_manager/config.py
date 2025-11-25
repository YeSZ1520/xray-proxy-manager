class ConfigGenerator:
    @staticmethod
    def _build_vmess_settings(node):
        """Build Vmess protocol core configuration"""
        return {
            "vnext": [{
                "address": node.get("add"),
                "port": int(node.get("port", 443)),
                "users": [{
                    "id": node.get("id"),
                    "alterId": int(node.get("aid", 0)),
                    "security": "auto"
                }]
            }]
        }

    @staticmethod
    def _build_stream_settings(node):
        """Build underlying transport configuration (TCP/WS/TLS)"""
        net = node.get("net", "tcp")
        security = node.get("tls", "none")
        
        settings = {
            "network": net,
            "security": security
        }

        # Transport layer configuration
        if net == "ws":
            settings["wsSettings"] = {
                "path": node.get("path", "/"),
                "headers": {"Host": node.get("host", "")}
            }
        elif net == "tcp" and node.get("type") == "http":
            settings["tcpSettings"] = {
                "header": {
                    "type": "http",
                    "request": {"headers": {"Host": [node.get("host", "")]}}
                }
            }

        # Security layer configuration
        if security == "tls":
            settings["tlsSettings"] = {
                "serverName": node.get("host") or node.get("add"),
                "allowInsecure": True
            }
            
        return settings

    @staticmethod
    def _build_outbound(node, tag=None):
        """Assemble complete Outbound object"""
        outbound = {
            "protocol": "vmess",
            "settings": ConfigGenerator._build_vmess_settings(node),
            "streamSettings": ConfigGenerator._build_stream_settings(node)
        }
        if tag:
            outbound["tag"] = tag
        return outbound

    @staticmethod
    def generate_single(node, http_port, socks_port):
        """Generate single node proxy configuration"""
        return {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {"port": socks_port, "protocol": "socks", "settings": {"auth": "noauth", "udp": True}},
                {"port": http_port, "protocol": "http", "settings": {}}
            ],
            "outbounds": [ConfigGenerator._build_outbound(node)]
        }

    @staticmethod
    def generate_multi(nodes, start_port=20000):
        """Generate multi-node concurrent speed test configuration"""
        inbounds = []
        outbounds = []
        rules = []
        
        for i, node in enumerate(nodes):
            port = start_port + i
            in_tag = f"in_{i}"
            out_tag = f"proxy_{i}"
            
            # Inbound: Each node corresponds to a local port
            inbounds.append({
                "tag": in_tag,
                "port": port,
                "protocol": "http",
                "settings": {}
            })
            
            # Outbound: Corresponds to a Vmess node
            outbounds.append(ConfigGenerator._build_outbound(node, tag=out_tag))
            
            # Routing: Bind inbound to outbound
            rules.append({
                "type": "field",
                "inboundTag": [in_tag],
                "outboundTag": out_tag
            })
            
        return {
            "log": {"loglevel": "error"},
            "inbounds": inbounds,
            "outbounds": outbounds,
            "routing": {"domainStrategy": "AsIs", "rules": rules}
        }, start_port
