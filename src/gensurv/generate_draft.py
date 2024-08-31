import os
import subprocess
import shutil
from typing import Dict
from pydantic import BaseModel
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from typing import List
from .models import Paper, Author
from .utils import format_bibtex

class Config(BaseModel):
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    latex_dir: str = os.path.join(current_dir, "latex")
    template_file: str = os.path.join(latex_dir, "template.tex")
    output_file: str = os.path.join(latex_dir, "output.tex")
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
    
def initialize_output_file():
    shutil.copy(config.template_file, config.output_file)    

def add_section_to_latex(coder: Coder, section_title: str, section_content: str) -> None:
    latex_edit_template = f"""
    Add the following section to the LaTeX file:
    \section{{{section_title}}}
    {section_content}

   - Note that you should properly escape LaTeX special characters, e.g. backslash, bracket, etc.
   - Add this section just before the \end{{document}} command.
    """
    coder.run(latex_edit_template)

def add_bibtex_to_latex(coder: Coder, papers: List[Paper]) -> None:
    latex_edit_template = "Add the following bibtex entries to the LaTeX file, just before the \\end{document} command:"
    for paper in papers:
        bibtex = paper.citation_styles["bibtex"]
        bibtex_string = "\n".join(bibtex)
        latex_edit_template += f"\n{bibtex_string}"
    
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

def compile_latex(cwd: str, tex_file: str, pdf_file: str, timeout: int = 30) -> None:
    print("GENERATING LATEX")

    commands = [
        ["pdflatex", "-interaction=nonstopmode", tex_file],
        ["bibtex", tex_file.replace(".tex", "")],
        ["pdflatex", "-interaction=nonstopmode", tex_file],
        ["pdflatex", "-interaction=nonstopmode", tex_file]
    ]

    for command in commands:
        run_latex_command(command, cwd, timeout)

    print("FINISHED GENERATING LATEX")

    try:
        output_pdf = os.path.join(cwd, tex_file.replace(".tex", ".pdf"))
        shutil.move(output_pdf, pdf_file)
        print(f"PDF successfully moved to {pdf_file}")
    except FileNotFoundError:
        print("Failed to rename PDF. File not found.")
    except Exception as e:
        print(f"Error moving PDF: {e}")

def generate_draft(overview: Dict[str, str], papers: List[Paper], _compile_latex: bool = False) -> None:
    initialize_output_file()
    coder = setup_coder()

    add_bibtex_to_latex(coder, papers)
    for section_title, paragraph in overview.items():
        add_section_to_latex(coder, section_title, paragraph)

    if _compile_latex:
        compile_latex(config.latex_dir, config.pdf_output)

if __name__ == "__main__":
    overview = {
        "Feedback": "Feedback plays a crucial role in aligning AI systems with human preferences. The use of reinforcement learning from human feedback (RLHF) has shown effectiveness in aligning large language models (LLMs) with human preferences, albeit with the challenge of acquiring high-quality human preference labels. In contrast, reinforcement learning from AI feedback (RLAIF) presents a promising alternative proposed by Bai et al. RLAIF leverages an off-the-shelf LLM to generate preferences, eliminating the need for human annotators. RLAIF demonstrates comparable or superior performance to RLHF in tasks such as summarization, helpful dialogue generation, and harmless dialogue generation, as assessed by human evaluators. Additionally, RLAIF exhibits the capability to surpass a supervised fine-tuned baseline even when the LLM preference labeler is of the same size as the policy. Notably, prompting the LLM directly for reward scores outperforms the traditional RLAIF setup, where LLM preference labels are transformed into a reward model. These findings suggest that RLAIF holds promise in achieving human-level performance and addresses scalability limitations encountered in RLHF \cite{lee2023rlaif,ouyang2022training}.",
        "Mechanistic Interpretability": "Mechanistic interpretability in AI systems is crucial for understanding their internal information processing mechanisms. Recent research efforts have aimed to reverse-engineer complex behaviors of transformer models to gain insights into how neural networks operate. By systematically following the interpretability process, researchers select relevant metrics and datasets to elicit specific model behaviors, then utilize activation patching to identify the neural network units involved. The variation in datasets, metrics, and units under investigation allows for a comprehensive understanding of each component's functionality. Automation tools like the ACDC algorithm have been proposed to identify the circuits implementing desired behaviors in computational graphs, showcasing promising results in rediscovering component types within models like GPT-2 Small. However, studies like those by \cite{conmy2023towards} question whether the substantial scaling of neural networks in size and datasets leads to improved mechanistic interpretability. Surprisingly, findings suggest that neither model size nor dataset scale positively impacts interpretability, with the interpretability of modern vision models potentially regressing compared to older architectures. This highlights the critical need for developing interpretable AI models explicitly and refining interpretability methods to enhance our comprehension of neural networks at a fundamental level (\cite{zimmermann2023scale})."
    }
    papers = [
            Paper(
                id="1",
                title="RLAIF: Scaling Reinforcement Learning from Human Feedback with AI Feedback",
                abstract="Reinforcement learning from human feedback (RLHF) has proven effective in aligning large language models (LLMs) with human preferences. However, gathering high-quality human preference labels can be a time-consuming and expensive endeavor. RL from AI Feedback (RLAIF), introduced by Bai et al., offers a promising alternative that leverages a powerful off-the-shelf LLM to generate preferences in lieu of human annotators. Across the tasks of summarization, helpful dialogue generation, and harmless dialogue generation, RLAIF achieves comparable or superior performance to RLHF, as rated by human evaluators. Furthermore, RLAIF demonstrates the ability to outperform a supervised fine-tuned baseline even when the LLM preference labeler is the same size as the policy. In another experiment, directly prompting the LLM for reward scores achieves superior performance to the canonical RLAIF setup, where LLM preference labels are first distilled into a reward model. Finally, we conduct extensive studies on techniques for generating aligned AI preferences. Our results suggest that RLAIF can achieve human-level performance, offering a potential solution to the scalability limitations of RLHF.",
                venue="arXiv",
                year=2023,
                authors=[Author(id="1", name="Harrison Lee"), Author(id="2", name="Samrat Phatale"), Author(id="3", name="Hassan Mansoor"), Author(id="4", name="Thomas Mesnard"), Author(id="5", name="Johan Ferret"), Author(id="6", name="Kellie Lu"), Author(id="7", name="Colton Bishop"), Author(id="8", name="Ethan Hall"), Author(id="9", name="Victor Carbune"), Author(id="10", name="Abhinav Rastogi"), Author(id="11", name="Sushant Prakash")],
                citation_styles={"bibtex": format_bibtex(
                                 "@article{lee2023rlaif,\n  title={Rlaif: Scaling reinforcement learning from human feedback with ai feedback},\n  author={Lee, Harrison and Phatale, Samrat and Mansoor, Hassan and Lu, Kellie and Mesnard, Thomas and Bishop, Colton and Carbune, Victor and Rastogi, Abhinav},\n  journal={arXiv preprint arXiv:2309.00267},\n  year={2023}\n}"
                                 )
                                 }
            ), 
            Paper(
                id="2",
                title="Training language models to follow instructions with human feedback",
                abstract="Making language models bigger does not inherently make them better at following a user's intent. For example, large language models can generate outputs that are untruthful, toxic, or simply not helpful to the user. In other words, these models are not aligned with their users. In this paper, we show an avenue for aligning language models with user intent on a wide range of tasks by fine-tuning with human feedback. Starting with a set of labeler-written prompts and prompts submitted through the OpenAI API, we collect a dataset of labeler demonstrations of the desired model behavior, which we use to fine-tune GPT-3 using supervised learning. We then collect a dataset of rankings of model outputs, which we use to further fine-tune this supervised model using reinforcement learning from human feedback. We call the resulting models InstructGPT. In human evaluations on our prompt distribution, outputs from the 1.3B parameter InstructGPT model are preferred to outputs from the 175B GPT-3, despite having 100x fewer parameters. Moreover, InstructGPT models show improvements in truthfulness and reductions in toxic output generation while having minimal performance regressions on public NLP datasets. Even though InstructGPT still makes simple mistakes, our results show that fine-tuning with human feedback is a promising direction for aligning language models with human intent.",
                venue="arXiv",
                year=2022,
                authors=[Author(id="1", name="Long Ouyang"), Author(id="2", name="Jeff Wu"), Author(id="3", name="Xu Jiang"), Author(id="4", name="Diogo Almeida"), Author(id="5", name="Carroll L. Wainwright"), Author(id="6", name="Pamela Mishkin"), Author(id="7", name="Chong Zhang"), Author(id="8", name="Sandhini Agarwal"), Author(id="9", name="Katarina Slama"), Author(id="10", name="Alex Ray"), Author(id="11", name="John Schulman"), Author(id="12", name="Jacob Hilton"), Author(id="13", name="Fraser Kelton"), Author(id="14", name="Luke Miller"), Author(id="15", name="Maddie Simens"), Author(id="16", name="Amanda Askell"), Author(id="17", name="Peter Welinder"), Author(id="18", name="Paul Christiano"), Author(id="19", name="Jan Leike"), Author(id="20", name="Ryan Lowe")],
                citation_styles={"bibtex": format_bibtex(
                                 "@article{ouyang2022training,\n  title={Training language models to follow instructions with human feedback},\n  author={Ouyang, Long and Wu, Jeff and Jiang, Xu and Almeida, Diogo and Wainwright, Carroll L. and Mishkin, Pamela and Zhang, Chong and Agarwal, Sandhini and Slama, Katarina and Ray, Alex and Schulman, John and Hilton, Jacob and Kelton, Fraser and Miller, Luke and Simens, Maddie and Askell, Amanda and Welinder, Peter and Christiano, Paul and Leike, Jan and Lowe, Ryan},\n  journal={arXiv preprint arXiv:2203.02155},\n  year={2022}\n}"
                                 )
                                 }
            ),
            Paper(
                id="3",
                title="Towards Automated Circuit Discovery for Mechanistic Interpretability",
                abstract="Through considerable effort and intuition, several recent works have reverse-engineered nontrivial behaviors of transformer models. This paper systematizes the mechanistic interpretability process they followed. First, researchers choose a metric and dataset that elicit the desired model behavior. Then, they apply activation patching to find which abstract neural network units are involved in the behavior. By varying the dataset, metric, and units under investigation, researchers can understand the functionality of each component. We automate one of the process' steps: to identify the circuit that implements the specified behavior in the model's computational graph. We propose several algorithms and reproduce previous interpretability results to validate them. For example, the ACDC algorithm rediscovered 5/5 of the component types in a circuit in GPT-2 Small that computes the Greater-Than operation. ACDC selected 68 of the 32,000 edges in GPT-2 Small, all of which were manually found by previous work. Our code is available at this https URL.",
                venue="arXiv",
                year=2023,
                authors=[Author(id="1", name="Arthur Conmy"), Author(id="2", name="Augustine N. Mavor-Parker"), Author(id="3", name="Aengus Lynch"), Author(id="4", name="Stefan Heimersheim"), Author(id="5", name="Adrià Garriga-Alonso")],
                citation_styles={"bibtex": format_bibtex(
                                 "@article{conmy2023towards,\n  title={Towards automated circuit discovery for mechanistic interpretability},\n  author={Conmy, Arthur and Mavor-Parker, Augustine N. and Lynch, Aengus and Heimersheim, Stefan and Garriga-Alonso, Adri{\`a}}],\n  journal={arXiv preprint arXiv:2305.14617},\n  year={2023}\n}"
                                 )
                                 }
            ),
            Paper(
                id="4",
                title="Scale Alone Does not Improve Mechanistic Interpretability in Vision Models",
                abstract="In light of the recent widespread adoption of AI systems, understanding the internal information processing of neural networks has become increasingly critical. Most recently, machine vision has seen remarkable progress by scaling neural networks to unprecedented levels in dataset and model size. We here ask whether this extraordinary increase in scale also positively impacts the field of mechanistic interpretability. In other words, has our understanding of the inner workings of scaled neural networks improved as well? We use a psychophysical paradigm to quantify one form of mechanistic interpretability for a diverse suite of nine models and find no scaling effect for interpretability - neither for model nor dataset size. Specifically, none of the investigated state-of-the-art models are easier to interpret than the GoogLeNet model from almost a decade ago. Latest-generation vision models appear even less interpretable than older architectures, hinting at a regression rather than improvement, with modern models sacrificing interpretability for accuracy. These results highlight the need for models explicitly designed to be mechanistically interpretable and the need for more helpful interpretability methods to increase our understanding of networks at an atomic level. We release a dataset containing more than 130'000 human responses from our psychophysical evaluation of 767 units across nine models. This dataset facilitates research on automated instead of human-based interpretability evaluations, which can ultimately be leveraged to directly optimize the mechanistic interpretability of models.",
                venue="arXiv",
                year=2023,
                authors=[Author(id="1", name="Roland S. Zimmermann"), Author(id="2", name="Thomas Klein"), Author(id="3", name="Wieland Brendel")],
                citation_styles={"bibtex": format_bibtex(
                                 "@article{zimmermann2023scale,\n  title={Scale alone does not improve mechanistic interpretability in vision models},\n  author={Zimmermann, Roland S. and Klein, Thomas and Brendel, Wieland},\n  journal={arXiv preprint arXiv:2305.14617},\n  year={2023}\n}"
                                 )
                                 }
            )
    ]
    generate_draft(overview, papers)