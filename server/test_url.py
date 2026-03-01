from urllib.parse import urlparse, urlunparse

database_url = os.getenv(
    "TEST_SUPABASE_DB_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

parsed = urlparse(database_url)
pooler_host = os.getenv("TEST_SUPABASE_POOLER_HOST", "localhost")
project_ref = parsed.hostname.split('.')[1] if parsed.hostname else "local"
new_user = f"{parsed.username}.{project_ref}"
netloc = parsed.netloc.replace(parsed.hostname, pooler_host).replace(f"{parsed.username}:", f"{new_user}:", 1)
netloc = netloc.replace(str(parsed.port), "6543")
db_url = urlunparse(parsed._replace(netloc=netloc))
print("Final string:", db_url)
