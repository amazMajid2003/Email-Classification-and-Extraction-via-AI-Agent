import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env
load_dotenv()

# Initialize Supabase client using service role key
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Ensure keys are set
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("❌ SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing from .env")

# Create global client instance for use across the project
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
