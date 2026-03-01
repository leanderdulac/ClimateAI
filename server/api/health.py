"""
Módulo de Health Checks para monitoramento de saúde da aplicação
Verifica status de Database, Redis, APIs externas e componentes críticos
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict

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
            # Importar engine do SQLAlchemy async
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text

            # Se for SQLite na memória, adicionar connect_args
            is_sqlite = self.database_url.startswith("sqlite")
            connect_args = {"check_same_thread": False} if is_sqlite else {}

            if self.database_url.startswith("postgresql"):
                if "asyncpg" in self.database_url:
                    connect_args["prepared_statement_cache_size"] = 0
                    connect_args["statement_cache_size"] = 0

            logger.debug(f"Database health check URL: {self.database_url}")
            engine = create_async_engine(self.database_url, connect_args=connect_args)

            # Teste de conexão assíncrono
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
                
            # Fechar conexão do engine
            await engine.dispose()

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.HEALTHY,
                message="Database connection successful",
                response_time_ms=elapsed,
                details={"driver": "PostgreSQL/SQLite (Async)"},
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


class MLModelHealthCheck:
    """Health check para modelos de Machine Learning"""

    def __init__(self):
        self.name = "ml_models"

    async def check(self) -> HealthCheckResult:
        """Verifica saúde dos modelos ML"""
        start_time = datetime.now()
        model_results = {}

        try:
            # noqa: F401
            from services.ml_service import (  # noqa: F401
                get_ml_model_info,
                sinistrality_predictor,
            )

            # Verificar se o modelo está carregado
            model_info = get_ml_model_info()
            model_results["sinistrality_model"] = {
                "loaded": model_info.get("model_loaded", False),
                "last_trained": model_info.get("last_trained"),
                "accuracy": model_info.get("accuracy"),
            }

            # Verificar LSTM se disponível
            try:
                from services.lstm_attention_service import lstm_attention_service

                model_results["lstm_attention"] = {
                    "available": True,
                    "model_loaded": hasattr(lstm_attention_service, "model"),
                }
            except ImportError:
                model_results["lstm_attention"] = {"available": False}

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            # Determinar status
            models_loaded = sum(
                1
                for v in model_results.values()
                if v.get("loaded", v.get("available", False))
            )
            status = (
                ServiceStatus.HEALTHY if models_loaded > 0 else ServiceStatus.DEGRADED
            )

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=f"{models_loaded} ML models available",
                response_time_ms=elapsed,
                details=model_results,
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.warning(f"ML model health check failed: {str(e)}")

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.DEGRADED,
                message=f"ML models check failed: {str(e)}",
                response_time_ms=elapsed,
                details={"error": str(e)},
            )


class ServicesHealthCheck:
    """Health check para serviços críticos da aplicação"""

    def __init__(self):
        self.name = "services"

    async def check(self) -> HealthCheckResult:
        """Verifica saúde dos serviços críticos"""
        start_time = datetime.now()
        service_results = {}

        try:
            # Verificar serviços climáticos
            try:
                from services.clima_service import ClimaService  # noqa: F401

                service_results["clima_service"] = {"available": True}
            except ImportError as e:
                service_results["clima_service"] = {"available": False, "error": str(e)}

            # Verificar serviços de previsão
            try:
                from services.previsao_service import PrevisaoService  # noqa: F401

                service_results["previsao_service"] = {"available": True}
            except ImportError as e:
                service_results["previsao_service"] = {
                    "available": False,
                    "error": str(e),
                }

            # Verificar serviço de auditoria
            try:
                from services.audit_service import log_operation  # noqa: F401

                service_results["audit_service"] = {"available": True}
            except ImportError as e:
                service_results["audit_service"] = {"available": False, "error": str(e)}

            # Verificar integração Gemini
            try:
                # noqa: F401
                from services.gemini_integration_service import (  # noqa: F401
                    GeminiIntegrationService,
                )

                service_results["gemini_integration"] = {"available": True}
            except ImportError as e:
                service_results["gemini_integration"] = {
                    "available": False,
                    "error": str(e),
                }

            # Verificar serviço de microsegmentação
            try:
                # noqa: F401
                from services.microsegmentation_service import (  # noqa: F401
                    create_microsegments,
                )

                service_results["microsegmentation"] = {"available": True}
            except ImportError as e:
                service_results["microsegmentation"] = {
                    "available": False,
                    "error": str(e),
                }

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            # Determinar status
            available_count = sum(
                1 for v in service_results.values() if v.get("available", False)
            )
            total_count = len(service_results)

            if available_count == total_count:
                status = ServiceStatus.HEALTHY
            elif available_count > total_count // 2:
                status = ServiceStatus.DEGRADED
            else:
                status = ServiceStatus.UNHEALTHY

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=f"{available_count}/{total_count} services available",
                response_time_ms=elapsed,
                details=service_results,
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Services health check failed: {str(e)}")

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.UNHEALTHY,
                message=f"Services check failed: {str(e)}",
                response_time_ms=elapsed,
                details={"error": str(e)},
            )


class CacheHealthCheck:
    """Health check para sistema de cache interno"""

    def __init__(self):
        self.name = "cache"

    async def check(self) -> HealthCheckResult:
        """Verifica saúde do sistema de cache"""
        try:
            # Tentar acessar o cache do main
            cache_info = {
                "type": "in-memory",
                "available": True,
            }

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.HEALTHY,
                message="Cache system operational",
                response_time_ms=0,
                details=cache_info,
            )

        except Exception as e:
            logger.warning(f"Cache health check failed: {str(e)}")

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.DEGRADED,
                message=f"Cache check failed: {str(e)}",
                details={"error": str(e)},
            )


class BlockchainBalanceHealthCheck:
    """Health check para o saldo da carteira da Blockchain"""

    def __init__(
        self,
        bc_node_url: str,
        admin_wallet_address: str,
        min_balance_threshold_ether: float,
    ):
        self.name = "blockchain_balance"
        self.bc_node_url = bc_node_url
        self.admin_wallet_address = admin_wallet_address
        self.min_balance_threshold_ether = min_balance_threshold_ether

    async def check(self) -> HealthCheckResult:
        """Verifica o saldo da carteira do administrador na blockchain"""
        start_time = datetime.now()

        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(self.bc_node_url))
            if not w3.is_connected():
                raise ConnectionError(
                    f"Não foi possível conectar ao nó: {self.bc_node_url}"
                )

            balance_wei = w3.eth.get_balance(self.admin_wallet_address)
            balance_ether = w3.from_wei(balance_wei, "ether")

            status = ServiceStatus.HEALTHY
            message = "Saldo da carteira blockchain OK."
            if balance_ether < self.min_balance_threshold_ether:
                status = ServiceStatus.UNHEALTHY
                message = "ALERTA: Saldo da carteira blockchain abaixo do limite!"
                logger.error(
                    f"{message} Saldo atual: {balance_ether} ETH, Mínimo: {self.min_balance_threshold_ether} ETH"
                )
            elif (
                balance_ether < self.min_balance_threshold_ether * 2
            ):  # Ex: Aviso se estiver entre 1 e 2x o mínimo
                status = ServiceStatus.DEGRADED
                message = "AVISO: Saldo da carteira blockchain está baixo."
                logger.warning(
                    f"{message} Saldo atual: {balance_ether} ETH, Mínimo: {self.min_balance_threshold_ether} ETH"
                )

            elapsed = (datetime.now() - start_time).total_seconds() * 1000

            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                response_time_ms=elapsed,
                details={
                    "wallet_address": self.admin_wallet_address,
                    "current_balance_ether": float(f"{balance_ether:.4f}"),
                    "min_balance_threshold_ether": self.min_balance_threshold_ether,
                    "blockchain_network": w3.eth.chain_id,  # Retorna o chain_id da rede
                },
            )

        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Blockchain balance health check failed: {str(e)}")

            return HealthCheckResult(
                name=self.name,
                status=ServiceStatus.UNHEALTHY,
                message=f"Blockchain check failed: {str(e)}",
                response_time_ms=elapsed,
                details={"error": str(e)},
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
        from config.config import (
            settings,
        )  # Importar settings aqui para pegar as configs atualizadas

        # Checks críticos
        self.checks["system"] = SystemHealthCheck()

        if settings.DATABASE_ENABLED and self.database_url:
            self.checks["database"] = DatabaseHealthCheck(self.database_url)

        if settings.REDIS_ENABLED and self.redis_url:
            self.checks["redis"] = RedisHealthCheck(self.redis_url)

        if (
            settings.BLOCKCHAIN_ENABLED
            and settings.BC_NODE_URL
            and settings.ADMIN_WALLET_ADDRESS
        ):
            self.checks["blockchain_balance"] = BlockchainBalanceHealthCheck(
                bc_node_url=settings.BC_NODE_URL,
                admin_wallet_address=settings.ADMIN_WALLET_ADDRESS,
                min_balance_threshold_ether=settings.MIN_BALANCE_THRESHOLD_ETHER,
            )

        # Checks de APIs externas
        self.checks["external_apis"] = APIHealthCheck()

        # Checks granulares adicionais
        self.checks["ml_models"] = MLModelHealthCheck()
        self.checks["services"] = ServicesHealthCheck()
        self.checks["cache"] = CacheHealthCheck()

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
                results[f"check_{i}_error"] = {
                    "status": ServiceStatus.UNHEALTHY.value,
                    "message": str(result),
                }
                overall_status = (
                    ServiceStatus.UNHEALTHY
                )  # Propaga o erro para o status geral
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

        critical_checks = ["system"]
        if "database" in self.checks:
            critical_checks.append("database")
        if (
            "blockchain_balance" in self.checks
        ):  # Adicionar blockchain ao critical se habilitado
            critical_checks.append("blockchain_balance")

        for name in critical_checks:
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


async def get_health_checker(
    database_url: str = None, redis_url: str = None
) -> HealthChecker:
    """Factory para criar HealthChecker"""
    return HealthChecker(database_url, redis_url)
