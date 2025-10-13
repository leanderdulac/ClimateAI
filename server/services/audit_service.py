"""
Audit and Compliance Service
Provides comprehensive logging and audit trails for insurance operations
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import os
from pathlib import Path
import uuid
import sqlite3
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

class AuditComplianceService:
    """
    Service for comprehensive audit logging and compliance tracking.
    Maintains detailed logs of all insurance operations, risk assessments,
    and decision-making processes.
    """

    def __init__(self, db_path: str = "data/audit.db", log_retention_days: int = 2555):  # 7 years
        self.db_path = db_path
        self.log_retention_days = log_retention_days
        self._lock = threading.Lock()

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._init_database()

        # Start cleanup thread
        self._start_cleanup_thread()

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self):
        """Initialize the audit database schema"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT,
                    operation TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    risk_score REAL,
                    compliance_flags TEXT,
                    created_at REAL
                )
            ''')

            # Compliance rules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_rules (
                    id TEXT PRIMARY KEY,
                    rule_name TEXT NOT NULL,
                    rule_type TEXT NOT NULL,
                    description TEXT,
                    conditions TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at REAL,
                    updated_at REAL
                )
            ''')

            # Compliance violations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_violations (
                    id TEXT PRIMARY KEY,
                    rule_id TEXT,
                    audit_log_id TEXT,
                    violation_details TEXT,
                    severity TEXT,
                    status TEXT DEFAULT 'open',
                    resolved_at REAL,
                    resolved_by TEXT,
                    created_at REAL,
                    FOREIGN KEY (rule_id) REFERENCES compliance_rules (id),
                    FOREIGN KEY (audit_log_id) REFERENCES audit_logs (id)
                )
            ''')

            # Risk assessment logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS risk_assessments (
                    id TEXT PRIMARY KEY,
                    audit_log_id TEXT,
                    location_lat REAL,
                    location_lon REAL,
                    asset_value REAL,
                    risk_factors TEXT,
                    calculated_risk REAL,
                    confidence_level REAL,
                    assessment_method TEXT,
                    ml_prediction TEXT,
                    created_at REAL,
                    FOREIGN KEY (audit_log_id) REFERENCES audit_logs (id)
                )
            ''')

            # Policy decision logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS policy_decisions (
                    id TEXT PRIMARY KEY,
                    audit_log_id TEXT,
                    policy_type TEXT,
                    coverage_amount REAL,
                    premium_amount REAL,
                    risk_adjustment REAL,
                    decision_reason TEXT,
                    approved_by TEXT,
                    decision_timestamp REAL,
                    created_at REAL,
                    FOREIGN KEY (audit_log_id) REFERENCES audit_logs (id)
                )
            ''')

            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    audit_log_id TEXT,
                    operation TEXT,
                    details TEXT,
                    timestamp TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0,
                    resolved INTEGER DEFAULT 0,
                    FOREIGN KEY (audit_log_id) REFERENCES audit_logs (id)
                )
            ''')

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_operation ON audit_logs(operation)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_compliance_violations_status ON compliance_violations(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(resolved)')

            conn.commit()

    def _start_cleanup_thread(self):
        """Start background thread for log cleanup"""
        def cleanup_worker():
            while True:
                try:
                    self._cleanup_old_logs()
                except Exception as e:
                    logger.error(f"Error in cleanup worker: {e}")
                # Run cleanup daily
                import time
                time.sleep(86400)

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()

    def _cleanup_old_logs(self):
        """Remove logs older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.log_retention_days)
        cutoff_timestamp = cutoff_date.timestamp()

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Delete old records (cascade will handle related tables)
            cursor.execute('DELETE FROM audit_logs WHERE created_at < ?', (cutoff_timestamp,))
            deleted_count = cursor.rowcount

            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old audit log entries")

    def log_operation(self,
                     operation: str,
                     resource_type: str,
                     action: str,
                     status: str = 'success',
                     user_id: Optional[str] = None,
                     session_id: Optional[str] = None,
                     resource_id: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     ip_address: Optional[str] = None,
                     user_agent: Optional[str] = None,
                     risk_score: Optional[float] = None,
                     compliance_flags: Optional[List[str]] = None) -> str:
        """
        Log an operation for audit purposes

        Args:
            operation: Type of operation (e.g., 'risk_assessment', 'policy_creation')
            resource_type: Type of resource (e.g., 'policy', 'location', 'user')
            action: Specific action performed
            status: Operation status ('success', 'failure', 'warning')
            user_id: ID of the user performing the operation
            session_id: Session identifier
            resource_id: ID of the affected resource
            details: Additional operation details
            ip_address: Client IP address
            user_agent: Client user agent
            risk_score: Associated risk score if applicable
            compliance_flags: List of compliance flags triggered

        Returns:
            Audit log entry ID
        """
        audit_id = str(uuid.uuid4())

        with self._lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO audit_logs (
                        id, timestamp, user_id, session_id, operation, resource_type,
                        resource_id, action, status, details, ip_address, user_agent,
                        risk_score, compliance_flags, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    audit_id,
                    datetime.now().isoformat(),
                    user_id,
                    session_id,
                    operation,
                    resource_type,
                    resource_id,
                    action,
                    status,
                    json.dumps(details) if details else None,
                    ip_address,
                    user_agent,
                    risk_score,
                    json.dumps(compliance_flags) if compliance_flags else None,
                    datetime.now().timestamp()
                ))

                conn.commit()

        # Check for compliance violations
        if compliance_flags:
            self._check_compliance_violations(audit_id, compliance_flags, details or {})

        # Check for alerts after logging
        self._check_for_alerts(audit_id, operation, status, risk_score, compliance_flags)

        logger.info(f"Audit log created: {operation} - {action} - {status} (ID: {audit_id})")
        return audit_id

    def log_risk_assessment(self,
                           audit_log_id: str,
                           location_lat: float,
                           location_lon: float,
                           asset_value: float,
                           risk_factors: Dict[str, Any],
                           calculated_risk: float,
                           confidence_level: float,
                           assessment_method: str = 'rule_based',
                           ml_prediction: Optional[Dict[str, Any]] = None):
        """
        Log a risk assessment operation

        Args:
            audit_log_id: Associated audit log entry ID
            location_lat, location_lon: Location coordinates
            asset_value: Value of the asset being assessed
            risk_factors: Risk factors used in assessment
            calculated_risk: Final risk score
            confidence_level: Confidence in the assessment
            assessment_method: Method used ('rule_based', 'ml', 'hybrid')
            ml_prediction: ML model prediction details if used
        """
        with self._lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO risk_assessments (
                        id, audit_log_id, location_lat, location_lon, asset_value,
                        risk_factors, calculated_risk, confidence_level, assessment_method,
                        ml_prediction, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    audit_log_id,
                    location_lat,
                    location_lon,
                    asset_value,
                    json.dumps(risk_factors),
                    calculated_risk,
                    confidence_level,
                    assessment_method,
                    json.dumps(ml_prediction) if ml_prediction else None,
                    datetime.now().timestamp()
                ))

                conn.commit()

    def log_policy_decision(self,
                           audit_log_id: str,
                           policy_type: str,
                           coverage_amount: float,
                           premium_amount: float,
                           risk_adjustment: float,
                           decision_reason: str,
                           approved_by: Optional[str] = None):
        """
        Log a policy decision

        Args:
            audit_log_id: Associated audit log entry ID
            policy_type: Type of insurance policy
            coverage_amount: Amount of coverage provided
            premium_amount: Premium charged
            risk_adjustment: Risk-based adjustment factor
            decision_reason: Reason for the decision
            approved_by: User who approved the policy
        """
        with self._lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO policy_decisions (
                        id, audit_log_id, policy_type, coverage_amount, premium_amount,
                        risk_adjustment, decision_reason, approved_by, decision_timestamp, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    audit_log_id,
                    policy_type,
                    coverage_amount,
                    premium_amount,
                    risk_adjustment,
                    decision_reason,
                    approved_by,
                    datetime.now().timestamp(),
                    datetime.now().timestamp()
                ))

                conn.commit()

    def _check_compliance_violations(self, audit_log_id: str, flags: List[str], details: Dict[str, Any]):
        """Check for compliance violations based on triggered flags"""
        with self._lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Get active compliance rules
                cursor.execute('SELECT * FROM compliance_rules WHERE is_active = 1')
                rules = cursor.fetchall()

                for rule in rules:
                    rule_dict = dict(zip([desc[0] for desc in cursor.description], rule))

                    # Simple rule checking (can be made more sophisticated)
                    if self._evaluate_rule(rule_dict, flags, details):
                        # Create violation record
                        violation_id = str(uuid.uuid4())
                        cursor.execute('''
                            INSERT INTO compliance_violations (
                                id, rule_id, audit_log_id, violation_details, severity,
                                status, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            violation_id,
                            rule_dict['id'],
                            audit_log_id,
                            json.dumps({
                                'rule_name': rule_dict['rule_name'],
                                'triggered_flags': flags,
                                'details': details
                            }),
                            rule_dict['severity'],
                            'open',
                            datetime.now().timestamp()
                        ))

                        logger.warning(f"Compliance violation detected: {rule_dict['rule_name']} (ID: {violation_id})")

                conn.commit()

    def _evaluate_rule(self, rule: Dict[str, Any], flags: List[str], details: Dict[str, Any]) -> bool:
        """Evaluate if a compliance rule is violated"""
        # Simple flag-based evaluation (can be extended with complex logic)
        conditions = json.loads(rule['conditions']) if isinstance(rule['conditions'], str) else rule['conditions']

        if 'required_flags' in conditions:
            required_flags = conditions['required_flags']
            if isinstance(required_flags, list):
                return any(flag in flags for flag in required_flags)

        if 'risk_threshold' in conditions:
            risk_score = details.get('risk_score', 0)
            return risk_score > conditions['risk_threshold']

        return False

    def add_compliance_rule(self,
                           rule_name: str,
                           rule_type: str,
                           description: str,
                           conditions: Dict[str, Any],
                           severity: str = 'medium') -> str:
        """
        Add a new compliance rule

        Args:
            rule_name: Name of the rule
            rule_type: Type of rule (e.g., 'risk_threshold', 'flag_based')
            description: Human-readable description
            conditions: Rule conditions as a dictionary
            severity: Severity level ('low', 'medium', 'high', 'critical')

        Returns:
            Rule ID
        """
        rule_id = str(uuid.uuid4())
        now = datetime.now().timestamp()

        with self._lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO compliance_rules (
                        id, rule_name, rule_type, description, conditions,
                        severity, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule_id,
                    rule_name,
                    rule_type,
                    description,
                    json.dumps(conditions),
                    severity,
                    1,  # Active by default
                    now,
                    now
                ))

                conn.commit()

        logger.info(f"Compliance rule added: {rule_name} (ID: {rule_id})")
        return rule_id

    def get_audit_logs(self,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      operation: Optional[str] = None,
                      user_id: Optional[str] = None,
                      status: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with optional filtering

        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            operation: Filter by operation type
            user_id: Filter by user ID
            status: Filter by status
            limit: Maximum number of records to return

        Returns:
            List of audit log entries
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT * FROM audit_logs WHERE 1=1
            '''
            params = []

            if start_date:
                query += ' AND created_at >= ?'
                params.append(start_date.timestamp())

            if end_date:
                query += ' AND created_at <= ?'
                params.append(end_date.timestamp())

            if operation:
                query += ' AND operation = ?'
                params.append(operation)

            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)

            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert to dictionaries
            columns = [desc[0] for desc in cursor.description]
            logs = []

            for row in rows:
                log_dict = dict(zip(columns, row))

                # Parse JSON fields
                if log_dict['details']:
                    log_dict['details'] = json.loads(log_dict['details'])
                if log_dict['compliance_flags']:
                    log_dict['compliance_flags'] = json.loads(log_dict['compliance_flags'])

                logs.append(log_dict)

            return logs

    def get_compliance_report(self,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate a compliance report

        Args:
            start_date: Start date for the report
            end_date: End date for the report

        Returns:
            Compliance report with violations and statistics
        """
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Build date filter
            date_filter = ""
            params = []

            if start_date:
                date_filter += " AND v.created_at >= ?"
                params.append(start_date.timestamp())

            if end_date:
                date_filter += " AND v.created_at <= ?"
                params.append(end_date.timestamp())

            # Get violations
            cursor.execute(f'''
                SELECT v.*, r.rule_name, r.severity as rule_severity, r.description as rule_description
                FROM compliance_violations v
                LEFT JOIN compliance_rules r ON v.rule_id = r.id
                WHERE 1=1 {date_filter}
                ORDER BY v.created_at DESC
            ''', params)

            violations = []
            for row in cursor.fetchall():
                violation = dict(zip([desc[0] for desc in cursor.description], row))
                if violation['violation_details']:
                    violation['violation_details'] = json.loads(violation['violation_details'])
                violations.append(violation)

            # Get summary statistics
            cursor.execute(f'''
                SELECT
                    COUNT(*) as total_violations,
                    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_violations,
                    COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_violations,
                    COUNT(CASE WHEN severity = 'high' THEN 1 END) as high_violations
                FROM compliance_violations v
                WHERE 1=1 {date_filter}
            ''', params)

            stats = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))

            return {
                'report_period': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                },
                'summary': stats,
                'violations': violations,
                'generated_at': datetime.now().isoformat()
            }

    def resolve_violation(self, violation_id: str, resolved_by: str, notes: Optional[str] = None):
        """
        Mark a compliance violation as resolved

        Args:
            violation_id: ID of the violation to resolve
            resolved_by: User who resolved the violation
            notes: Optional resolution notes
        """
        with self._lock:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE compliance_violations
                    SET status = 'resolved', resolved_at = ?, resolved_by = ?,
                        violation_details = json_set(violation_details, '$.resolution_notes', ?)
                    WHERE id = ?
                ''', (
                    datetime.now().timestamp(),
                    resolved_by,
                    notes,
                    violation_id
                ))

                conn.commit()

        logger.info(f"Compliance violation resolved: {violation_id} by {resolved_by}")

    def _check_for_alerts(self, audit_log_id: str, operation: str, status: str,
                         risk_score: Optional[float] = None,
                         compliance_flags: Optional[List[str]] = None):
        """Check for conditions that should trigger alerts"""
        alerts = []

        # High risk score alert
        if risk_score and risk_score > 0.8:
            alerts.append({
                'type': 'high_risk',
                'severity': 'high',
                'message': f'Alta pontuação de risco detectada: {risk_score:.2f}',
                'audit_log_id': audit_log_id,
                'operation': operation
            })

        # Operation failure alert
        if status == 'error':
            alerts.append({
                'type': 'operation_failure',
                'severity': 'medium',
                'message': f'Falha na operação: {operation}',
                'audit_log_id': audit_log_id,
                'operation': operation
            })

        # Compliance violation alert
        if compliance_flags and len(compliance_flags) > 0:
            alerts.append({
                'type': 'compliance_violation',
                'severity': 'critical',
                'message': f'Violações de compliance detectadas: {", ".join(compliance_flags)}',
                'audit_log_id': audit_log_id,
                'operation': operation,
                'compliance_flags': compliance_flags
            })

        # Suspicious activity patterns
        suspicious_patterns = self._check_suspicious_patterns(operation, audit_log_id)
        alerts.extend(suspicious_patterns)

        # Create alerts in database
        for alert in alerts:
            self._create_alert(alert)

    def _check_suspicious_patterns(self, operation: str, audit_log_id: str) -> List[Dict[str, Any]]:
        """Check for suspicious activity patterns"""
        alerts = []

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Check for rapid successive operations (potential abuse)
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM audit_logs
                WHERE operation = ?
                AND timestamp > datetime('now', '-1 hour')
            """, (operation,))

            recent_count = cursor.fetchone()[0]
            if recent_count > 10:  # More than 10 operations of same type in 1 hour
                alerts.append({
                    'type': 'suspicious_activity',
                    'severity': 'medium',
                    'message': f'Atividade suspeita detectada: {recent_count} operações {operation} em 1 hora',
                    'audit_log_id': audit_log_id,
                    'operation': operation
                })

            # Check for failed operations rate
            cursor.execute("""
                SELECT
                    COUNT(CASE WHEN status = 'error' THEN 1 END) * 1.0 / COUNT(*) as error_rate
                FROM audit_logs
                WHERE operation = ?
                AND timestamp > datetime('now', '-24 hours')
            """, (operation,))

            result = cursor.fetchone()
            if result and result[0] and result[0] > 0.5:  # More than 50% error rate
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'high',
                    'message': f'Taxa de erro elevada: {result[0]:.1%} para operação {operation}',
                    'audit_log_id': audit_log_id,
                    'operation': operation
                })

        return alerts

    def _create_alert(self, alert_data: Dict[str, Any]):
        """Create an alert in the database"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO alerts (
                    id, type, severity, message, audit_log_id, operation,
                    details, timestamp, acknowledged, resolved
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
            """, (
                str(uuid.uuid4()),
                alert_data['type'],
                alert_data['severity'],
                alert_data['message'],
                alert_data['audit_log_id'],
                alert_data['operation'],
                json.dumps({
                    'compliance_flags': alert_data.get('compliance_flags', []),
                    'additional_data': alert_data.get('additional_data', {})
                }),
                datetime.now().isoformat(),
            ))

            conn.commit()

            # Log alert creation
            logger.warning(f"Alert created: {alert_data['type']} - {alert_data['message']}")

    def get_alerts(self, acknowledged: Optional[bool] = None,
                   resolved: Optional[bool] = None,
                   severity: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            query = """
                SELECT id, type, severity, message, audit_log_id, operation,
                       details, timestamp, acknowledged, resolved
                FROM alerts
                WHERE 1=1
            """
            params = []

            if acknowledged is not None:
                query += " AND acknowledged = ?"
                params.append(1 if acknowledged else 0)

            if resolved is not None:
                query += " AND resolved = ?"
                params.append(1 if resolved else 0)

            if severity:
                query += " AND severity = ?"
                params.append(severity)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            alerts = []
            for row in cursor.fetchall():
                alert = {
                    'id': row[0],
                    'type': row[1],
                    'severity': row[2],
                    'message': row[3],
                    'audit_log_id': row[4],
                    'operation': row[5],
                    'details': json.loads(row[6]) if row[6] else {},
                    'timestamp': row[7],
                    'acknowledged': bool(row[8]),
                    'resolved': bool(row[9])
                }
                alerts.append(alert)

            return alerts

    def acknowledge_alert(self, alert_id: str):
        """Mark an alert as acknowledged"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE alerts SET acknowledged = 1 WHERE id = ?",
                (alert_id,)
            )
            conn.commit()

    def resolve_alert(self, alert_id: str, resolution_notes: Optional[str] = None):
        """Mark an alert as resolved"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE alerts
                SET resolved = 1, details = json_set(details, '$.resolution_notes', ?)
                WHERE id = ?
            """, (resolution_notes or '', alert_id))
            conn.commit()

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alerts"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Count by severity and status
            cursor.execute("""
                SELECT
                    severity,
                    acknowledged,
                    resolved,
                    COUNT(*) as count
                FROM alerts
                WHERE 1=1
                GROUP BY severity, acknowledged, resolved
            """)

            summary = {
                'total_alerts': 0,
                'unacknowledged_alerts': 0,
                'unresolved_alerts': 0,
                'by_severity': {
                    'critical': 0,
                    'high': 0,
                    'medium': 0,
                    'low': 0
                },
                'by_type': {}
            }

            for row in cursor.fetchall():
                severity, acknowledged, resolved, count = row
                summary['total_alerts'] += count

                if not acknowledged:
                    summary['unacknowledged_alerts'] += count

                if not resolved:
                    summary['unresolved_alerts'] += count

                if severity in summary['by_severity']:
                    summary['by_severity'][severity] += count

            # Count by type
            cursor.execute("""
                SELECT type, COUNT(*) as count
                FROM alerts
                WHERE resolved = 0
                GROUP BY type
            """)

            for row in cursor.fetchall():
                alert_type, count = row
                summary['by_type'][alert_type] = count

            return summary

    def get_alert_stats(self) -> Dict:
        """Get alert statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get total alerts
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total_alerts = cursor.fetchone()[0]

            # Get unacknowledged alerts
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")
            unacknowledged = cursor.fetchone()[0]

            # Get unresolved alerts
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE resolved = 0")
            unresolved = cursor.fetchone()[0]

            # Get alerts by severity
            cursor.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
            severity_counts = dict(cursor.fetchall())

            # Get recent alerts (last 24 hours)
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp > ?", (yesterday.isoformat(),))
            recent_alerts = cursor.fetchone()[0]

            conn.close()

            return {
                "total_alerts": total_alerts,
                "unacknowledged": unacknowledged,
                "unresolved": unresolved,
                "severity_counts": severity_counts,
                "recent_alerts": recent_alerts
            }

        except Exception as e:
            logger.error(f"Error getting alert stats: {e}")
            return {
                "total_alerts": 0,
                "unacknowledged": 0,
                "unresolved": 0,
                "severity_counts": {},
                "recent_alerts": 0
            }

# Global instance
audit_service = AuditComplianceService()

# Convenience functions
def log_operation(operation: str, resource_type: str, action: str, **kwargs) -> str:
    """Log an operation"""
    return audit_service.log_operation(operation, resource_type, action, **kwargs)

def log_risk_assessment(audit_log_id: str, **kwargs):
    """Log a risk assessment"""
    audit_service.log_risk_assessment(audit_log_id, **kwargs)

def log_policy_decision(audit_log_id: str, **kwargs):
    """Log a policy decision"""
    audit_service.log_policy_decision(audit_log_id, **kwargs)

def get_audit_logs(**kwargs) -> List[Dict[str, Any]]:
    """Get audit logs"""
    return audit_service.get_audit_logs(**kwargs)

def get_compliance_report(**kwargs) -> Dict[str, Any]:
    """Get compliance report"""
    return audit_service.get_compliance_report(**kwargs)

def add_compliance_rule(**kwargs) -> str:
    """Add a compliance rule"""
    return audit_service.add_compliance_rule(**kwargs)