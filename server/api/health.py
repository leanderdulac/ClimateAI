"""
Módulo de Health Checks para monitoramento de saúde da aplicação
Verifica status de Database, Redis, APIs externas e componentes críticos
"""

import asyncio
import logging
import socket
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import psutil

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Estados possíveis de um serviço"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """Resultado de um health check"""

    def __init__(
        self,
        name: str,
        status: ServiceStatus = ServiceStatus.UNKNOWN,
        message: str = "",
        response_time_ms: float = 0,
        details: Dict[str, Any] = None,
    ):
        self.name = name
        self.status = status
        self.message = message
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": round(self.response_time_ms, 2),
            "timestamp": self.timestamp,
            "details": self.details,
        }


class DatabaseHealthCheck:
    """Health check para Database"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.name = "database"

    async def check(self) -> HealthCheckResult:
        """Verifica saúde do database"""
        start_time = datetime.now()

        try:
            # Importar engine do SQLAlchemy
            from sqlalchemy import create_engine, text

            engine = create_engine(self.database_url)

            # Teste de conexão
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.HEALTHY,
                message="Database connection successful",
                response_time_ms=elapsed,
                details={"driver": "PostgreSQL/SQLite"},
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Database health check failed: {str(e)}")

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                response_time_ms=elapsed,
                details={"error": str(e)},
            )


class RedisHealthCheck:
    """Health check para Redis"""

    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.name = "redis"

    async def check(self) -> HealthCheckResult:
        """Verifica saúde do Redis"""
        start_time = datetime.now()

        try:
            # Tentar importar redis
            try:
                import redis
            except ImportError:
                return HealthCheckResult(
                    name=self.name,
                    status=ServiceStatus.UNKNOWN,
                    message="Redis library not installed",
                    response_time_ms=0,
                    details={"installed": False},
                )

            # Conectar ao Redis
            r = redis.from_url(self.redis_url, socket_timeout=2)
            r.ping()

            # Pegar informações do Redis
            info = r.info()

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.HEALTHY,
                message="Redis connection successful",
                response_time_ms=elapsed,
                details={
                    "version": info.get("redis_version", "unknown"),
                    "memory_usage_mb": round(
                        info.get("used_memory", 0) / 1024 / 1024, 2
                    ),
                    "connected_clients": info.get("connected_clients", 0),
                },
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.warning(f"Redis health check failed: {str(e)}")

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.DEGRADED,
                message=f"Redis not available: {str(e)}",
                response_time_ms=elapsed,
                details={"error": str(e)},
            )


class SystemHealthCheck:
    """Health check para recursos do sistema"""

    def __init__(self):
        self.name = "system"

    async def check(self) -> HealthCheckResult:
        """Verifica saúde do sistema"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            # Determinar status
            status = ServiceStatus.HEALTHY
            if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
                status = ServiceStatus.DEGRADED

            return HealthCheckResult(
                name=self.name,
                status=status,
                message="System resources check completed",
                response_time_ms=0,
                details={
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(memory.percent, 2),
                    "memory_available_mb": round(memory.available / 1024 / 1024, 2),
                    "disk_percent": round(disk.percent, 2),
                    "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                },
            )

        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.UNKNOWN,
                message=f"System check failed: {str(e)}",
                details={"error": str(e)},
            )


class APIHealthCheck:
    """Health check para APIs externas"""

    def __init__(self):
        self.name = "external_apis"

    async def check(self) -> HealthCheckResult:
        """Verifica saúde de APIs externas críticas"""
        start_time = datetime.now()
        api_results = {}

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                # Verificar Open-Meteo (Weather API)
                try:
                    async with session.get(
                        "https://api.open-meteo.com/v1/forecast",
                        params={
                            "latitude": 0,
                            "longitude": 0,
                            "current": "temperature_2m",
                        },
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as resp:
                        api_results["open_meteo"] = (
                            "healthy" if resp.status == 200 else "unhealthy"
                        )
                except Exception as e:
                    api_results["open_meteo"] = f"error: {str(e)}"

        except ImportError:
            logger.warning("aiohttp not installed, skipping external API checks")
            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.UNKNOWN,
                message="aiohttp library not installed",
                details={"installed": False},
            )

        elapsed = (datetime.now() - start_time).total_seconds() * 1000

        # Determinar status geral
        unhealthy_count = sum(1 for v in api_results.values() if "error" in str(v))
        status = ServiceStatus.HEALTHY
        if unhealthy_count > 0:
            status = ServiceStatus.DEGRADED

        return HealthCheckResult(
            name=self.name,
            status=status,
            message="External APIs check completed",
            response_time_ms=elapsed,
            details=api_results,
        )


class HealthChecker:
    """Gerenciador central de health checks"""

    def __init__(self, database_url: str = None, redis_url: str = None):
        self.database_url = database_url
        self.redis_url = redis_url
        self.checks = {}
        self._initialize_checks()

    def _initialize_checks(self):
        """Inicializa todos os health checks"""
        self.checks["system"] = SystemHealthCheck()

        if self.database_url:
            self.checks["database"] = DatabaseHealthCheck(self.database_url)

        if self.redis_url:
            self.checks["redis"] = RedisHealthCheck(self.redis_url)

        self.checks["external_apis"] = APIHealthCheck()

    async def check_all(self) -> Dict[str, Any]:
        """Executa todos os health checks"""
        results = {}
        overall_status = ServiceStatus.HEALTHY

        # Executar checks em paralelo
        tasks = [check.check() for check in self.checks.values()]
        check_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(check_results):
            if isinstance(result, Exception):
                logger.error(f"Health check error: {result}")
                continue

            results[result.name] = result.to_dict()

            # Atualizar status geral
            if result.status == ServiceStatus.UNHEALTHY:
                overall_status = ServiceStatus.UNHEALTHY
            elif (
                result.status == ServiceStatus.DEGRADED
                and overall_status != ServiceStatus.UNHEALTHY
            ):
                overall_status = ServiceStatus.DEGRADED

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
            "summary": {
                "total_checks": len(results),
                "healthy": sum(1 for r in results.values() if r["status"] == "healthy"),
                "degraded": sum(
                    1 for r in results.values() if r["status"] == "degraded"
                ),
                "unhealthy": sum(
                    1 for r in results.values() if r["status"] == "unhealthy"
                ),
            },
        }

    async def check_critical(self) -> Dict[str, Any]:
        """Executa apenas checks críticos (database, system)"""
        results = {}

        for name in ["database", "system"]:
            if name in self.checks:
                result = await self.checks[name].check()
                results[name] = result.to_dict()

        overall_status = ServiceStatus.HEALTHY
        for result in results.values():
            if result["status"] == ServiceStatus.UNHEALTHY.value:
                overall_status = ServiceStatus.UNHEALTHY
                break

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
        }


async def get_health_checker(
    database_url: str = None, redis_url: str = None
) -> HealthChecker:
    """Factory para criar HealthChecker"""
    return HealthChecker(database_url, redis_url)
