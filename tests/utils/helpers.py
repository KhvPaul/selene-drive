def fix_sqlalchemy_url(url: str, *, sync: bool = True) -> str:
    url = url.replace("+psycopg2", "+psycopg").replace("+asyncpg", "+psycopg")
    if not sync:
        url = url.replace("+psycopg", "+asyncpg")
    return url
