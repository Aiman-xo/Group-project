from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import create_engine
from app.core.config import DATABASE_URL
from fastapi import HTTPException,status,Depends,Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.redis_config import get_redis
import redis.asyncio as redis




engine = create_engine(DATABASE_URL)

sessionLocal = sessionmaker(
    autoflush=False,
    autocommit = False,
    bind=engine,
    expire_on_commit=False
)

# Base = declarative_base()
PublicBase = declarative_base()

TenantBase = declarative_base()

def get_db():
    db=sessionLocal()

    try:
        yield db
    finally:
        db.close()

# this is a dependency/middleware that takes the incoming request url and extract the subdomain from the headers and cross check if it is any reserved word 
# like we can see in the RESERVED_SUBDOMAINS if it is in this or there is not any subdomain then fallback to public db like the Company etc..
# The next step is to take the schema_name from the cache if it is in there if not then we query in to the db and takes the company object and take the schema_name
# and set to the cache in this way we can reduce the db hit to ge the schema_name by storing in the redis [we only cache this for 24h]
RESERVED_SUBDOMAINS = {"www", "api", "admin", "app", "help", "support", "static"}
async def get_tenant_db(
    request: Request,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    # Get host header (e.g. "company-a.lvh.me:8000")
    host = request.headers.get("host", "").split(":")[0]
    parts = host.split(".")
    
    # Extract the subdomain
    subdomain = parts[0].lower() if len(parts) >= 3 else None

    # Local development fallback
    if not subdomain:
        subdomain = request.headers.get("X-Tenant-Slug")
    
    # Fallback to public if no subdomain or is a reserved system subdomain
    if not subdomain or subdomain in RESERVED_SUBDOMAINS:
        db.execute(text('SET search_path TO "public"'))
        # db.commit()
        try:
            yield db
        finally:
            db.close()
        return
    # Check cache for schema name mapping
    cache_key = f"slug_to_schema:{subdomain}"
    schema_name = await redis_client.get(cache_key)

    if schema_name:
        # Redis returns bytes - decode it
        schema_name = schema_name.decode() if isinstance(schema_name, bytes) else schema_name
    
    else:
        from app.models.company_model import Company
        company = db.query(Company).filter(Company.slug == subdomain, Company.is_verified == True).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace '{subdomain}' does not exist or is unverified."
            )
        schema_name = company.schema_name
        await redis_client.setex(cache_key, 86400, schema_name) # Cache for 24h

    print(f"SETTING SCHEMA TO: {schema_name}")
    print(f"SCHEMA TYPE: {type(schema_name)}")
        
    # Route to isolated schema
    db.execute(text(f'SET search_path TO "{schema_name}", public'))

    
    # db.commit()
    try:
        yield db
    finally:
        db.close()


# This is a db connection pooling security to avoid pooling into other companies db connection
# Because when a company access a tenant schema it creates a db session and this set the search_path to that schema_name
# so this resets the search_path when a session finishes.
from sqlalchemy import event

# Reset search_path when a connection is returned to the pool.
# This prevents tenant schema data from leaking into another company's session.
@event.listens_for(engine.pool, "checkin")
def reset_search_path(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("RESET search_path;")
    cursor.close()
