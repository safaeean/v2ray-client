import os
import json
import subprocess
import tempfile
import threading
import socket
from datetime import datetime
from config_generator import ConfigGenerator
import psutil
import signal
import time
from embedded_xray import extract_xray_to_tmp
import shutil
import os

class V2RayController:
    def __init__(self, xray_binary, socks_port=1080):
        self.xray_binary = extract_xray_to_tmp()
        self.process = None
        self.config_file = None
        self.config_gen = ConfigGenerator()
        self.log_file = None
        self.log_thread = None
        self.running = False
        self.running_redirect_traffic = False
        self.socks_port = socks_port
        self.config_gen = ConfigGenerator(socks_port=self.socks_port)

        # Setup logs directory
        self.logs_dir = os.path.expanduser("~/.v2ray-client/logs")
        os.makedirs(self.logs_dir, exist_ok=True)

    def _kill_existing_processes(self):
        """Kill any existing processes using our port"""
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.connections():
                    if conn.laddr.port == self.socks_port:
                        os.kill(proc.pid, signal.SIGTERM)
                        time.sleep(1)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def _log_message(self, message, source="Xray"):
        """Log a message to console and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{source}] {message}"
        print(log_entry)
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")

    def _read_process_output(self):
        """Read process output in a thread"""
        while self.running and self.process:
            # Try to read both stdout and stderr
            try:
                stdout = self.process.stdout.readline()
                if stdout:
                    self._log_message(stdout.decode('utf-8', errors='replace').strip())

                stderr = self.process.stderr.readline()
                if stderr:
                    self._log_message(stderr.decode('utf-8', errors='replace').strip(), "Xray-Error")
            except Exception as e:
                self._log_message(f"Error reading process output: {str(e)}", "Controller-Error")

            time.sleep(0.1)

    def _check_network(self):
        """Verify basic network connectivity"""
        try:
            # Test DNS resolution
            socket.gethostbyname('google.com')

            # Test raw TCP connection
            with socket.create_connection(('4.2.2.4', 53), timeout=5):
                pass

            return True
        except Exception as e:
            self._log_message(f"Network check failed: {str(e)}", "Error")
            return False

    def diagnose_connection(self):
        """Run comprehensive connection tests"""
        tests = [
            ("TCP Connection", self._test_tcp_connection),
            ("DNS Resolution", self._test_dns_resolution),
            ("HTTP Proxy", lambda: self._test_http_proxy("http://example.com")),
            ("HTTPS Proxy", lambda: self._test_http_proxy("https://example.com")),
            ("TLS Handshake", self._test_tls_handshake)
        ]

        for name, test_func in tests:
            success = test_func()
            self._log_message(f"{name}: {'✓' if success else '✗'}", "Diagnostics")
            if not success:
                return False
        return True

    def _test_tls_handshake(self):
        """Test TLS 1.3 handshake through proxy"""
        try:
            test_cmd = [
                "curl", "-v",
                "-x", f"socks5://127.0.0.1:{self.socks_port}",
                "--tlsv1.3",
                "--tls-max", "1.3",
                "https://www.google.com"
            ]
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=30)
            return "SSL connection using TLSv1.3" in result.stderr
        except Exception as e:
            self._log_message(f"TLS test failed: {str(e)}", "Debug")
            return False

    def redirect_all_traffic_through_socks(self):
        def run_pkexec():
            try:
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts/run.sh"))

                print(f"Script path: {script_path}")

                if not os.path.exists(script_path):
                    print(f"Error: Script not found at {script_path}")
                else:
                    print("Script exists, proceeding...")

                try:
                    self.running_redirect_traffic = True
                    result = subprocess.run(
                        ["bash", script_path, "redirect.sh", str(self.socks_port)],
                        timeout=10,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    print("Direct execution output:", result.stdout)
                except Exception as e:
                    print("Direct execution error:", e)
                except subprocess.TimeoutExpired:
                    print("Error: Script timed out after 10 seconds")
                except subprocess.CalledProcessError as e:
                    print(f"Script failed with error {e.returncode}:")
                    print("Stdout:", e.stdout)
                    print("Stderr:", e.stderr)
                except Exception as e:
                    print(f"Unexpected error: {e}")
                # بعد از موفقیت می‌تونی سیگنال یا کال‌بک برای UI بزنی تا وضعیت رو به روز کنه
            except subprocess.CalledProcessError as e:
                print("[PKEXEC Error]", e.stderr)
            except Exception as e:
                print("[PKEXEC Exception]", str(e))

        threading.Thread(target=run_pkexec, daemon=True).start()
        return True  # اینجا سریع True برگردون، چون عملیات توی ترد داره انجام میشه

    def start(self, server_config):
        """Start with enhanced network validation"""
        # First verify if we're even connected to any network
        if not self._check_network():
            self._log_message("Critical Network Issue Detected", "Critical")
            return False

        """Start Xray with proper process handling"""
        self.stop()  # Clean up any existing process

        self.log_file = os.path.join(self.logs_dir, f"xray.log")

        try:
            # Generate config
            config = self.config_gen.generate(server_config)
            self._log_message(f"Using config:\n{json.dumps(config, indent=2)}", "Debug")

            # Write config to temp file
            fd, self.config_file = tempfile.mkstemp(suffix='.json')
            with os.fdopen(fd, 'w') as f:
                json.dump(config, f, indent=2)

            print(self.config_file)
            # Start process without buffering warnings
            self.process = subprocess.Popen(
                [self.xray_binary, "-config", self.config_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                bufsize=0,  # Disable buffering to avoid warnings
                universal_newlines=False
            )

            # Start output reader
            self.running = True
            self.log_thread = threading.Thread(target=self._read_process_output)
            self.log_thread.daemon = True
            self.log_thread.start()

            # Verify Xray is listening
            if not self._wait_for_port():
                raise RuntimeError("Xray failed to start listening on port")

            self._log_message("Xray started and listening", "Controller")
            return True

        except Exception as e:
            self._log_message(f"Start failed: {str(e)}", "Controller-Error")
            self.stop()
            return False

    def _wait_for_port(self, timeout=5):
        """Wait until Xray is listening on the port"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._check_port():
                return True
            time.sleep(0.5)
        return False

    def _check_port(self):
        """Check if Xray is listening on the port"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                return s.connect_ex(('127.0.0.1', self.socks_port)) == 0
        except Exception as e:
            self._log_message(f"Port check error: {str(e)}", "Debug")
            return False


    def stop(self):
        if self.running_redirect_traffic:
            try:
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts/run.sh"))

                print(f"Script path: {script_path}")

                if not os.path.exists(script_path):
                    print(f"Error: Script not found at {script_path}")
                else:
                    print("Script exists, proceeding...")

                try:
                    result = subprocess.run(
                        ["bash", script_path, "revert.sh", str(self.socks_port)],
                        timeout=10,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    print("Direct execution output:", result.stdout)
                except Exception as e:
                    print("Direct execution error:", e)

            except Exception as e:
                print("Direct execution error:", e)


        """Clean up the Xray process"""
        if self.process:
            self._log_message("Stopping Xray...", "Controller")
            self.running = False

            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                if self.xray_binary and os.path.exists(self.xray_binary):
                    os.unlink(self.xray_binary)
                self._log_message("Forcefully killed Xray", "Controller")
            except Exception as e:
                self._log_message(f"Stop error: {str(e)}", "Controller-Error")

            self.process = None

        if self.config_file and os.path.exists(self.config_file):
            try:
                os.unlink(self.config_file)
            except Exception as e:
                self._log_message(f"Config cleanup error: {str(e)}", "Controller-Error")

        if self.log_thread and self.log_thread.is_alive():
            self.log_thread.join(timeout=1)

        if self.is_port_in_use():
            self._cleanup_port()

    def _safe_kill_process(self, pid: int):
        """Safely kill a process with error handling"""
        try:
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                process.terminate()
                try:
                    process.wait(timeout=3)
                except psutil.TimeoutExpired:
                    process.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    def _cleanup_port(self):
        """Clean up any processes using our port"""
        for conn in psutil.net_connections():
            if conn.laddr and conn.laddr.port == self.socks_port:
                if conn.pid:
                    self._safe_kill_process(conn.pid)

    def is_port_in_use(self) -> bool:
        """Check if port is still in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', self.socks_port)) == 0

    def __del__(self):
        self.stop()
