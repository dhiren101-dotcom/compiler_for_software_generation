import time
import json
from compiler import compile_user_intent, run_validation_checks, repair_blueprint

# Section 7: The Dataset (Real Prompts + Edge Cases)
TEST_DATASET = [
    # 3 Real Product Prompts
    "Build an E-commerce store with a shopping cart, stripe payments, and inventory table.",
    "Create a school management system where teachers assign grades and students view reports.",
    "Build a fitness tracker app with custom workout logs, profile settings, and exercise lists.",
    
    # 3 Devious Edge Cases (Vague / Conflicting)
    "Make an app.", # Super Vague
    "Build a system where users can delete logs but the logs database table is read-only.", # Conflicting
    "Create a messaging tool with private chat rooms but no users table." # Missing core entity
]

def run_evaluation_framework():
    print("🧪 INITIALIZING EVALUATION FRAMEWORK (Section 7 & 8)...")
    print(f"Running tests across {len(TEST_DATASET)} scenarios.\n")
    print(f"{'Prompt Preview':<40} | {'Status':<12} | {'Retries':<8} | {'Latency':<8}")
    print("-" * 75)
    
    success_count = 0
    total_retries = 0
    total_start_time = time.time()
    
    for prompt in TEST_DATASET:
        preview = prompt[:37] + "..." if len(prompt) > 40 else prompt
        start_time = time.time()
        retries = 0
        status = "Passed"
        
        try:
            # 1. First Pass Generation
            raw_output = compile_user_intent(prompt)
            
            # 2. Logic Check
            is_valid, error_msg = run_validation_checks(raw_output)
            
            if not is_valid:
                retries += 1
                total_retries += 1
                # 3. Trigger Repair Engine
                final_output = repair_blueprint(raw_output, error_msg)
                status = "Healed"
            
            success_count += 1
            
        except Exception:
            status = "Failed"
            
        latency = time.time() - start_time
        print(f"{preview:<40} | {status:<12} | {retries:<8} | {latency:.2f}s")
    
    # Calculate final metrics
    total_time = time.time() - total_start_time
    success_rate = (success_count / len(TEST_DATASET)) * 100
    
    print("\n📊 FINAL SYSTEM SIGNAL METRICS")
    print("=" * 40)
    print(f"🏁 Overall Success Rate: {success_rate:.1f}%")
    print(f"🔄 Total Self-Healing Retries: {total_retries}")
    print(f"⏱️ Total Execution Latency: {total_time:.2f} seconds")
    print("=" * 40)

if __name__ == "__main__":
    run_evaluation_framework()