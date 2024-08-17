import os
import subprocess
import shutil
from typing import Dict, List
from pydantic import BaseModel
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput

class Config(BaseModel):
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    latex_dir: str = os.path.join(current_dir, "latex")
    writeup_file: str = os.path.join(latex_dir, "template.tex")
    pdf_output: str = os.path.join(latex_dir, "paper.pdf")
    model_name: str = "gpt-4o-2024-05-13"

config = Config()

latex_edit_template = """
    Add the following section to the latex template:
    \section{{{section_title}}}
    {section_content}

   - Note that you should properly escape use LaTeX special characters, e.g. backslash, blacket, etc.
   - If there are duplicate bibtex entries, you should remove them.
"""

def setup_coder() -> Coder:
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

def generate_draft(overview: Dict[str, str]) -> None:
    coder = setup_coder()

    for section_title, paragraph in overview.items():
        add_section_to_latex(coder, section_title, paragraph)

    compile_latex(config.latex_dir, config.pdf_output)

if __name__ == "__main__":
    overview = {
        "Feedback": "Feedback plays a crucial role in aligning AI systems with human preferences. The use of reinforcement learning from human feedback (RLHF) has shown effectiveness in aligning large language models (LLMs) with human preferences, albeit with the challenge of acquiring high-quality human preference labels. In contrast, reinforcement learning from AI feedback (RLAIF) presents a promising alternative proposed by Bai et al. RLAIF leverages an off-the-shelf LLM to generate preferences, eliminating the need for human annotators. RLAIF demonstrates comparable or superior performance to RLHF in tasks such as summarization, helpful dialogue generation, and harmless dialogue generation, as assessed by human evaluators. Additionally, RLAIF exhibits the capability to surpass a supervised fine-tuned baseline even when the LLM preference labeler is of the same size as the policy. Notably, prompting the LLM directly for reward scores outperforms the traditional RLAIF setup, where LLM preference labels are transformed into a reward model. These findings suggest that RLAIF holds promise in achieving human-level performance and addresses scalability limitations encountered in RLHF \cite{lee2023rlaif,ouyang2022training}.",
        "Mechanistic Interpretability": "Mechanistic interpretability in AI systems is crucial for understanding their internal information processing mechanisms. Recent research efforts have aimed to reverse-engineer complex behaviors of transformer models to gain insights into how neural networks operate. By systematically following the interpretability process, researchers select relevant metrics and datasets to elicit specific model behaviors, then utilize activation patching to identify the neural network units involved. The variation in datasets, metrics, and units under investigation allows for a comprehensive understanding of each component's functionality. Automation tools like the ACDC algorithm have been proposed to identify the circuits implementing desired behaviors in computational graphs, showcasing promising results in rediscovering component types within models like GPT-2 Small. However, studies like those by \cite{conmy2023towards} question whether the substantial scaling of neural networks in size and datasets leads to improved mechanistic interpretability. Surprisingly, findings suggest that neither model size nor dataset scale positively impacts interpretability, with the interpretability of modern vision models potentially regressing compared to older architectures. This highlights the critical need for developing interpretable AI models explicitly and refining interpretability methods to enhance our comprehension of neural networks at a fundamental level (\cite{zimmermann2023scale})."
    }
    generate_draft(overview)