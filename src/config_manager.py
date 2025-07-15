import os
import json
import base64
from urllib.parse import urlparse, parse_qs, unquote


def parse_trojan(trojan_url):
    """Parse trojan:// URL"""
    url = urlparse(trojan_url)
    if url.scheme != "trojan":
        raise ValueError("Invalid Trojan URL")

    password = url.netloc.split('@')[0]
    server_address = url.netloc.split('@')[1].split(':')[0]
    server_port = url.netloc.split('@')[1].split(':')[1]

    # Parse query parameters
    params = parse_qs(url.query)

    config = {
        'protocol': 'trojan',
        'password': password,
        'add': server_address,
        'port': server_port,
        'ps': unquote(url.fragment) if url.fragment else server_address,
        'security': params.get('security', ['tls'])[0],
        'type': params.get('type', ['tcp'])[0],
        'host': params.get('host', [''])[0],
        'path': params.get('path', [''])[0]
    }
    return config


def parse_ss(ss_url):
    """Parse shadowsocks:// URL"""
    url = urlparse(ss_url)
    if url.scheme != "ss":
        raise ValueError("Invalid Shadowsocks URL")

    # SS format: method:password@hostname:port
    userinfo = url.netloc.split('@')[0]
    method = userinfo.split(':')[0]
    password = ':'.join(userinfo.split(':')[1:])
    server_address = url.netloc.split('@')[1].split(':')[0]
    server_port = url.netloc.split('@')[1].split(':')[1]

    config = {
        'protocol': 'shadowsocks',
        'method': method,
        'password': password,
        'add': server_address,
        'port': server_port,
        'ps': unquote(url.fragment) if url.fragment else server_address
    }
    return config


def parse_vless(vless_url):
    """Parse vless:// URL"""
    url = urlparse(vless_url)
    if url.scheme != "vless":
        raise ValueError("Invalid VLESS URL")

    # Extract UUID from netloc (before @)
    uuid = url.netloc.split('@')[0]
    server_part = url.netloc.split('@')[1]
    server_address = server_part.split(':')[0]
    server_port = server_part.split(':')[1].split('?')[0]

    # Parse query parameters
    params = parse_qs(url.query)

    config = {
        'protocol': 'vless',
        'id': uuid,
        'add': server_address,
        'port': server_port,
        'ps': unquote(url.fragment) if url.fragment else server_address,
        'encryption': params.get('encryption', ['none'])[0],
        'security': params.get('security', [''])[0],
        'type': params.get('type', ['tcp'])[0],
        'host': params.get('host', [''])[0],
        'path': params.get('path', [''])[0]
    }
    return config


def parse_vmess(vmess_url):
    """Parse vmess:// URL"""
    url = urlparse(vmess_url)
    if url.scheme != "vmess":
        raise ValueError("Invalid VMESS URL")

    config_json = base64.b64decode(url.netloc).decode('utf-8')
    config = json.loads(config_json)
    config['protocol'] = 'vmess'
    return config


class ConfigManager:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.v2ray-client")
        self.servers_file = os.path.join(self.config_dir, "servers.json")

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

        if not os.path.exists(self.servers_file):
            with open(self.servers_file, 'w') as f:
                json.dump([], f)

    def add_server(self, server_url, title):
        """Add a new server from URL"""
        try:
            protocol = server_url.split('://')[0].lower()

            if protocol == 'vmess':
                config = parse_vmess(server_url)
            elif protocol == 'vless':
                config = parse_vless(server_url)
            elif protocol == 'ss':
                config = parse_ss(server_url)
            elif protocol == 'trojan':
                config = parse_trojan(server_url)
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")

            config['title'] = title

            # Read existing servers
            with open(self.servers_file, 'r') as f:
                servers = json.load(f)

            # Add new server
            servers.append(config)

            # Save back to file
            with open(self.servers_file, 'w') as f:
                json.dump(servers, f, indent=2)

            return True
        except Exception as e:
            print(f"Error adding server: {e}")
            return False

    def get_servers(self):
        """Get list of all servers"""
        with open(self.servers_file, 'r') as f:
            return json.load(f)

    def remove_server(self, server_id):
        """Remove a server by ID"""
        servers = self.get_servers()
        servers = [s for s in servers if s.get('id') != server_id]
        with open(self.servers_file, 'w') as f:
            json.dump(servers, f, indent=2)
