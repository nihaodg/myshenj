import re
from typing import List, Dict, Optional
from app.models.rule import CustomRule


class Rule:
    def __init__(self, rule_id: str, name: str, severity: str, pattern: str,
                 message: str, language: Optional[str] = None):
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
        self.pattern = pattern
        self.message = message
        self.language = language
        self._compiled_pattern = re.compile(pattern)

    def match(self, content: str, language: Optional[str] = None) -> List[Dict]:
        if self.language and language and self.language.lower() != language.lower():
            return []

        matches = []
        for i, line in enumerate(content.split('\n'), 1):
            if self._compiled_pattern.search(line):
                matches.append({
                    'line_number': i,
                    'line_content': line.strip(),
                    'matched_text': self._compiled_pattern.search(line).group()
                })
        return matches


class RuleEngine:
    def __init__(self):
        self._rules: List[Rule] = []

    def load_rules(self, db_rules: List[CustomRule]):
        self._rules = []
        for db_rule in db_rules:
            if db_rule.enabled:
                try:
                    rule = Rule(
                        rule_id=db_rule.rule_id,
                        name=db_rule.name,
                        severity=db_rule.severity,
                        pattern=db_rule.pattern,
                        message=db_rule.message,
                        language=db_rule.language
                    )
                    self._rules.append(rule)
                except re.error:
                    continue

    def scan_content(self, content: str, language: Optional[str] = None,
                     filename: Optional[str] = None) -> List[Dict]:
        findings = []

        for rule in self._rules:
            if rule.language and language and rule.language.lower() != language.lower():
                continue

            matches = rule.match(content, language)
            for match in matches:
                findings.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'severity': rule.severity,
                    'message': rule.message,
                    'file_name': filename,
                    'line_number': match['line_number'],
                    'line_content': match['line_content'],
                    'matched_text': match['matched_text']
                })

        return findings

    def get_rule_count(self) -> int:
        return len(self._rules)


_default_rule_templates = [
    {
        'id': 'SQLI-001',
        'name': 'SQL注入检测 (Python)',
        'severity': 'high',
        'language': 'python',
        'pattern': r'(?i)(cursor\.execute|executemany)\s*\([^)]*%s',
        'message': '检测到使用 %s 占位的SQL查询，请使用参数化查询'
    },
    {
        'id': 'SQLI-002',
        'name': 'SQL注入检测 (通用)',
        'severity': 'high',
        'language': None,
        'pattern': r'(?i)(exec|execute)\s*\(.*?(?:select|insert|update|delete)\s*',
        'message': '检测到使用字符串拼接执行SQL语句，可能导致SQL注入'
    },
    {
        'id': 'HARDCODED-001',
        'name': '硬编码密钥检测',
        'severity': 'high',
        'language': None,
        'pattern': r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token)\s*=\s*["\'][a-zA-Z0-9]{16,}',
        'message': '检测到硬编码的密钥，请使用环境变量'
    },
    {
        'id': 'DANGER-001',
        'name': 'eval使用检测',
        'severity': 'high',
        'language': 'javascript',
        'pattern': r'\beval\s*\(',
        'message': '检测到eval使用，可能存在代码注入风险'
    },
    {
        'id': 'DANGER-002',
        'name': 'innerHTML使用检测',
        'severity': 'medium',
        'language': 'javascript',
        'pattern': r'\.innerHTML\s*=',
        'message': '检测到innerHTML使用，可能存在XSS风险'
    },
    {
        'id': 'INSECURE-001',
        'name': '不安全的随机数',
        'severity': 'medium',
        'language': 'python',
        'pattern': r'random\.(random|randint|choice)\s*\(',
        'message': '检测到使用random模块生成安全敏感数据，请使用secrets模块'
    },
    {
        'id': 'PASSWORD-001',
        'name': '硬编码密码检测',
        'severity': 'critical',
        'language': None,
        'pattern': r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}',
        'message': '检测到硬编码密码，请使用环境变量或配置中心'
    },
    {
        'id': 'LOG-INJECT-001',
        'name': '日志注入检测',
        'severity': 'medium',
        'language': None,
        'pattern': r'(?i)(log|logger|print)\s*\(.*?(?:\\n|\\r|%0a|%0d)',
        'message': '检测到可能存在日志注入风险'
    }
]


def get_default_rules() -> List[Dict]:
    return _default_rule_templates
