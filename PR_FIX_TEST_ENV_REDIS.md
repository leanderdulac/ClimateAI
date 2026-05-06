# PR: Fix test environment and production Redis config

## Summary
- Updated `server/tests/conftest.py` to:
  * set `DATABASE_URL` early with `sqlite+aiosqlite` default
  * make autouse `setup_test_environment` async
  * initialize/drop tables in the fixture
  * switch tests to a file-based SQLite DB to avoid in-memory isolation issues
- Adjusted `server/config/config.py` default for `REDIS_URL` to `redis://redis:6379`
  (matches docker-compose/production) and added explanatory comment.

## Motivation
Several integration test failures and production runtime errors were due to:
1. SQLAlchemy asyncio complaining about non-async driver (pysqlite) during tests
   because default `DATABASE_URL` wasn't using `aiosqlite` until after app
   import. Tests also failed because the in-memory database schema was not
   shared between engine instances.
2. DigitalOcean deployment logs showed Redis connection refused on
   `localhost:6379`; the compose network service is named `redis` so
   `redis://redis:6379` should be default.

These changes ensure tests run reliably in CI and local dev, and prevent
Redis misconfiguration in containerized/prod environments.

## Testing
- Ran `pytest server/tests/integration/test_auth_api.py` (12 passed)
- Ran `pytest server/tests/unit/test_config.py::TestRedisConfiguration` (2 passed)
- Full suite will be rerun in CI once branch is pushed.

## Deployment notes
- After merging, ensure environment variables in production / DO App Platform
  include:
  ```bash
  REDIS_URL=redis://redis:6379  # or explicit host
  DATABASE_URL=postgresql+asyncpg://...   # already configured
  ```
- No migration or manual steps required: the test fixture handles schema
  creation for CI.

## Additional
A brief deploy checklist is attached below (next section).

---

## Deploy checklist for DigitalOcean
1. **Validate environment variables**
   - `REDIS_URL` pointing to the Redis service (on compose use `redis://redis:6379`).
   - `DATABASE_URL` with correct credentials/ssl (pooler url w/out `?sslmode=require`).
   - Optional: `VAULT_TOKEN`, `GEMINI_API_KEY`, KMS envs if you rely on them.
2. **Restart services**
   ```bash
   # on droplet
   cd /opt/climatewise
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d --build
   docker-compose -f docker-compose.prod.yml logs -f backend
   ```
   or use `doctl apps update --spec` for App Platform.
3. **Monitor logs** for any errors similar to those earlier (Redis, Vault,
   Gemini warnings). Fix by providing missing envs or installing packages.
4. **Run health endpoints**
   ```bash
   curl -f https://$DOMAIN/health
   curl -f https://$DOMAIN/api/v1/health
   ```
5. **Optional post-deploy:** verify Redis connectivity and run `redis-cli` if
   using dedicated Redis droplet.

_Make sure to merge branch and push before rerunning any pipelines._
