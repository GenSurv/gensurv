from pydantic import BaseModel

class Author(BaseModel):
    id: str
    name: str
class Paper(BaseModel):
    id: str
    title: str
    abstract: str | None
    venue: str
    year: int
    authors: list[Author]

import os
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
import subprocess
import shutil

latex_edit_template = """
    Add the following section to the latex template:
    \section{{{section_title}}}
    {section_content}

   - Note that you should properly escape use LaTeX special characters, e.g. backslash, blacket, etc.
   - If there are duplicate bibtex entries, you should remove them.
"""

current_dir = os.path.dirname(os.path.abspath(__file__))
latex_dir = os.path.join(current_dir, "latex")
writeup_file = os.path.join(latex_dir, "template.tex")
fnames = [writeup_file]

io = InputOutput(yes=True)
# main_model = Model("gpt-4o-2024-05-13")
main_model = Model("claude-3-5-sonnet-20240620")
coder = Coder.create(
    main_model=main_model, fnames=fnames, io=io, stream=False, use_git=False, edit_format="diff"
)

def generate_draft(overview: dict[str, str]) -> str:
    # write overview to latex template
    with open(writeup_file, "a") as f:
        for section_title, paragraph in overview.items():
            coder.run(
                latex_edit_template.format(
                    section_title=section_title,
                    section_content=paragraph
                )
            )

    compile_latex(latex_dir, os.path.join(latex_dir, "paper.pdf"))

def compile_latex(cwd, pdf_file, timeout=30):
    print("GENERATING LATEX")

    commands = [
        ["pdflatex", "-interaction=nonstopmode", "template.tex"],
        ["bibtex", "-debug", "template"],  # デバッグオプションを追加
        ["pdflatex", "-interaction=nonstopmode", "template.tex"],
        ["pdflatex", "-interaction=nonstopmode", "template.tex"]
    ]

    for command in commands:
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
            print("Exit code:", result.returncode)
            print("Standard Output:\n", result.stdout)
            print("Standard Error:\n", result.stderr)
            if result.returncode != 0:
                print(f"Warning: Command {' '.join(command)} exited with non-zero status")
        except subprocess.TimeoutExpired:
            print(f"Command {' '.join(command)} timed out after {timeout} seconds")
        except subprocess.CalledProcessError as e:
            print(f"Error running command {' '.join(command)}: {e}")

    print("FINISHED GENERATING LATEX")

    try:
        shutil.move(os.path.join(cwd, "template.pdf"), pdf_file)
        print(f"PDF successfully moved to {pdf_file}")
    except FileNotFoundError:
        print("Failed to rename PDF. File not found.")
    except Exception as e:
        print(f"Error moving PDF: {e}")

if __name__ == "__main__":
    overview = {
        "Feedback": "Feedback plays a crucial role in improving the alignment of AI systems with human preferences. Research by Lee et al. introduces RL from AI Feedback (RLAIF), which utilizes a pre-trained large language model (LLM) to generate preferences, reducing the dependency on labor-intensive human labeling. The study shows that RLAIF achieves comparable or superior performance to conventional reinforcement learning from human feedback (RLHF) across tasks like summarization and dialogue generation. Additionally, Ouyang et al. propose InstructGPT, a model fine-tuned with human feedback, demonstrating improvements in aligning language models with user intent. In human evaluations, the InstructGPT models outperform larger models like GPT-3 in terms of preference and quality of output. These findings highlight the effectiveness of leveraging human feedback to enhance the alignment of AI systems with human preferences, offering a promising avenue for addressing the scalability challenges associated with traditional approaches. (\cite{lee2023rlaif}; \cite{ouyang2022training})",
        "Mechanistic Interpretability": "In the realm of mechanistic interpretability in AI, recent studies have delved into reverse-engineering complex behaviors exhibited by transformer models with remarkable success \cite{conmy2023towards}. These works have systematized the interpretability process by selecting specific metrics and datasets to reveal desired model behaviors, employing techniques like activation patching to identify the neural network units responsible for these behaviors. By manipulating datasets, metrics, and units, researchers can gain insights into the functionality of each component. One notable advancement is the automation of identifying the computational graph circuit implementing targeted behaviors within the model, with proposed algorithms validated through reproducing previous interpretability findings. For instance, the ACDC algorithm successfully identified the components responsible for the Greater-Than operation in a GPT-2 Small circuit, reaffirming findings from previous manual efforts \cite{zimmermann2024scale}. This progress underscores the importance of developing AI models with mechanistic interpretability in mind, emphasizing the significance of interpretability methods for comprehensive understanding at a granular level."
    }
    generate_draft(overview)

