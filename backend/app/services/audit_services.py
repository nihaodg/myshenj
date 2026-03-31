import os
import zipfile
from typing import List, Dict, Any, Optional
from app.utils.file_utils import (
    get_file_language, is_supported_file, get_all_files,
    read_file_lines
)
from app.utils.pcap_parser import parse_pcap
from app.services.rule_engine import RuleEngine, get_default_rules
from app.services.ai_adapter import AIAdapter, build_code_audit_prompt
from app.models.rule import CustomRule
from sqlalchemy.ext.asyncio import AsyncSession


class CodeAuditService:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.rule_engine = RuleEngine()
        self.ai_adapter = AIAdapter()
        self.db = db
        self._load_rules()

    def _load_rules(self):
        default_rules = get_default_rules()
        for r in default_rules:
            self.rule_engine._rules.append(
                self._dict_to_rule(r)
            )

    def _dict_to_rule(self, rule_dict: Dict) -> Any:
        from app.services.rule_engine import Rule
        return Rule(
            rule_id=rule_dict['id'],
            name=rule_dict['name'],
            severity=rule_dict['severity'],
            pattern=rule_dict['pattern'],
            message=rule_dict['message'],
            language=rule_dict.get('language')
        )

    async def audit_file(self, file_path: str, use_ai: bool = False,
                         language: Optional[str] = None) -> List[Dict]:
        findings = []

        if language is None:
            language = get_file_language(file_path)

        content = ''.join(read_file_lines(file_path, max_lines=5000))

        rule_findings = self.rule_engine.scan_content(content, language, file_path)
        findings.extend(rule_findings)

        if use_ai and language:
            try:
                ai_findings = await self._ai_analyze(content, language, file_path)
                findings.extend(ai_findings)
            except Exception:
                pass

        return self._deduplicate_findings(findings)

    async def _ai_analyze(self, content: str, language: str, file_path: str) -> List[Dict]:
        prompt = build_code_audit_prompt(content, language)
        result = await self.ai_adapter.analyze_json(prompt)

        if isinstance(result, list):
            findings = []
            for item in result:
                if isinstance(item, dict):
                    findings.append({
                        'rule_id': f"AI_{item.get('vuln_type', 'UNKNOWN')}",
                        'rule_name': item.get('vuln_type', 'AI Detected Issue'),
                        'severity': item.get('severity', 'medium'),
                        'message': item.get('description', ''),
                        'file_name': os.path.basename(file_path),
                        'line_number': item.get('line'),
                        'line_content': '',
                        'matched_text': '',
                        'recommendation': item.get('recommendation', '')
                    })
            return findings
        return []

    async def audit_directory(self, directory: str, use_ai: bool = False) -> Dict[str, Any]:
        files = get_all_files(directory)
        all_findings = []
        processed_files = 0

        for relative_path, full_path in files:
            try:
                language = get_file_language(relative_path)
                if language and language != 'log' and language != 'text':
                    findings = await self.audit_file(full_path, use_ai, language)
                    all_findings.extend(findings)
                    processed_files += 1
            except Exception:
                continue

        return {
            'total_files': processed_files,
            'total_issues': len(all_findings),
            'issues': all_findings,
            'severity_summary': self._count_by_severity(all_findings)
        }

    def _deduplicate_findings(self, findings: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        for f in findings:
            key = (f.get('file_name'), f.get('line_number'), f.get('rule_id'))
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    def _count_by_severity(self, findings: List[Dict]) -> Dict[str, int]:
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for f in findings:
            severity = f.get('severity', 'medium').lower()
            if severity in counts:
                counts[severity] += 1
        return counts


class LogAuditService:
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.ai_adapter = AIAdapter()
        self._load_rules()

    def _load_rules(self):
        default_rules = get_default_rules()
        for r in default_rules:
            self.rule_engine._rules.append(
                self._dict_to_rule(r)
            )

    def _dict_to_rule(self, rule_dict: Dict) -> Any:
        from app.services.rule_engine import Rule
        return Rule(
            rule_id=rule_dict['id'],
            name=rule_dict['name'],
            severity=rule_dict['severity'],
            pattern=rule_dict['pattern'],
            message=rule_dict['message'],
            language=rule_dict.get('language')
        )

    async def audit_log_file(self, file_path: str, use_ai: bool = False,
                              format_type: str = "auto") -> Dict[str, Any]:
        from app.utils.log_parser import parse_log_file

        entries = parse_log_file(file_path, format_type)
        findings = []

        log_content = '\n'.join([e.get('raw', '') for e in entries[:1000]])

        rule_findings = self.rule_engine.scan_content(log_content, 'log')
        for f in rule_findings:
            f['rule_name'] = f"规则匹配: {f['rule_name']}"
        findings.extend(rule_findings)

        attack_chain = []
        if use_ai:
            try:
                attack_chain = await self._ai_analyze(entries)
            except Exception:
                pass

        return {
            'total_lines': len(entries),
            'issues': findings,
            'attack_chain': attack_chain,
            'severity_summary': self._count_by_severity(findings)
        }

    async def _ai_analyze(self, entries: List[Dict]) -> List[Dict]:
        from app.services.ai_adapter import build_log_audit_prompt

        log_content = '\n'.join([
            f"{e.get('timestamp', '')} {e.get('message', '')}"
            for e in entries[:500]
        ])

        prompt = build_log_audit_prompt(log_content)
        result = await self.ai_adapter.analyze_json(prompt)

        if isinstance(result, list):
            return result
        return []


class TrafficAuditService:
    def __init__(self):
        self.ai_adapter = AIAdapter()

    async def audit_pcap(self, pcap_path: str, use_ai: bool = False) -> Dict[str, Any]:
        try:
            pcap_result = parse_pcap(pcap_path)
        except Exception as e:
            return {'error': str(e)}

        findings = []

        for session in pcap_result.get('suspicious_sessions', []):
            findings.append({
                'rule_id': 'TRAFFIC-001',
                'rule_name': '可疑会话检测',
                'severity': 'medium',
                'message': f"检测到可疑流量: {session.get('protocol')} 从 {session.get('src_ip')} 到 {session.get('dst_ip')}",
                'file_name': pcap_path,
                'session': session
            })

        attack_graph = pcap_result.get('attack_graph', {'nodes': [], 'edges': []})

        if use_ai:
            try:
                ai_findings = await self._ai_analyze(pcap_result)
                findings.extend(ai_findings)
            except Exception:
                pass

        return {
            'total_packets': pcap_result.get('total_packets', 0),
            'unique_ips': pcap_result.get('unique_ips', []),
            'session_count': pcap_result.get('session_count', 0),
            'issues': findings,
            'attack_graph': attack_graph,
            'severity_summary': self._count_by_severity(findings)
        }

    async def _ai_analyze(self, pcap_result: Dict) -> List[Dict]:
        from app.services.ai_adapter import build_traffic_audit_prompt

        sessions = pcap_result.get('sessions', [])[:50]
        traffic_summary = json.dumps(sessions, indent=2)

        prompt = build_traffic_audit_prompt(traffic_summary)
        result = await self.ai_adapter.analyze_json(prompt)

        if isinstance(result, list):
            findings = []
            for item in result:
                if isinstance(item, dict):
                    findings.append({
                        'rule_id': 'AI_TRAFFIC',
                        'rule_name': 'AI流量分析',
                        'severity': item.get('severity', 'medium'),
                        'message': f"AI分析: {item.get('reason', '')}",
                        'src_ip': item.get('src_ip'),
                        'dst_ip': item.get('dst_ip')
                    })
            return findings
        return []

    def _count_by_severity(self, findings: List[Dict]) -> Dict[str, int]:
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for f in findings:
            severity = f.get('severity', 'medium').lower()
            if severity in counts:
                counts[severity] += 1
        return counts


import json
