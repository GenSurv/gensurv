import streamlit as st
import subprocess
import os
from pathlib import Path
import json
import time
import re
import base64

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    output = []
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, line in enumerate(process.stdout):
        output.append(line.strip())
        status_text.text(f"Processing: {line.strip()}")
        
        # Update progress bar (assuming 100 total steps, adjust as needed)
        progress = min((i + 1) / 100, 1.0)
        progress_bar.progress(progress)
        
        time.sleep(0.1)  # Small delay to make the progress visible
    
    progress_bar.progress(1.0)
    status_text.text("Processing completed!")
    return output

def get_latest_output_dir(base_path, title):
    # Escape special characters in the title for use in regex
    escaped_title = re.escape(title.replace(' ', '_'))
    pattern = re.compile(f"\\d{{8}}_\\d{{6}}_{escaped_title}")
    
    matching_dirs = [d for d in base_path.iterdir() if d.is_dir() and pattern.match(d.name)]
    
    if not matching_dirs:
        return None
    
    # Sort directories by name (which includes the timestamp) in descending order
    latest_dir = max(matching_dirs, key=lambda d: d.name)
    return latest_dir

def display_pdf(pdf_file):
    with open(pdf_file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def main():
    st.title("GenSurv")

    title = st.text_input("Enter the title of your paper:")
    max_papers = st.number_input("Maximum number of papers to retrieve:", min_value=1, max_value=50, value=5)
    retrieve_papers = st.checkbox("Retrieve papers from Semantic Scholar")
    generate_headings = st.checkbox("Generate headings")

    if st.button("Generate Survey"):
        if not title:
            st.error("Please enter a title for your paper.")
            return

        base_output_path = Path("data")
        base_output_path.mkdir(exist_ok=True)

        command = [
            "python", "src/main.py",
            "--title", f'"{title}"',
            "--max_papers", str(max_papers),
            "--output_path", str(base_output_path)
        ]

        if retrieve_papers:
            command.append("--retrieve_papers")
        if generate_headings:
            command.append("--generate_headings")

        # st.write("Running command:", " ".join(command))
        
        with st.spinner('Generating survey... This may take a few minutes.'):
            output = run_command(" ".join(command))

        st.success("Survey generation completed!")
        # st.write("Displaying results:")

        # Find the latest output directory
        output_dir = get_latest_output_dir(base_output_path, title)
        if not output_dir:
            st.error(f"Could not find output directory for title '{title}' in {base_output_path}")
            return

        # st.write(f"Found output directory: {output_dir}")

        # Display papers
        papers_file = output_dir / "papers.json"
        if papers_file.exists():
            with open(papers_file, "r") as f:
                papers = json.load(f)
            st.subheader("Retrieved Papers")
            for paper in papers:
                st.write(f"- {paper['title']} ({paper['year']})")

        # Display structured papers
        # structured_papers_file = output_dir / "structured_papers.json"
        # if structured_papers_file.exists():
        #     with open(structured_papers_file, "r") as f:
        #         structured_papers = json.load(f)
        #     st.subheader("Structured Papers")
        #     for heading, papers in structured_papers.items():
        #         st.write(f"### {heading}")
        #         for paper in papers:
        #             st.write(f"- {paper}")

        # Display overview
        # overview_file = output_dir / "overview.json"
        # if overview_file.exists():
        #     with open(overview_file, "r") as f:
        #         overview = json.load(f)
        #     st.subheader("Overview")
        #     st.write(overview)

        # Display and provide link to download the generated PDF file
        # st.write("Searching for PDF file in:", output_dir)
        pdf_files = list(output_dir.glob("*.pdf"))
        if pdf_files:
            # st.write(f"Found {len(pdf_files)} PDF file(s):")
            for pdf_file in pdf_files:
                # st.write(f"- {pdf_file.name}")
                
                # Display PDF
                st.subheader(f"Preview of {pdf_file.name}")
                display_pdf(pdf_file)
                
                # Provide download button
                with open(pdf_file, "rb") as file:
                    btn = st.download_button(
                        label=f"Download {pdf_file.name}",
                        data=file,
                        file_name=pdf_file.name,
                        mime="application/pdf"
                    )
        else:
            st.error(f"No PDF file found in {output_dir}. Please check if the file was generated correctly.")

if __name__ == "__main__":
    main()