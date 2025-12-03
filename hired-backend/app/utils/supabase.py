from supabase import create_client, Client
import os

supabase: Client = None

def get_supabase_client():
    global supabase
    if supabase is None:
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_KEY')
        if not url or not key:
            raise ValueError("Supabase URL or Key missing in .env")
        supabase = create_client(url, key)
    return supabase
