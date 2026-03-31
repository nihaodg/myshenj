import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


LOG_FORMATTERS = {
    "syslog": re.compile(r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+):\s+(.*)$'),
    "json": None,
    "apache": re.compile(r'^(\S+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)'),
    "nginx": re.compile(r'^(\S+)\s+-\s+\S+\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)'),
}


class LogParser:
    def __init__(self, format_type: str = "auto"):
        self.format_type = format_type

    def parse_line(self, line: str) -> Optional[Dict]:
        if self.format_type == "auto":
            return self._auto_parse(line)
        elif self.format_type == "json":
            return self._parse_json(line)
        else:
            return self._parse_by_format(line, self.format_type)

    def _auto_parse(self, line: str) -> Dict:
        for format_name, pattern in LOG_FORMATTERS.items():
            if format_name == "json":
                continue
            if pattern and pattern.match(line):
                return self._parse_by_format(line, format_name)

        try:
            return self._parse_json(line)
        except:
            return self._parse_plain(line)

    def _parse_json(self, line: str) -> Optional[Dict]:
        import json
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                return {
                    "timestamp": data.get("timestamp") or data.get("time") or data.get("@timestamp"),
                    "level": data.get("level") or data.get("severity") or "INFO",
                    "message": data.get("message") or data.get("msg") or str(data),
                    "raw": line
                }
        except:
            pass
        return None

    def _parse_by_format(self, line: str, format_type: str) -> Optional[Dict]:
        pattern = LOG_FORMATTERS.get(format_type)
        if not pattern:
            return self._parse_plain(line)

        match = pattern.match(line)
        if match:
            groups = match.groups()
            if format_type == "syslog":
                return {
                    "timestamp": groups[0],
                    "host": groups[1],
                    "process": groups[2],
                    "message": groups[3],
                    "raw": line
                }
            elif format_type in ("apache", "nginx"):
                return {
                    "ip": groups[0],
                    "timestamp": groups[1],
                    "request": groups[2],
                    "status": groups[3],
                    "size": groups[4],
                    "raw": line
                }
        return self._parse_plain(line)

    def _parse_plain(self, line: str) -> Dict:
        return {
            "timestamp": None,
            "level": self._detect_level(line),
            "message": line.strip(),
            "raw": line
        }

    def _detect_level(self, line: str) -> str:
        line_upper = line.upper()
        if "ERROR" in line_upper or "ERR" in line_upper:
            return "ERROR"
        elif "WARN" in line_upper:
            return "WARN"
        elif "DEBUG" in line_upper:
            return "DEBUG"
        elif "TRACE" in line_upper:
            return "TRACE"
        return "INFO"


def parse_log_file(file_path: str, format_type: str = "auto", max_lines: int = 10000) -> List[Dict]:
    parser = LogParser(format_type)
    entries = []

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            if line.strip():
                entry = parser.parse_line(line)
                if entry:
                    entries.append(entry)

    return entries
