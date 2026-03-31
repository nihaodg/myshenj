import json
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings


class AIAdapter:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self.api_key = settings.AI_API_KEY
        self.base_url = settings.AI_BASE_URL
        self.model = settings.AI_MODEL
        self.timeout = settings.AI_TIMEOUT

    async def analyze(self, prompt: str, model: Optional[str] = None) -> str:
        if self.provider == "openai":
            return await self._analyze_openai(prompt, model)
        elif self.provider == "ollama":
            return await self._analyze_ollama(prompt, model)
        elif self.provider == "zhipu":
            return await self._analyze_zhipu(prompt, model)
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

    async def _analyze_openai(self, prompt: str, model: Optional[str] = None) -> str:
        model = model or self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.TimeoutException:
                raise TimeoutError("AI request timed out")
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"AI API error: {e.response.status_code}")

    async def _analyze_ollama(self, prompt: str, model: Optional[str] = None) -> str:
        model = model or self.model

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": model, "prompt": prompt}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
            except httpx.TimeoutException:
                raise TimeoutError("Ollama request timed out")
            except Exception as e:
                raise RuntimeError(f"Ollama error: {str(e)}")

    async def _analyze_zhipu(self, prompt: str, model: Optional[str] = None) -> str:
        model = model or "glm-4"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except httpx.TimeoutException:
                raise TimeoutError("Zhipu AI request timed out")
            except Exception as e:
                raise RuntimeError(f"Zhipu AI error: {str(e)}")

    async def analyze_json(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        try:
            response = await self.analyze(prompt, model)
            response = response.strip()

            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            response = response.strip()

            return json.loads(response)
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response as JSON", "raw": response[:500]}
        except Exception as e:
            return {"error": str(e)}


_code_audit_prompt_template = """你是一位安全专家，请分析以下{language}代码中的安全漏洞。

```{language}
{code}
```

请以JSON数组格式输出，每个漏洞包含：
- vuln_type: 漏洞类型（字符串）
- line: 行号（整数）
- severity: 风险等级（critical/high/medium/low）
- description: 漏洞描述
- recommendation: 修复建议

如果没有发现漏洞，返回空数组[]。
只返回JSON数组，不要包含其他内容。"""


_log_audit_prompt_template = """分析以下系统日志，识别可能的攻击行为。

返回JSON数组，每个攻击步骤包含：
- timestamp: 时间戳（字符串）
- ip: 相关IP地址（字符串）
- action: 攻击动作描述（字符串）
- description: 详细描述（字符串）
- severity: 严重程度（critical/high/medium/low）

日志内容：
{log_content}

只返回JSON数组，不要包含其他内容。"""


_traffic_audit_prompt_template = """分析以下网络流量摘要，判断是否存在攻击行为。

返回JSON数组，每个可疑会话包含：
- src_ip: 源IP（字符串）
- dst_ip: 目标IP（字符串）
- protocol: 协议（字符串）
- reason: 判断理由（字符串）
- severity: 可疑程度（critical/high/medium/low）

流量摘要：
{traffic_summary}

只返回JSON数组，不要包含其他内容。"""


def build_code_audit_prompt(code: str, language: str) -> str:
    code = code[:8000]
    return _code_audit_prompt_template.format(language=language, code=code)


def build_log_audit_prompt(log_content: str) -> str:
    log_content = log_content[:6000]
    return _log_audit_prompt_template.format(log_content=log_content)


def build_traffic_audit_prompt(traffic_summary: str) -> str:
    traffic_summary = traffic_summary[:6000]
    return _traffic_audit_prompt_template.format(traffic_summary=traffic_summary)
