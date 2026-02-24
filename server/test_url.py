from urllib.parse import urlparse, urlunparse

database_url = "postgresql+asyncpg://postgres:brBU04YrEeJiXUne@db.tyzmywhvpmdfepxdtyes.supabase.co:5432/postgres"

parsed = urlparse(database_url)
pooler_host = "aws-0-sa-east-1.pooler.supabase.com"
project_ref = parsed.hostname.split('.')[1]
new_user = f"{parsed.username}.{project_ref}"
netloc = parsed.netloc.replace(parsed.hostname, pooler_host).replace(f"{parsed.username}:", f"{new_user}:", 1)
netloc = netloc.replace(str(parsed.port), "6543")
db_url = urlunparse(parsed._replace(netloc=netloc))
print("Final string:", db_url)
