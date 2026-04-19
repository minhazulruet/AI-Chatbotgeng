"""
Database initialization service
Checks if required tables exist and provides setup instructions if needed
"""
import os
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Get Supabase credentials
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Initialize Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")


def check_table_exists(table_name: str = "users") -> bool:
    """
    Check if a table exists in the database
    """
    if not supabase:
        logger.warning("⚠️ Supabase client not initialized")
        return False
    
    try:
        # Try to query the table - if it doesn't exist, this will fail
        response = supabase.table(table_name).select("*").limit(1).execute()
        logger.info(f"✅ Table '{table_name}' exists")
        return True
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg or "relation" in error_msg or "PGRST" in error_msg:
            logger.warning(f"⚠️ Table '{table_name}' does not exist: {error_msg}")
            return False
        else:
            # Other errors
            logger.warning(f"⚠️ Could not check table: {error_msg}")
            return False


async def init_all_tables():
    """
    Initialize database tables if they don't exist
    This runs automatically when the application starts
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("❌ Supabase credentials not found!")
        logger.error("   Make sure SUPABASE_URL and SUPABASE_KEY are set in .env file")
        print_manual_setup_sql()
        return
    
    try:
        logger.info("🔄 Checking database tables...")
        
        # Check if users table exists
        if check_table_exists("users"):
            logger.info("✅ All required tables exist. Database ready!")
            return
        
        # Table doesn't exist
        logger.warning("⚠️  Table 'users' not found in database")
        logger.warning("   Automatic table creation is not supported via REST API")
        logger.warning("   You must create the table manually in Supabase")
        print_manual_setup_sql()
        
    except Exception as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
        print_manual_setup_sql()


def print_manual_setup_sql():
    """Print instructions for manual table creation"""
    sql = """
================================================================================
                    MANUAL DATABASE SETUP REQUIRED
================================================================================

The 'users' table was not found in your Supabase database.

FOLLOW THESE STEPS TO CREATE IT:

1. Go to: https://app.supabase.com
2. Log in and select your project
3. Click 'SQL Editor' in the left sidebar
4. Click 'New Query'
5. Copy and paste the SQL below:
6. Click 'Run' (or press Ctrl+Enter)

================================================================================
SQL TO RUN:
================================================================================

CREATE TABLE IF NOT EXISTS public.users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    department TEXT,
    roll_id TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public access" ON public.users;
CREATE POLICY "Allow public access" ON public.users
    FOR ALL USING (true) WITH CHECK (true);

================================================================================

After running the SQL above, restart your application and signup will work! ✅

===============================================================================
    """
    print(sql)
    logger.info(sql)


