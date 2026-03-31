MITRE_ATTACK_TACTICS = {
    "reconnaissance": {
        "name": "侦察",
        "techniques": ["T1595", "T1592", "T1589", "T1590", "T1598", "T1597", "T1596", "T1593", "T1594", "T1591"]
    },
    "resource_development": {
        "name": "资源开发",
        "techniques": ["T1583", "T1586", "T1587", "T1585", "T1584", "T1588", "T1595"]
    },
    "initial_access": {
        "name": "初始访问",
        "techniques": ["T1189", "T1190", "T1133", "T1566", "T1200", "T1434", "T1477"]
    },
    "execution": {
        "name": "执行",
        "techniques": ["T1059", "T1603", "T1604", "T1559", "T1203", "T1106", "T1505"]
    },
    "persistence": {
        "name": "持久化",
        "techniques": ["T1098", "T1547", "T1543", "T1554", "T1546", "T1542", "T1179", "T1548"]
    },
    "privilege_escalation": {
        "name": "权限提升",
        "techniques": ["T1068", "T1055", "T1543", "T1484", "T1069", "T1053", "T1574"]
    },
    "defense_evasion": {
        "name": "防御规避",
        "techniques": ["T1562", "T1484", "T1570", "T1564", "T1497", "T1553", "T1078"]
    },
    "credential_access": {
        "name": "凭证访问",
        "techniques": ["T1110", "T1555", "T1552", "T1606", "T1558", "T1556"]
    },
    "discovery": {
        "name": "发现",
        "techniques": ["T1018", "T1046", "T1049", "T1057", "T1082", "T1083", "T1124", "T1201"]
    },
    "lateral_movement": {
        "name": "横向移动",
        "techniques": ["T1210", "T1534", "T1021", "T1570", "T1563", "T1550"]
    },
    "collection": {
        "name": "收集",
        "techniques": ["T1005", "T1039", "T1074", "T1114", "T1185", "T1113", "T1123"]
    },
    "command_and_control": {
        "name": "命令与控制",
        "techniques": ["T1071", "T1132", "T1568", "T1572", "T1573", "T1104", "T1001"]
    },
    "exfiltration": {
        "name": "数据泄露",
        "techniques": ["T1041", "T1560", "T1048", "T1567", "T1052"]
    },
    "impact": {
        "name": "影响",
        "techniques": ["T1486", "T1491", "T1489", "T1490", "T1495", "T1499", "T1498"]
    }
}


ATTACK_TYPE_MAPPING = {
    "SQL注入": {
        "tactic": "initial_access",
        "technique_id": "T1190",
        "technique_name": "Exploitation of Remote Services",
        "severity": "high"
    },
    "XSS": {
        "tactic": "initial_access",
        "technique_id": "T1190",
        "technique_name": "Cross-site Scripting",
        "severity": "medium"
    },
    "命令注入": {
        "tactic": "execution",
        "technique_id": "T1059",
        "technique_name": "Command and Scripting Interpreter",
        "severity": "critical"
    },
    "暴力破解": {
        "tactic": "credential_access",
        "technique_id": "T1110",
        "technique_name": "Brute Force",
        "severity": "high"
    },
    "端口扫描": {
        "tactic": "discovery",
        "technique_id": "T1046",
        "technique_name": "Network Service Scanning",
        "severity": "medium"
    },
    "SQLI": {
        "tactic": "initial_access",
        "technique_id": "T1190",
        "technique_name": "Exploitation of Remote Services",
        "severity": "high"
    },
    "DANGER": {
        "tactic": "execution",
        "technique_id": "T1059",
        "technique_name": "Command and Scripting Interpreter",
        "severity": "high"
    },
    "HARDCODED": {
        "tactic": "credential_access",
        "technique_id": "T1552",
        "technique_name": "Unsecured Credentials",
        "severity": "medium"
    },
    "PASSWORD": {
        "tactic": "credential_access",
        "technique_id": "T1552",
        "technique_name": "Unsecured Credentials",
        "severity": "high"
    },
    "PATH-TRAV": {
        "tactic": "initial_access",
        "technique_id": "T1190",
        "technique_name": "Path Traversal",
        "severity": "high"
    },
    "CMD-INJ": {
        "tactic": "execution",
        "technique_id": "T1059",
        "technique_name": "Command Injection",
        "severity": "critical"
    },
    "LOG-INJECT": {
        "tactic": "defense_evasion",
        "technique_id": "T1562",
        "technique_name": "Impair Defenses",
        "severity": "low"
    },
    "INSECURE": {
        "tactic": "defense_evasion",
        "technique_id": "T1562",
        "technique_name": "Insecure Design",
        "severity": "medium"
    },
    "innerHTML": {
        "tactic": "initial_access",
        "technique_id": "T1190",
        "technique_name": "Cross-site Scripting",
        "severity": "medium"
    },
    "eval": {
        "tactic": "execution",
        "technique_id": "T1059",
        "technique_name": "Dangerous Function",
        "severity": "high"
    },
    "traffic": {
        "tactic": "command_and_control",
        "technique_id": "T1071",
        "technique_name": "Application Layer Protocol",
        "severity": "medium"
    },
    "扫描": {
        "tactic": "discovery",
        "technique_id": "T1046",
        "technique_name": "Network Scanning",
        "severity": "low"
    },
    "攻击": {
        "tactic": "impact",
        "technique_id": "T1486",
        "technique_name": "Data Encrypted",
        "severity": "high"
    }
}


def get_attack_info(rule_id: str) -> dict:
    rule_id_upper = rule_id.upper()
    
    for key, mapping in ATTACK_TYPE_MAPPING.items():
        if key.upper() in rule_id_upper:
            tactic_info = MITRE_ATTACK_TACTICS.get(mapping["tactic"], {})
            return {
                "rule_id": rule_id,
                "tactic_id": mapping["tactic"],
                "tactic_name": tactic_info.get("name", "未知"),
                "technique_id": mapping.get("technique_id", ""),
                "technique_name": mapping.get("technique_name", ""),
                "mitre_url": f"https://attack.mitre.org/techniques/{mapping.get('technique_id', '')}"
            }
    
    return {
        "rule_id": rule_id,
        "tactic_id": "unknown",
        "tactic_name": "未知",
        "technique_id": "",
        "technique_name": "",
        "mitre_url": ""
    }


def get_all_tactics() -> list:
    return [
        {
            "id": tactic_id,
            "name": tactic_info["name"],
            "techniques": tactic_info["techniques"]
        }
        for tactic_id, tactic_info in MITRE_ATTACK_TACTICS.items()
    ]
