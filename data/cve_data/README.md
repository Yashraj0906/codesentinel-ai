# This folder is reserved for CWE/OWASP vulnerability data files.
#
# Currently, the CWE data is hardcoded in scripts/seed_cve_data.py
# (10 entries covering the top vulnerability types).
#
# In a production version, you would:
# 1. Download the full CWE database from https://cwe.mitre.org/data/
# 2. Place the JSON/CSV files in this folder
# 3. Update seed_cve_data.py to read from these files
#    instead of using hardcoded data
#
# This keeps the knowledge base updatable without changing code.
