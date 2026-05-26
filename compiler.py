import os
import json
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# -------------------------------------------------------------------------
# DATA CONTRACT
# -------------------------------------------------------------------------
class AppBlueprint(BaseModel):
    project_name: str = Field(description="A clean, short name for the application")
    ui_pages: List[str] = Field(description="List of UI screens needed")
    api_endpoints: List[str] = Field(description="List of HTTP endpoints (e.g., POST /login, GET /contacts)")
    database_tables: List[str] = Field(description="List of relational DB tables needed (e.g., users, contacts)")
    auth_roles: List[str] = Field(description="User roles needed for permissions")

API_KEY = "AIzaSyDHqiz9I0aELTsHYT6dYuf2pquersCr0tY" 
client = genai.Client(api_key=API_KEY)

# -------------------------------------------------------------------------
# STAGE 1: FIRST GENERATION
# -------------------------------------------------------------------------
def compile_user_intent(user_prompt: str) -> str:
    system_instruction = "You are a principal system architect. Translate requirements into a precise blueprint."
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"User Request: {user_prompt}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=AppBlueprint,
            temperature=0.1,
        ),
    )
    return response.text

# -------------------------------------------------------------------------
# STAGE 2: THE REPAIR ENGINE (Validation Code Logic)
# -------------------------------------------------------------------------
def run_validation_checks(blueprint_json: str):
    data = json.loads(blueprint_json)
    endpoints = data.get("api_endpoints", [])
    tables = data.get("database_tables", [])
    
    # Standardize table names to a clean lookup list (including plural variations)
    normalized_tables = set()
    for t in tables:
        t_clean = t.lower().strip()
        normalized_tables.add(t_clean)
        normalized_tables.add(t_clean + "s")  # Handles matching 'teacher' to 'teachers'
        if t_clean.endswith('ies'):
            normalized_tables.add(t_clean[:-3] + 'y')
        if t_clean.endswith('s'):
            normalized_tables.add(t_clean[:-1])   # Handles matching 'courses' to 'course'

    for endpoint in endpoints:
        # Extract the endpoint path part (e.g., "GET /teacher/courses" -> "/teacher/courses")
        try:
            path = endpoint.split(" ")[1]
        except IndexError:
            continue
            
        parts = [p.lower() for p in path.split("/") if p and not p.startswith("{")]
        
        # Skip standard generic utility endpoint verbs
        if not parts or any(verb in parts for verb in ["login", "logout", "me", "register", "profile", "auth", "analytics", "dashboard"]):
            continue
            
        # Check if at least one core resource noun in the path matches a database entity
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
    """Passes the failure back to Gemini to fix just the broken parts."""
    print(f"⚠️ Repair Engine Triggered! Error found: {error_message}")
    
    repair_prompt = f"""
    The generated system blueprint failed architectural validation with the following error:
    "{error_message}"
    
    Here is the invalid blueprint:
    {broken_json}
    
    Please correct the mismatch and return a perfectly aligned system schema.
    """
    
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

# -------------------------------------------------------------------------
# EXECUTION PIPELINE
# -------------------------------------------------------------------------
if __name__ == "__main__":
    test_prompt = "Build a CRM with login, contacts dashboard, role-based access, and premium plan with payments. Admins can see analytics."
    
    print("🚀 Running Pipeline...")
    raw_blueprint = compile_user_intent(test_prompt)
    
    # Run validation
    is_valid, status_or_error = run_validation_checks(raw_blueprint)
    
    if is_valid:
        print("\n🏆 Architecture Passed Validation on First Attempt!")
        print(raw_blueprint)
    else:
        # Auto-Correction Cycle
        fixed_blueprint = repair_blueprint(raw_blueprint, status_or_error)
        print("\n🛠️ Self-Correction Complete! Fixed Blueprint:")
        print(fixed_blueprint)