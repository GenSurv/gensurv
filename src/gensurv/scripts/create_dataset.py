import pandas as pd
import json

tsv_file_path = "data/filemaker/paper2.tsv"
df = pd.read_csv(tsv_file_path, sep="\t")

input_data_path = "gensurv/scripts/headings_input_data.json"
evaluation_data_path = "gensurv/scripts/headings_evaluation_data.json"

headings_input_data = []

for _, row in df.iterrows():
    
    paper_id = str(row['paper_id']) if pd.notna(row['paper_id']) else '9999'
    author_name = row['author'] if pd.notna(row['author']) else ""
    
    paper_entry = {
        "id": paper_id,
        "title": row['title'] if pd.notna(row['title']) else "",
        "abstract": row['abstract'] if pd.notna(row['abstract']) else "",
        "venue": "",
        "year": "",
        "authors": [{"id": "", "name": author_name}]
    }
    headings_input_data.append(paper_entry)

eval_data = {}
for _, row in df.iterrows():
    if pd.notna(row['headlines_section_title']) and pd.notna(row['title']):
        section_title = row['headlines_section_title']
        if section_title not in eval_data:
            eval_data[section_title] = []
        eval_data[section_title].append(row['title'])

headings_evaluation_data = {"headings": []}
for heading, papers in eval_data.items():
    headings_evaluation_data["headings"].append({
        "heading": heading,
        "papers": papers
    })

with open(input_data_path, 'w', encoding='utf-8') as f:
    json.dump(headings_input_data, f, ensure_ascii=False, indent=4)

with open(evaluation_data_path, 'w', encoding='utf-8') as f:
    json.dump(headings_evaluation_data, f, ensure_ascii=False, indent=4)

print(f"Input data saved to {input_data_path}")
print(f"Evaluation data saved to {evaluation_data_path}")