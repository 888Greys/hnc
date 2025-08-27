#!/usr/bin/env python3
"""
Test script to verify PostgreSQL and Redis connections for HNC Legal Application
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_postgresql():
    """Test PostgreSQL connection"""
    print("🔍 Testing PostgreSQL connection...")
    try:
        import psycopg
        from psycopg import sql
        
        # Connection parameters from environment
        db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            print("❌ DATABASE_URL not found in environment variables")
            return False
            
        # Test connection
        async with await psycopg.AsyncConnection.connect(db_url) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT version();")
                version = await cur.fetchone()
                print(f"✅ PostgreSQL connected successfully!")
                print(f"   Version: {version[0]}")
                
                # Test if our tables exist
                await cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                tables = await cur.fetchall()
                
                print(f"   Found {len(tables)} tables:")
                for table in tables:
                    print(f"     - {table[0]}")
                    
                # Test sample query
                await cur.execute("SELECT count(*) FROM users;")
                user_count = await cur.fetchone()
                print(f"   Users in database: {user_count[0]}")
                
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

async def test_redis():
    """Test Redis connection"""
    print("\n🔍 Testing Redis connection...")
    try:
        import redis.asyncio as redis
        
        # Connection parameters from environment
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # Test connection
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        await redis_client.ping()
        print("✅ Redis connected successfully!")
        
        # Test set/get operations
        test_key = "hnc_test_key"
        test_value = "HNC Legal System Test"
        
        await redis_client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        retrieved_value = await redis_client.get(test_key)
        
        if retrieved_value == test_value:
            print("✅ Redis read/write operations working!")
        else:
            print("❌ Redis read/write operations failed!")
            return False
            
        # Clean up test key
        await redis_client.delete(test_key)
        
        # Get Redis info
        info = await redis_client.info()
        print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 'Unknown')}")
        
        await redis_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def test_fastapi_integration():
    """Test FastAPI integration with databases"""
    print("\n🔍 Testing FastAPI API endpoints...")
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("✅ FastAPI health endpoint accessible")
            else:
                print(f"❌ FastAPI health endpoint failed: {response.status_code}")
                return False
                
            # Test docs endpoint
            response = await client.get(f"{base_url}/docs")
            if response.status_code == 200:
                print("✅ FastAPI documentation accessible")
            else:
                print(f"❌ FastAPI docs failed: {response.status_code}")
                
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 HNC Legal Application Database Connection Test\n")
    
    # Test all connections
    pg_result = await test_postgresql()
    redis_result = await test_redis()
    api_result = await test_fastapi_integration()
    
    print(f"\n📊 Test Results Summary:")
    print(f"   PostgreSQL: {'✅ PASS' if pg_result else '❌ FAIL'}")
    print(f"   Redis:      {'✅ PASS' if redis_result else '❌ FAIL'}")
    print(f"   FastAPI:    {'✅ PASS' if api_result else '❌ FAIL'}")
    
    if pg_result and redis_result and api_result:
        print(f"\n🎉 All database connections are working correctly!")
        print(f"   Your HNC Legal Application is ready for development!")
        return 0
    else:
        print(f"\n⚠️  Some connections failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)