import streamlit as st
import subprocess
import os
from pathlib import Path
import json
import time
import re
import base64
from PIL import Image
import io

def make_image_transparent(image_path, opacity):
    img = Image.open(image_path).convert("RGBA")
    data = img.getdata()
    new_data = []
    for item in data:
        new_data.append(item[:-1] + (int(255 * opacity),))
    img.putdata(new_data)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

def set_transparent_background(image_path, opacity=0.5):
    img_byte_arr = make_image_transparent(image_path, opacity)
    b64_encoded = base64.b64encode(img_byte_arr.getvalue()).decode()
    style = f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{b64_encoded});
            background-size: cover;
        }}
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 2rem;
            border-radius: 10px;
        }}
        </style>
    """
    st.markdown(style, unsafe_allow_html=True)

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    output = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, line in enumerate(process.stdout):
        output.append(line.strip())
        status_text.text(f"Processing: {line.strip()}")
        
        progress = min((i + 1) / 100, 1.0)
        progress_bar.progress(progress)
        
        time.sleep(0.1)
    
    progress_bar.progress(1.0)
    status_text.text("Processing completed!")
    return output

def get_latest_output_dir(base_path, title):
    escaped_title = re.escape(title.replace(' ', '_'))
    pattern = re.compile(f"\\d{{8}}_\\d{{6}}_{escaped_title}")
    
    matching_dirs = [d for d in base_path.iterdir() if d.is_dir() and pattern.match(d.name)]
    
    if not matching_dirs:
        return None
    
    latest_dir = max(matching_dirs, key=lambda d: d.name)
    return latest_dir

def display_pdf(pdf_file):
    with open(pdf_file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def main():
    # 背景画像の設定（透明度0.5）
    set_transparent_background('/root/ladec-demo/figs/robots.png', opacity=0.5)

    # タイトル画像の表示
    st.image('/root/ladec-demo/figs/robots_cropped.png', use_column_width=True)

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

        with st.spinner('Generating survey... This may take a few minutes.'):
            output = run_command(" ".join(command))

        st.success("Survey generation completed!")

        output_dir = get_latest_output_dir(base_output_path, title)
        if not output_dir:
            st.error(f"Could not find output directory for title '{title}' in {base_output_path}")
            return

        papers_file = output_dir / "papers.json"
        if papers_file.exists():
            with open(papers_file, "r") as f:
                papers = json.load(f)
            st.subheader("Retrieved Papers")
            for paper in papers:
                st.write(f"- {paper['title']} ({paper['year']})")

        pdf_files = list(output_dir.glob("*.pdf"))
        if pdf_files:
            for pdf_file in pdf_files:
                st.subheader(f"Preview of {pdf_file.name}")
                display_pdf(pdf_file)
                
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