import os
import json
import time
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

# -------------------------------------------------------------------------
# DATA CONTRACT
# -------------------------------------------------------------------------
class AppBlueprint(BaseModel):
    project_name: str = Field(description="A clean, short name for the application")
    ui_pages: List[str] = Field(description="List of UI screens needed")
    api_endpoints: List[str] = Field(description="List of HTTP endpoints (e.g., POST /login, GET /contacts)")
    database_tables: List[str] = Field(description="List of relational DB tables needed (e.g., users, contacts)")
    auth_roles: List[str] = Field(description="User roles needed for permissions")

# -------------------------------------------------------------------------
# SECURE API INITIALIZATION
# -------------------------------------------------------------------------
# 1. First look for standard system environment variables
API_KEY = os.environ.get("GEMINI_API_KEY")

# 2. Fallback to Streamlit's deployment production secrets engine if running live
if not API_KEY:
    try:
        import streamlit as st
        API_KEY = st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

# 3. Crash gracefully with a clean setup hint if no key is configured anywhere
if not API_KEY:
    raise ValueError(
        "🔴 CRITICAL CONFIGURATION ERROR:\n"
        "GEMINI_API_KEY is missing! Set it locally in your terminal using:\n"
        "export GEMINI_API_KEY='your_key_here'\n"
        "Or add it to the Secrets configuration dashboard inside Streamlit Cloud."
    )

client = genai.Client(api_key=API_KEY)

# -------------------------------------------------------------------------
# STAGE 1: GENERATION WITH FALLBACKS & RETRIES
# -------------------------------------------------------------------------
def compile_user_intent(user_prompt: str) -> str:
    system_instruction = "You are a principal system architect. Translate requirements into a precise blueprint."
    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-1.5-flash']
    
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"User Request: {user_prompt}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        response_schema=AppBlueprint,
                        temperature=0.1,
                    ),
                )
                return response.text
            except (ServerError, APIError):
                print(f"⚠️ Server busy on {model_name} (Attempt {attempt+1}/3). Retrying in 2 seconds...")
                time.sleep(2)
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                raise e
                
    raise Exception("🔴 All Gemini models are currently overloaded. Please try again in a moment.")

# -------------------------------------------------------------------------
# STAGE 2: THE REPAIR ENGINE (Validation Code Logic)
# -------------------------------------------------------------------------
def run_validation_checks(blueprint_json: str):
    data = json.loads(blueprint_json)
    endpoints = data.get("api_endpoints", [])
    tables = data.get("database_tables", [])
    
    normalized_tables = set()
    for t in tables:
        t_clean = t.lower().strip()
        normalized_tables.add(t_clean)
        normalized_tables.add(t_clean + "s")  
        if t_clean.endswith('ies'):
            normalized_tables.add(t_clean[:-3] + 'y')
        if t_clean.endswith('s'):
            normalized_tables.add(t_clean[:-1])   

    for endpoint in endpoints:
        try:
            path = endpoint.split(" ")[1]
        except IndexError:
            continue
            
        parts = [p.lower() for p in path.split("/") if p and not p.startswith("{")]
        
        if not parts or any(verb in parts for verb in ["login", "logout", "me", "register", "profile", "auth", "analytics", "dashboard"]):
            continue
            
        has_matching_table = False
        for resource in parts:
            if resource in normalized_tables:
                has_matching_table = True
                break
                
        if not has_matching_table:
            error_msg = f"SCHEMA MISMATCH: API endpoint '{endpoint}' uses path resources {parts}, but none match your database tables {tables}!"
            return False, error_msg
            
    return True, "All clear!"

# -------------------------------------------------------------------------
# STAGE 3: SELF-HEALING LOOP
# -------------------------------------------------------------------------
def repair_blueprint(broken_json: str, error_message: str) -> str:
    print(f"⚠️ Repair Engine Triggered! Error found: {error_message}")
    
    repair_prompt = f"""
    The generated system blueprint failed architectural validation with the following error:
    "{error_message}"
    
    Here is the invalid blueprint:
    {broken_json}
    
    Please correct the mismatch and return a perfectly aligned system schema.
    """
    
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=repair_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AppBlueprint,
                    temperature=0.1,
                ),
            )
            return response.text
        except (ServerError, APIError):
            print(f"⚠️ Repair engine endpoint busy. Retrying attempt {attempt+1}/3...")
            time.sleep(2)
            
    raise Exception("🔴 Repair engine failed to execute due to server overload.")

# -------------------------------------------------------------------------
# EXECUTION PIPELINE
# -------------------------------------------------------------------------
if __name__ == "__main__":
    test_prompt = "Build a CRM with login, contacts dashboard, role-based access, and premium plan with payments. Admins can see analytics."
    
    print("🚀 Running Pipeline...")
    try:
        raw_blueprint = compile_user_intent(test_prompt)
        is_valid, status_or_error = run_validation_checks(raw_blueprint)
        
        if is_valid:
            print("\n🏆 Architecture Passed Validation on First Attempt!")
            print(raw_blueprint)
        else:
            fixed_blueprint = repair_blueprint(raw_blueprint, status_or_error)
            print("\n🛠️ Self-Correction Complete! Fixed Blueprint:")
            print(fixed_blueprint)
    except Exception as main_error:
        print(f"\n❌ Pipeline failed: {main_error}")