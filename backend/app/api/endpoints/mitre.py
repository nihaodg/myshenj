from fastapi import APIRouter
from app.services.attack_mapping import (
    get_attack_info, 
    get_all_tactics,
    MITRE_ATTACK_TACTICS
)

router = APIRouter()


@router.get("/mitre/tactics")
async def get_tactics():
    return get_all_tactics()


@router.get("/mitre/tactics/{tactic_id}")
async def get_tactic_detail(tactic_id: str):
    tactic = MITRE_ATTACK_TACTICS.get(tactic_id)
    if not tactic:
        return {"error": "Tactic not found"}
    return {
        "id": tactic_id,
        "name": tactic["name"],
        "techniques": tactic["techniques"]
    }


@router.get("/mitre/classify/{rule_id}")
async def classify_attack(rule_id: str):
    return get_attack_info(rule_id)


@router.get("/mitre/all")
async def get_all_mitre_info():
    return {
        "tactics": get_all_tactics(),
        "mappings": {
            key: {
                "tactic_id": val["tactic"],
                "technique_id": val.get("technique_id", ""),
                "technique_name": val.get("technique_name", ""),
                "severity": val.get("severity", "medium")
            }
            for key, val in {
                "SQL注入": {"tactic": "initial_access", "technique_id": "T1190", "technique_name": "Exploitation of Remote Services", "severity": "high"},
                "XSS": {"tactic": "initial_access", "technique_id": "T1190", "technique_name": "Cross-site Scripting", "severity": "medium"},
                "命令注入": {"tactic": "execution", "technique_id": "T1059", "technique_name": "Command and Scripting Interpreter", "severity": "critical"},
                "暴力破解": {"tactic": "credential_access", "technique_id": "T1110", "technique_name": "Brute Force", "severity": "high"},
                "端口扫描": {"tactic": "discovery", "technique_id": "T1046", "technique_name": "Network Service Scanning", "severity": "medium"},
                "硬编码密钥": {"tactic": "credential_access", "technique_id": "T1552", "technique_name": "Unsecured Credentials", "severity": "medium"},
                "硬编码密码": {"tactic": "credential_access", "technique_id": "T1552", "technique_name": "Unsecured Credentials", "severity": "high"},
                "路径遍历": {"tactic": "initial_access", "technique_id": "T1190", "technique_name": "Path Traversal", "severity": "high"},
                "SQL注入检测": {"tactic": "initial_access", "technique_id": "T1190", "technique_name": "Exploitation of Remote Services", "severity": "high"},
            }.items()
        }
    }
