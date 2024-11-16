import socket
import json
import time
import argparse
import struct
from typing import Tuple, Optional, List
import sys
import dns.resolver # 
import statistics
from datetime import datetime

class SRVRecord:
    @staticmethod
    def lookup(domain: str) -> Optional[Tuple[str, int]]:
        """
        查询Minecraft服务器的SRV记录
        按照Minecraft的规则，查询 _minecraft._tcp.<domain> 的SRV记录
        """
        try:
            answers = dns.resolver.resolve(f"_minecraft._tcp.{domain}", 'SRV')
            if answers:
                # 选择第一个SRV记录（通常是优先级最高的）
                answer = answers[0]
                target = str(answer.target).rstrip('.')  # 移除末尾的点
                return target, answer.port
        except Exception as e:
            print(f"SRV lookup failed: {e}", file=sys.stderr)
        return None

class PingStatistics:
    def __init__(self):
        self.ping_times: List[float] = []
        self.packets_sent = 0
        self.packets_received = 0
        self.start_time = time.time()
        self.target_host = ""
        self.original_host = ""  # 保存原始域名，用于显示

    def add_result(self, success: bool, ping_time: Optional[float] = None):
        self.packets_sent += 1
        if success:
            self.packets_received += 1
            if ping_time is not None:
                self.ping_times.append(ping_time)

    def get_summary(self) -> str:
        duration = time.time() - self.start_time
        loss_rate = ((self.packets_sent - self.packets_received) / self.packets_sent * 100) if self.packets_sent > 0 else 0
        
        # 如果使用了SRV记录，显示原始域名
        display_host = self.original_host if self.original_host else self.target_host
        
        summary = f"\n--- {display_host} mcping statistics ---\n" \
                 f"{self.packets_sent} packets transmitted, {self.packets_received} received, " \
                 f"{loss_rate:.1f}% packet loss, time {int(duration*1000)}ms"
        
        if self.ping_times:
            try:
                summary += f"\nrtt min/avg/max/mdev = {min(self.ping_times):.3f}/{statistics.mean(self.ping_times):.3f}/" \
                          f"{max(self.ping_times):.3f}/{statistics.stdev(self.ping_times):.3f} ms"
            except statistics.StatisticsError:
                pass
                
        return summary

class MCPing:
    PROTOCOL_VERSION = 767  # Minecraft 1.21
    TIMEOUT_SECONDS = 0.5   # 500ms timeout

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._socket = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self) -> bool:
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.TIMEOUT_SECONDS)
            self._socket.connect((self.host, self.port))
            return True
        except socket.error as e:
            print(f"Connection failed: {e}", file=sys.stderr)
            return False

    def close(self):
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None

    def write_varint(self, value: int) -> bytes:
        buffer = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            if value:
                byte |= 0x80
            buffer.append(byte)
            if not value:
                break
        return bytes(buffer)

    def read_varint(self) -> int:
        result = 0
        position = 0
        
        while True:
            try:
                byte = self._socket.recv(1)[0]
            except (IndexError, socket.error) as e:
                raise socket.error(f"Failed to read varint: {e}")
                
            result |= (byte & 0x7F) << position
            
            if not (byte & 0x80):
                break
                
            position += 7
            if position >= 32:
                raise ValueError("VarInt is too big")
                
        return result

    def create_handshake_packet(self) -> bytes:
        host_bytes = self.host.encode('utf-8')
        
        # 构建数据包内容
        packet = (
            self.write_varint(0) +  # Packet ID for handshake
            self.write_varint(self.PROTOCOL_VERSION) +  # Protocol version
            bytes([len(host_bytes)]) + host_bytes +  # Host length and host
            struct.pack('>H', self.port) +  # Port (big-endian)
            self.write_varint(1)  # Next state (1 for status)
        )
        
        # 添加数据包长度前缀
        return self.write_varint(len(packet)) + packet

    def create_status_request_packet(self) -> bytes:
        packet = self.write_varint(0)  # Packet ID for status request
        return self.write_varint(len(packet)) + packet

    def ping(self) -> Tuple[Optional[dict], float]:
        start_time = time.time()
        try:
            if not self.connect():
                return None, (time.time() - start_time) * 1000

            # 发送握手包
            self._socket.sendall(self.create_handshake_packet())
            
            # 发送状态请求包
            self._socket.sendall(self.create_status_request_packet())
            
            # 读取响应
            packet_length = self.read_varint()
            packet_id = self.read_varint()
            
            if packet_id != 0:
                raise ValueError(f"Invalid packet ID: {packet_id}")
            
            json_length = self.read_varint()
            json_data = b''
            
            while len(json_data) < json_length:
                chunk = self._socket.recv(json_length - len(json_data))
                if not chunk:
                    raise socket.error("Connection closed while reading JSON data")
                json_data += chunk
            
            response_data = json.loads(json_data.decode('utf-8'))
            return response_data, (time.time() - start_time) * 1000
            
        except Exception as e:
            # print(f"Ping failed: {e}", file=sys.stderr)
            return None, (time.time() - start_time) * 1000
        finally:
            self.close()

def resolve_address(host: str, port: int = None) -> Tuple[str, int]:
    """解析地址，支持SRV记录查询"""
    # 如果提供了端口号，直接返回
    if port is not None:
        return host, port
        
    # 检查是否包含端口号
    if ':' in host:
        host, port = host.split(':')
        return host, int(port)
        
    # 尝试SRV记录查询
    srv_result = SRVRecord.lookup(host)
    if srv_result:
        return srv_result
        
    # 默认返回标准端口
    return host, 25565

def main():
    parser = argparse.ArgumentParser(description='Minecraft server status checker')
    parser.add_argument('-srv', help='Server host (with SRV lookup)')
    parser.add_argument('-host', help='Host:port combination')
    parser.add_argument('-c', type=int, default=0, help='Count of pings (0 = infinite)')
    parser.add_argument('-i', type=int, default=1000, help='Interval between pings in ms')
    parser.add_argument('-t', type=int, help='Timeout in ms')
    parser.add_argument('args', nargs='*', help='Positional arguments: host [port]')

    args = parser.parse_args()

    # 确定主机和端口
    original_host = None
    if args.srv:
        original_host = args.srv
        host, port = resolve_address(args.srv)
    elif args.host:
        host, port = resolve_address(args.host)
    elif args.args:
        host = args.args[0]
        port = int(args.args[1]) if len(args.args) > 1 else None
        host, port = resolve_address(host, port)
    else:
        parser.print_help()
        sys.exit(1)

    interval = args.i / 1000.0
    MCPing.TIMEOUT_SECONDS = (args.t / 1000.0) if args.t else (interval * 2)

    try:
        ip = socket.gethostbyname(host)
        if original_host:
            print(f"MCPING {original_host} -> {host} ({ip}) port {port}")
        else:
            print(f"MCPING {host} ({ip}) port {port}")
    except socket.gaierror as e:
        print(f"Could not resolve hostname: {host}")
        sys.exit(1)

    stats = PingStatistics()
    stats.target_host = host
    if original_host:
        stats.original_host = original_host
    
    try:
        ping_count = 0
        while args.c == 0 or ping_count < args.c:
            with MCPing(host, port) as pinger:
                result, ping_time = pinger.ping()
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            if result:
                player_count = result.get('players', {}).get('online', 0)
                max_players = result.get('players', {}).get('max', 0)
                version = result.get('version', {}).get('name', 'Unknown')
                print(f"[{timestamp}] {player_count}/{max_players} players online, version {version}, latency={ping_time:.1f}ms")
                stats.add_result(True, ping_time)
            else:
                print(f"[{timestamp}] Request timed out")
                stats.add_result(False)
            
            ping_count += 1
            
            if args.c == 0 or ping_count < args.c:
                time.sleep(interval)

    except KeyboardInterrupt:
        pass
    finally:
        print(stats.get_summary())

if __name__ == "__main__":
    main()
