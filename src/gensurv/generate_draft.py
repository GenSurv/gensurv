import os
from pathlib import Path
import shutil
import subprocess
from typing import List, Dict

from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from pydantic import BaseModel

from .models import Paper


class Config(BaseModel):
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    latex_dir: str = os.path.join(current_dir, "latex")
    writeup_file: str = os.path.join(latex_dir, "template.tex")
    pdf_output: str = os.path.join(latex_dir, "paper.pdf")
    model_name: str = "gpt-4o-2024-05-13"
    # model_name: str = "claude-3-5-sonnet-20240620"


latex_edit_template = """
    Add the following section to the latex template:
    \section{{{section_title}}}
    {section_content}

   - Note that you should properly escape use LaTeX special characters, e.g. backslash, blacket, etc.
   - If there are duplicate bibtex entries, you should remove them.
"""


def setup_coder(config: Config) -> Coder:
    io = InputOutput(yes=True)
    main_model = Model(config.model_name)
    return Coder.create(
        main_model=main_model,
        fnames=[config.writeup_file],
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff"
    )


def add_section_to_latex(coder: Coder, section_title: str, section_content: str) -> None:
    coder.run(
        latex_edit_template.format(
            section_title=section_title,
            section_content=section_content
        )
    )


def add_bibtex_to_latex(coder: Coder, papers: List[Paper]) -> None:
    latex_edit_template = "Add the following bibtex entries to the latex template:"
    for paper in papers:
        bibtex = paper.citation_styles["bibtex"]
        bibtex_string = "\n".join(bibtex)
        latex_edit_template += bibtex_string + "\n"
    
    coder.run(latex_edit_template)


def run_latex_command(command: List[str], cwd: str, timeout: int = 30) -> None:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        print(f"Command: {' '.join(command)}")
        print(f"Exit code: {result.returncode}")
        print(f"Standard Output:\n{result.stdout}")
        print(f"Standard Error:\n{result.stderr}")
        if result.returncode != 0:
            print(f"Warning: Command {' '.join(command)} exited with non-zero status")
    except subprocess.TimeoutExpired:
        print(f"Command {' '.join(command)} timed out after {timeout} seconds")
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")


def compile_latex(cwd: str, pdf_file: str, timeout: int = 30) -> None:
    print("GENERATING LATEX")

    commands = [
        ["pdflatex", "-interaction=nonstopmode", "template.tex"],
        ["bibtex", "-debug", "template"],
        ["pdflatex", "-interaction=nonstopmode", "template.tex"],
        ["pdflatex", "-interaction=nonstopmode", "template.tex"]
    ]

    for command in commands:
        run_latex_command(command, cwd, timeout)

    print("FINISHED GENERATING LATEX")

    try:
        shutil.move(os.path.join(cwd, "template.pdf"), pdf_file)
        print(f"PDF successfully moved to {pdf_file}")
    except FileNotFoundError:
        print("Failed to rename PDF. File not found.")
    except Exception as e:
        print(f"Error moving PDF: {e}")


def generate_draft(overview: Dict[str, str], papers: List[Paper], output_dir: Path, _compile_latex: bool = False) -> None:
    config = Config(
        latex_dir=str(output_dir),
        writeup_file=str(output_dir / "template.tex"),
        pdf_output=str(output_dir / "paper.pdf")
    )
    coder = setup_coder(config)

    add_bibtex_to_latex(coder, papers)
    for section_title, paragraph in overview.items():
        add_section_to_latex(coder, section_title, paragraph)

    if _compile_latex:
        compile_latex(config.latex_dir, config.pdf_output)
