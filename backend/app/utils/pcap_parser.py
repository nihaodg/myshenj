from typing import List, Dict, Optional, Set
from scapy.all import rdpcap, IP, TCP, UDP, DNS, DNSQR, Raw
from collections import defaultdict
import json


class Session:
    def __init__(self, src_ip: str, dst_ip: str, protocol: str):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.protocol = protocol
        self.src_ports: Set[int] = set()
        self.dst_ports: Set[int] = set()
        self.packet_count = 0
        self.bytes_sent = 0
        self.bytes_recv = 0
        self.http_requests: List[Dict] = []
        self.dns_queries: List[str] = []
        self.flags: Dict[str, int] = defaultdict(int)

    def to_dict(self) -> dict:
        return {
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "protocol": self.protocol,
            "src_ports": list(self.src_ports),
            "dst_ports": list(self.dst_ports),
            "packet_count": self.packet_count,
            "bytes_sent": self.bytes_sent,
            "bytes_recv": self.bytes_recv,
            "http_requests": self.http_requests,
            "dns_queries": self.dns_queries,
            "flags": dict(self.flags)
        }


class PCAPParser:
    def __init__(self, pcap_path: str):
        self.pcap_path = pcap_path
        self.sessions: Dict[tuple, Session] = {}
        self.total_packets = 0
        self.ip_addresses: Set[str] = set()

    def parse(self) -> Dict:
        try:
            packets = rdpcap(self.pcap_path)
            self.total_packets = len(packets)

            for packet in packets:
                self._process_packet(packet)

            return self._generate_summary()
        except Exception as e:
            raise ValueError(f"Failed to parse PCAP: {str(e)}")

    def _process_packet(self, packet):
        if IP in packet:
            ip_src = packet[IP].src
            ip_dst = packet[IP].dst
            self.ip_addresses.add(ip_src)
            self.ip_addresses.add(ip_dst)

            protocol = "OTHER"
            src_port = 0
            dst_port = 0

            if TCP in packet:
                protocol = "TCP"
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
                self._update_session(ip_src, ip_dst, protocol, src_port, dst_port, packet)
                self._process_tcp_flags(packet)

            elif UDP in packet:
                protocol = "UDP"
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
                self._update_session(ip_src, ip_dst, protocol, src_port, dst_port, packet)

                if DNS in packet and packet[DNS].qr == 0:
                    try:
                        dns_query = packet[DNSQR].qname.decode('utf-8', errors='ignore')
                        session_key = self._get_session_key(ip_src, ip_dst, protocol)
                        if session_key in self.sessions:
                            self.sessions[session_key].dns_queries.append(dns_query)
                    except:
                        pass

            self._extract_http(packet, ip_src, ip_dst, protocol)

    def _update_session(self, src_ip: str, dst_ip: str, protocol: str, src_port: int, dst_port: int, packet):
        key = self._get_session_key(src_ip, dst_ip, protocol)
        reverse_key = self._get_session_key(dst_ip, src_ip, protocol)

        if key in self.sessions:
            session = self.sessions[key]
        elif reverse_key in self.sessions:
            session = self.sessions[reverse_key]
        else:
            session = Session(src_ip, dst_ip, protocol)
            self.sessions[key] = session

        session.src_ports.add(src_port)
        session.dst_ports.add(dst_port)
        session.packet_count += 1

        if Raw in packet:
            session.bytes_sent += len(packet[Raw].load)

    def _get_session_key(self, ip1: str, ip2: str, protocol: str) -> tuple:
        return (ip1, ip2, protocol)

    def _process_tcp_flags(self, packet):
        tcp = packet[TCP]
        flags = {
            "SYN": tcp.flags & 0x02,
            "ACK": tcp.flags & 0x10,
            "FIN": tcp.flags & 0x01,
            "RST": tcp.flags & 0x04,
            "PSH": tcp.flags & 0x08
        }
        for flag, present in flags.items():
            if present:
                session_key = self._get_session_key(packet[IP].src, packet[IP].dst, "TCP")
                if session_key in self.sessions:
                    self.sessions[session_key].flags[flag] += 1

    def _extract_http(self, packet, ip_src, ip_dst, protocol):
        if Raw in packet:
            try:
                payload = packet[Raw].load
                if isinstance(payload, bytes):
                    payload = payload.decode('utf-8', errors='ignore')

                if 'HTTP' in payload:
                    lines = payload.split('\r\n')
                    if lines:
                        request_line = lines[0]
                        session_key = self._get_session_key(ip_src, ip_dst, protocol)
                        if session_key in self.sessions:
                            self.sessions[session_key].http_requests.append({
                                "method": request_line.split(' ')[0] if ' ' in request_line else '',
                                "uri": request_line.split(' ')[1] if len(request_line.split(' ')) > 1 else '',
                                "raw": payload[:500]
                            })
            except:
                pass

    def _generate_summary(self) -> Dict:
        sessions_list = [s.to_dict() for s in self.sessions.values()]

        suspicious_sessions = []
        for session in sessions_list:
            if self._is_suspicious(session):
                suspicious_sessions.append(session)

        return {
            "total_packets": self.total_packets,
            "unique_ips": list(self.ip_addresses),
            "session_count": len(sessions_list),
            "sessions": sessions_list,
            "suspicious_sessions": suspicious_sessions,
            "attack_graph": self._generate_attack_graph(sessions_list)
        }

    def _is_suspicious(self, session: Session) -> bool:
        if session.flags.get('SYN', 0) > 100 and session.flags.get('ACK', 0) < 10:
            return True
        if len(session.dns_queries) > 50:
            return True
        return False

    def _generate_attack_graph(self, sessions: List[Dict]) -> Dict:
        nodes = []
        edges = []
        ip_to_node = {}

        for ip in self.ip_addresses:
            node_id = f"ip_{len(ip_to_node)}"
            ip_to_node[ip] = node_id
            nodes.append({"id": node_id, "ip": ip, "type": "ip"})

        for session in sessions:
            if self._is_suspicious(session):
                src_node = ip_to_node.get(session['src_ip'])
                dst_node = ip_to_node.get(session['dst_ip'])
                if src_node and dst_node:
                    edges.append({
                        "source": src_node,
                        "target": dst_node,
                        "label": "suspicious_traffic",
                        "protocol": session['protocol']
                    })

        return {"nodes": nodes, "edges": edges}


def parse_pcap(pcap_path: str) -> Dict:
    parser = PCAPParser(pcap_path)
    return parser.parse()
