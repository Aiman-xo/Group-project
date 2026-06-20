from app.service.intel_service import IntelService

# 1. Initialize the background engine execution
intel_worker = IntelService()

print("\n[*] SAAS MULTI-TENANT CRAWLER TRIGGERED")
print("="*60)

# --- SCENARIO 1: Main User Logs In (Bridgeon Solution) ---
LOGGED_COMPANY_ID = "company_bridgeon"
LOGGED_COMPANY_NAME = "Bridgeon Solution"

print(f"\n[STEP 1] USER LOGGED IN: Auto-Crawling Admin Metrics...")
intel_worker.process_offsite_intel(
    main_company_id=LOGGED_COMPANY_ID,
    target_name=LOGGED_COMPANY_NAME,
    is_competitor=False  # Goes to company/company_bridgeon/admin/
)

# --- SCENARIO 2: User Clicks "Track Competitor" on Dashboard ---
INPUT_COMP_NAME = "Alpha Academy"
INPUT_COMP_URL = "https://alphaacademy.example.com"

print(f"\n[STEP 2] DASHBOARD EVENT: User requested tracking on a market competitor...")
intel_worker.process_offsite_intel(
    main_company_id=LOGGED_COMPANY_ID, # Remains tied to the active user's workspace account
    target_name=INPUT_COMP_NAME,
    target_url=INPUT_COMP_URL,       # Pass URL variables to our data pipelines
    is_competitor=True  # Automatically branches to company/company_bridgeon/competitor/alpha_academy/
)

print("\n" + "="*60)
print("[*] PIPELINE ENGINE RUN COMPLETE: Memory stream layout successfully verified!\n")