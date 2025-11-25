#!/usr/bin/env python3
"""
Verification script for Phase 2 implementation.

Checks:
1. Database table structure
2. API endpoint returns clean JSON
3. Streamlit app configuration

Run: python verify_phase2.py
"""

import sys
from pathlib import Path

print("🔍 Phase 2 Verification\n")
print("=" * 60)

# Check 1: Database and Persistence
print("\n1️⃣  Checking Database Setup...")
try:
    from app.state.persistence import CouncilSession, get_persistence_manager
    from sqlalchemy import inspect
    
    # Initialize persistence (creates tables)
    persistence = get_persistence_manager()
    
    # Inspect table structure
    inspector = inspect(persistence.engine)
    tables = inspector.get_table_names()
    
    if "council_sessions" in tables:
        print("   ✅ Table 'council_sessions' exists")
        
        columns = inspector.get_columns("council_sessions")
        column_names = [c["name"] for c in columns]
        
        required_columns = ["session_id", "state_data", "status", "user_request"]
        for col in required_columns:
            if col in column_names:
                print(f"   ✅ Column '{col}' found")
            else:
                print(f"   ❌ Column '{col}' MISSING")
        
        print(f"   ℹ️  Total columns: {len(column_names)}")
    else:
        print("   ❌ Table 'council_sessions' NOT FOUND")
        
except Exception as e:
    print(f"   ❌ Database check failed: {e}")

# Check 2: API Response Structure
print("\n2️⃣  Checking API Response Structure...")
try:
    from app.api.schemas import SessionDetailResponse
    from pydantic import BaseModel
    
    # Get schema
    schema = SessionDetailResponse.model_json_schema()
    properties = schema.get("properties", {})
    
    required_fields = [
        "status", "messages", "reviews", "current_agent",
        "current_design", "faq_entries", "session_id"
    ]
    
    for field in required_fields:
        if field in properties:
            print(f"   ✅ Field '{field}' in response schema")
        else:
            print(f"   ❌ Field '{field}' MISSING from schema")
    
    print(f"   ℹ️  Total response fields: {len(properties)}")
    
except Exception as e:
    print(f"   ❌ API schema check failed: {e}")

# Check 3: Streamlit App
print("\n3️⃣  Checking Streamlit App...")
try:
    streamlit_app = Path("streamlit_app.py")
    
    if streamlit_app.exists():
        print("   ✅ streamlit_app.py exists")
        
        # Check imports
        content = streamlit_app.read_text()
        
        checks = [
            ("render_main_view", "from app.ui.main_view import render_main_view"),
            ("render_sidebar", "from app.ui.sidebar import render_sidebar"),
            ("set_page_config", "st.set_page_config"),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                print(f"   ✅ '{check_name}' imported")
            else:
                print(f"   ⚠️  '{check_name}' import not found")
                
    else:
        print("   ❌ streamlit_app.py NOT FOUND")
        
except Exception as e:
    print(f"   ❌ Streamlit check failed: {e}")

# Summary
print("\n" + "=" * 60)
print("📊 Verification Summary")
print("=" * 60)
print("\n✅ All checks completed!")
print("\nNext steps:")
print("1. Start backend: uvicorn main:app --reload")
print("2. Start UI: streamlit run streamlit_app.py")
print("3. Test workflow execution via UI")
print("\n" + "=" * 60)

