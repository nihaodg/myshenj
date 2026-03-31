import time
import smtplib
import logging
from typing import Optional, List, Dict
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertSystem:
    def __init__(self):
        self.config = {
            'web_notification': True,
            'email_notification': False,
            'smtp_server': '',
            'smtp_port': 587,
            'smtp_username': '',
            'smtp_password': '',
            'email_recipients': [],
            'min_severity': 'medium',
            'alert_throttling': True,
            'throttle_period': 300,
            'webhook_url': '',
            'webhook_enabled': False
        }
        self.alerts: List[Dict] = []
        self.recent_alerts: Dict[str, float] = {}

    def update_config(self, new_config: Dict):
        if new_config:
            for key in self.config:
                if key in new_config:
                    self.config[key] = new_config[key]
        return True

    def should_send_notification(self, alert_data: Dict) -> bool:
        severity_levels = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
        alert_severity = severity_levels.get(alert_data.get('severity', 'medium'), 1)
        config_min_severity = severity_levels.get(self.config['min_severity'], 1)

        if alert_severity < config_min_severity:
            return False

        if self.config['alert_throttling']:
            alert_key = f"{alert_data.get('src_ip', '')}_{alert_data.get('type', '')}"
            current_time = time.time()

            if alert_key in self.recent_alerts:
                last_time = self.recent_alerts[alert_key]
                if current_time - last_time < self.config['throttle_period']:
                    return False

            self.recent_alerts[alert_key] = current_time

        return True

    def process_alert(self, alert_data: Dict) -> bool:
        try:
            alert_data['timestamp'] = datetime.now().isoformat()
            self.alerts.append(alert_data)

            if len(self.alerts) > 1000:
                self.alerts = self.alerts[-1000:]

            should_notify = self.should_send_notification(alert_data)

            if should_notify:
                if self.config['webhook_enabled'] and self.config['webhook_url']:
                    self._send_webhook(alert_data)
                if self.config['email_notification']:
                    self._send_email(alert_data)

            self._cleanup_throttling()

            return True
        except Exception as e:
            logger.error(f"处理告警失败: {str(e)}")
            return False

    def _cleanup_throttling(self):
        current_time = time.time()
        expired_keys = [
            k for k, v in self.recent_alerts.items()
            if current_time - v >= self.config['throttle_period']
        ]
        for key in expired_keys:
            del self.recent_alerts[key]

    def _send_email(self, alert_data: Dict):
        if not self.config['email_recipients']:
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['smtp_username']
            msg['To'] = ', '.join(self.config['email_recipients'])
            msg['Subject'] = f"[{self.config.get('system_name', 'DeepAudit')}] 安全告警: {alert_data.get('severity', 'medium').upper()} - {alert_data.get('type', '未知')}"

            body = f"""
            <html><body>
                <h2>安全告警</h2>
                <p><strong>时间:</strong> {alert_data.get('timestamp', 'N/A')}</p>
                <p><strong>类型:</strong> {alert_data.get('type', '未知')}</p>
                <p><strong>严重程度:</strong> {alert_data.get('severity', 'medium')}</p>
                <p><strong>来源IP:</strong> {alert_data.get('src_ip', '未知')}</p>
                <p><strong>描述:</strong> {alert_data.get('message', '无描述')}</p>
                <p><strong>操作:</strong> {alert_data.get('action', '已记录')}</p>
            </body></html>
            """

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['smtp_username'], self.config['smtp_password'])
            server.send_message(msg)
            server.quit()

            logger.info(f"邮件告警发送成功")
        except Exception as e:
            logger.error(f"发送邮件告警失败: {str(e)}")

    def _send_webhook(self, alert_data: Dict):
        try:
            import requests
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"[{self.config.get('system_name', 'DeepAudit')}] 告警\n严重程度: {alert_data.get('severity', 'medium').upper()}\n类型: {alert_data.get('type', '未知')}\n来源: {alert_data.get('src_ip', '未知')}\n描述: {alert_data.get('message', '无')}"
                }
            }
            requests.post(self.config['webhook_url'], json=payload, timeout=5)
        except Exception as e:
            logger.error(f"发送Webhook告警失败: {str(e)}")

    def get_recent_alerts(self, limit: int = 100) -> List[Dict]:
        return self.alerts[-limit:] if self.alerts else []

    def get_alert_stats(self) -> Dict:
        total = len(self.alerts)
        severity_stats = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        type_stats = {}

        for alert in self.alerts:
            sev = alert.get('severity', 'medium').lower()
            if sev in severity_stats:
                severity_stats[sev] += 1
            alert_type = alert.get('type', 'unknown')
            type_stats[alert_type] = type_stats.get(alert_type, 0) + 1

        return {
            'total': total,
            'severity': severity_stats,
            'types': type_stats
        }

    def create_alert(self, alert_type: str, severity: str, message: str,
                    src_ip: str = None, action: str = "已记录") -> Dict:
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'src_ip': src_ip,
            'action': action,
            'timestamp': datetime.now().isoformat()
        }
        self.process_alert(alert)
        return alert


alert_system = AlertSystem()
