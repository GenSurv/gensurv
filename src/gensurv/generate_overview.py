import os
from typing import Dict, List

from openai import OpenAI

from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from models import Paper, Author

# Constants
REVIEW_PAPER_THEME = "AI alignment"
OPENAI_MODEL = "gpt-3.5-turbo"
MAIN_MODEL = "claude-3-5-sonnet-20240620"

# Type aliases
ParagraphDict = Dict[str, str]

def get_latex_file_path() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    latex_dir = os.path.join(current_dir, "latex")
    return os.path.join(latex_dir, "template.tex")

def setup_coder(latex_file_path: str) -> Coder:
    io = InputOutput(yes=True)
    main_model = Model(MAIN_MODEL)
    return Coder.create(
        main_model=main_model,
        fnames=[latex_file_path],
        io=io,
        stream=False,
        use_git=False,
        edit_format="diff"
    )

def create_prompt(section_title: str, papers: List[Paper]) -> str:
    prompt = f"""
Generate a paragraph of the following section of an academic review paper on the theme of {REVIEW_PAPER_THEME}:
section_title:
{section_title}

The paragraph is composed of the research papers that have the following papers.
You 'must' use \\cite{{...}} to reference papers from bibtex name, do not manually type out author names!
- Please escape appropriately characters for LaTeX if necessary, e.g. adding two backshalses, two backticks, etc.
- When making multiple citations, use the `\\cite{{..., ...}}` format instead of the `(\\cite{{...}}; \\cite{{...}})` format.

papers:
"""
    for paper in papers:
        bibtex = paper.citation_styles["bibtex"]
        bibtex_string = "\n".join(bibtex)
        prompt += f"abstract: {paper.abstract}\n"
        prompt += f"bibtex: {bibtex_string}\n\n"
    return prompt

def generate_paragraph(client: OpenAI, system_message: str, prompt: str) -> str:
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating paragraph: {e}")
        return ""
    
def format_bibtex(bibtex: str) -> str:
    # Remove any newline characters and extra spaces
    bibtex = ' '.join(bibtex.split())
    # Escape any backslashes and double quotes
    bibtex = bibtex.replace('\\', '\\\\').replace('"', '\\"')
    return bibtex

def generate_overview(client: OpenAI, structured_papers: Dict[str, List[Paper]]) -> ParagraphDict:
    system_message = f"""
You are a expert researcher in the field of AI. 
You are writing an academic review paper on the theme of {REVIEW_PAPER_THEME}.
You are tasked with generating a paragraph for the review paper.
"""
    paragraphs = {}

    for section_title, papers in structured_papers.items():
        prompt = create_prompt(section_title, papers)        
        paragraph = generate_paragraph(client, system_message, prompt)
        paragraphs[section_title] = paragraph
    return paragraphs

def main():
    client = OpenAI()

    structured_papers = {
        "Feedback": [
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
            )
        ],
        "Mechanistic Interpretability": [
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
    }

    paragraphs = generate_overview(client, structured_papers)
    for section_title, paragraph in paragraphs.items():
        print(f"Section: {section_title}")
        print(f"Paragraph: {paragraph}")
        print("-" * 100)

if __name__ == "__main__":
    main()