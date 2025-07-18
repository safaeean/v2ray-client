import os
import json
from typing import Dict, Any


class ConfigGenerator:
    def __init__(self, logs_dir: str = "~/.v2ray-client/logs", socks_port: int = 1080):
        self.logs_dir = os.path.expanduser(logs_dir)
        os.makedirs(self.logs_dir, exist_ok=True)
        self.socks_port = socks_port

    def generate(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Xray config based on protocol"""
        protocol = server_config.get('protocol', 'vmess').lower()

        if protocol == 'vmess':
            return self._generate_vmess_config(server_config)
        elif protocol == 'vless':
            return self._generate_vless_config(server_config)
        elif protocol == 'shadowsocks':
            return self._generate_shadowsocks_config(server_config)
        elif protocol == 'trojan':
            return self._generate_trojan_config(server_config)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

    def _base_inbound(self) -> Dict[str, Any]:
        """Generate common inbound configuration"""
        return {
            "port": self.socks_port,
            "listen": "127.0.0.1",
            "protocol": "socks",
            "settings": {
                "auth": "noauth",
                "udp": True,
                "ip": "127.0.0.1"
            },
            "sniffing": {
                "enabled": True,
                "destOverride": ["http", "tls"],
                "metadataOnly": False
            }
        }

    def _base_logging(self) -> Dict[str, Any]:
        """Generate common logging configuration"""
        return {
            "loglevel": "debug",
            "access": os.path.join(self.logs_dir, "access.log"),
            "error": os.path.join(self.logs_dir, "error.log")
        }

    def _generate_vmess_config(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized VMESS configuration"""
        return {
            "log": self._base_logging(),
            "inbounds": [self._base_inbound()],
            "outbounds": [{
                "protocol": "vmess",
                "settings": {
                    "vnext": [{
                        "address": server_config["add"],
                        "port": int(server_config["port"]),
                        "users": [{
                            "id": server_config["id"],
                            "alterId": int(server_config.get("aid", 0)),
                            "security": server_config.get("scy", "auto")
                        }]
                    }]
                },
                "streamSettings": {
                    "network": server_config.get("net", "tcp"),
                    "security": server_config.get("tls", "tls"),
                    "tlsSettings": {
                        "serverName": server_config.get("host", ""),
                        "alpn": ["h2", "http/1.1"],
                        "fingerprint": "chrome"
                    } if server_config.get("tls") else None,
                    "tcpSettings": {
                        "header": {
                            "type": "http",
                            "request": {
                                "path": [server_config.get("path", "/")],
                                "headers": {
                                    "Host": [server_config.get("host", "")]
                                }
                            }
                        }
                    } if server_config.get("net") == "tcp" and server_config.get("headerType") == "http" else None,
                    "wsSettings": {
                        "path": server_config.get("path", "/"),
                        "headers": {
                            "Host": server_config.get("host", "")
                        }
                    } if server_config.get("net") == "ws" else None
                }
            }]
        }

    def _generate_vless_config(self, server_config: dict) -> dict:
        """Generate VLESS config that works with your specific server"""
        return {
            "log": {
                "loglevel": "debug",
                "access": os.path.join(self.logs_dir, "access.log"),
                "error": os.path.join(self.logs_dir, "error.log")
            },
            "inbounds": [{
                "port": self.socks_port,
                "listen": "127.0.0.1",
                "protocol": "socks",
                "settings": {
                    "auth": "noauth",
                    "udp": True
                }
            }],
            "outbounds": [{
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": server_config["add"],
                        "port": int(server_config["port"]),
                        "users": [{
                            "id": server_config["id"],
                            "encryption": "none"
                        }]
                    }]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "none",
                    "tcpSettings": {
                        "header": {
                            "type": "http",
                            "request": {
                                "path": ["/"],
                                "headers": {
                                    "Host": [server_config["host"]]
                                }
                            }
                        }
                    }
                }
            }]
        }

    def _generate_shadowsocks_config(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized Shadowsocks configuration"""
        return {
            "log": self._base_logging(),
            "inbounds": [self._base_inbound()],
            "outbounds": [{
                "protocol": "shadowsocks",
                "settings": {
                    "servers": [{
                        "address": server_config["add"],
                        "port": int(server_config["port"]),
                        "method": server_config["method"],
                        "password": server_config["password"],
                        "ota": False,
                        "level": 0
                    }]
                },
                "streamSettings": {
                    "network": "tcp"
                }
            }]
        }

    def _generate_trojan_config(self, server_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimized Trojan configuration"""
        return {
            "log": self._base_logging(),
            "inbounds": [self._base_inbound()],
            "outbounds": [{
                "protocol": "trojan",
                "settings": {
                    "servers": [{
                        "address": server_config["add"],
                        "port": int(server_config["port"]),
                        "password": server_config["password"]
                    }]
                },
                "streamSettings": {
                    "network": server_config.get("type", "tcp"),
                    "security": server_config.get("security", "tls"),
                    "tlsSettings": {
                        "serverName": server_config.get("host", ""),
                        "alpn": ["h2", "http/1.1"],
                        "fingerprint": "chrome"
                    },
                    "wsSettings": {
                        "path": server_config.get("path", "/"),
                        "headers": {
                            "Host": server_config.get("host", "")
                        }
                    } if server_config.get("type") == "ws" else None
                }
            }]
        }
