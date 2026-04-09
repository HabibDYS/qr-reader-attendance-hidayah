import pandas as pd
import re
from collections import defaultdict

# Path to your Excel file
excel_file = "Data Siswa 10.11.12 TA. 2026.xlsx"

# Load all sheets
xl = pd.ExcelFile(excel_file)
sheet_names = xl.sheet_names

# We'll collect all student records here
all_students = []

# Helper to generate base username from name
def generate_base_username(name):
    # Replace spaces with underscores
    base = re.sub(r'\s+', '_', name.strip())
    # Remove any characters that are not letters, numbers, or underscore
    base = re.sub(r'[^a-zA-Z0-9_]', '', base)
    # Convert to lowercase
    base = base.lower()
    # If empty (e.g., very weird characters), use a fallback
    if not base:
        base = "student"
    return base

# Process each sheet
for sheet in sheet_names:
    print(f"Processing sheet: {sheet}")
    df = pd.read_excel(excel_file, sheet_name=sheet)
    
    # Look for column with student names (case-insensitive)
    name_col = None
    for col in df.columns:
        if 'nama' in str(col).lower() and 'siswa' in str(col).lower():
            name_col = col
            break
    if name_col is None:
        # Try just 'Nama Siswa' or fallback to first column that looks like names
        if 'Nama Siswa' in df.columns:
            name_col = 'Nama Siswa'
        else:
            # Use the second column as heuristic (first is usually No)
            name_col = df.columns[1] if len(df.columns) > 1 else None
    if name_col is None:
        print(f"  Skipping sheet {sheet}: no name column found")
        continue
    
    for idx, row in df.iterrows():
        name = row[name_col]
        if pd.isna(name) or str(name).strip() == '':
            continue
        
        name = str(name).strip()
        base_username = generate_base_username(name)
        all_students.append({
            'original_name': name,
            'base_username': base_username,
            'email_base': base_username
        })

# Make usernames unique by appending numbers
username_count = defaultdict(int)
unique_students = []
for student in all_students:
    base = student['base_username']
    username_count[base] += 1
    count = username_count[base]
    if count == 1:
        final_username = base
    else:
        final_username = f"{base}_{count}"
    
    # Ensure email is unique using the final username
    email = f"{final_username}@example.com"
    
    unique_students.append({
        'username': final_username,
        'email': email,
        'name': student['original_name'],
        'password': 'siswa123'   # default password, change if needed
    })

# Create a DataFrame and save to CSV
df_out = pd.DataFrame(unique_students)
df_out.to_csv('students.csv', index=False, encoding='utf-8')

print(f"✅ Successfully converted {len(unique_students)} students to students.csv")
print("Sample of first 5 records:")
print(df_out.head())
print("\nYou can now run 'python import_users.py' to import them into the database.")