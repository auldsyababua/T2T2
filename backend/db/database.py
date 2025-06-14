import os
import time

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from backend.utils.logging import log_db_query, log_error_with_context, setup_logger

load_dotenv()


logger = setup_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Configure engine based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't support pool_size, max_overflow, or PostgreSQL-specific connect_args
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
    )
else:
    # PostgreSQL configuration
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,  # Test connections before using
        pool_size=5,
        max_overflow=10,
        connect_args={
            "statement_cache_size": 0,  # Disable prepared statements for Supabase pooler
            "prepared_statement_cache_size": 0,
        },
    )
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session created")
            yield session
        finally:
            await session.close()
            logger.debug("Database session closed")


async def init_db():
    logger.info("Initializing database...")
    start_time = time.time()

    try:
        async with engine.begin() as conn:
            # Only create PostgreSQL-specific extensions and policies for PostgreSQL
            if not DATABASE_URL.startswith("sqlite"):
                # Create pgvector extension
                logger.info("Creating pgvector extension...")
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                log_db_query(
                    logger,
                    "CREATE EXTENSION IF NOT EXISTS vector",
                    (time.time() - start_time) * 1000,
                )

            # Create tables
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)

            # Only enable RLS for PostgreSQL
            if not DATABASE_URL.startswith("sqlite"):
                logger.info("Enabling row-level security...")

                # Read and execute RLS SQL file
                rls_sql_path = os.path.join(
                    os.path.dirname(__file__), "user_messages_rls.sql"
                )
                if os.path.exists(rls_sql_path):
                    with open(rls_sql_path, "r") as f:
                        rls_sql = f.read()

                    # Execute each statement separately
                    statements = [
                        stmt.strip() for stmt in rls_sql.split(";") if stmt.strip()
                    ]
                    for statement in statements:
                        if statement:
                            try:
                                await conn.execute(text(statement))
                                logger.debug(
                                    f"Executed RLS statement: {statement[:50]}..."
                                )
                            except Exception as e:
                                # Log but don't fail if policy already exists
                                if "already exists" in str(e):
                                    logger.debug(f"RLS policy already exists: {e}")
                                else:
                                    logger.warning(
                                        f"Error executing RLS statement: {e}"
                                    )
                else:
                    # Fallback to basic RLS if file doesn't exist
                    await conn.execute(
                        text("ALTER TABLE user_messages ENABLE ROW LEVEL SECURITY;")
                    )

                    # Check if policy exists before creating
                    result = await conn.execute(
                        text(
                            """
                        SELECT 1 FROM pg_policies 
                        WHERE tablename = 'user_messages' AND policyname = 'per_user'
                    """
                        )
                    )
                    if result.scalar() is None:
                        await conn.execute(
                            text(
                                """
                            CREATE POLICY per_user ON user_messages
                            USING (user_id = current_setting('app.user_id')::bigint);
                        """
                            )
                        )

        total_time = (time.time() - start_time) * 1000
        logger.info(f"Database initialized successfully in {total_time:.2f}ms")

    except Exception as e:
        log_error_with_context(logger, e, "Database initialization failed")
        raise
