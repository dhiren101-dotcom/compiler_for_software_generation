import streamlit as st
import json
# Import the functions directly from your compiler script
from compiler import compile_user_intent, run_validation_checks, repair_blueprint

# Set page layout
st.set_page_config(page_title="AI System Compiler", page_icon="🚀", layout="wide")

st.title("🎛️ Multi-Stage AI System Compiler")
st.caption("Translate open-ended product requirements into validated system architectures with self-healing validation loops.")

# User Input
user_prompt = st.text_area(
    "Enter your application requirements:",
    value="Build a CRM with login, contacts dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
    height=100
)

if st.button("Compile Architecture", type="primary"):
    if not user_prompt.strip():
        st.error("Please enter a valid prompt.")
    else:
        # Create columns to display progress visually
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Pipeline Execution Logs")
            log_placeholder = st.empty()
            
            log_placeholder.info("📥 Step 1: Extracting intent and generating base schemas...")
            try:
                # 1. Run First Pass
                raw_blueprint = compile_user_intent(user_prompt)
                log_placeholder.success("✅ Base generation complete.")
                
                # Show raw generation in an expander
                with st.expander("View Raw (First-Pass) Blueprint"):
                    st.json(json.loads(raw_blueprint))
                
                # 2. Run Validation Checks
                st.info("🔍 Step 2: Running logical cross-layer validation tests...")
                is_valid, status_or_error = run_validation_checks(raw_blueprint)
                
                final_blueprint = raw_blueprint
                
                if is_valid:
                    st.success("🏆 Architecture validation passed on the first attempt!")
                else:
                    st.warning(f"⚠️ Validation Failed: {status_or_error}")
                    st.info("🛠️ Step 3: Activating Self-Healing Repair Engine...")
                    
                    # 3. Trigger Self-Healing Loop
                    final_blueprint = repair_blueprint(raw_blueprint, status_or_error)
                    st.success("🎉 Repair complete! Output structures successfully aligned.")
                
            except Exception as e:
                st.error(f"Pipeline crashed: {e}")
                final_blueprint = None

        with col2:
            st.subheader("Final Validated System Blueprint")
            if final_blueprint:
                try:
                    st.json(json.loads(final_blueprint))
                except Exception:
                    st.code(final_blueprint, language="json")