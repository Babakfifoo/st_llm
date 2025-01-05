import ollama


def generate_answer(messages, user_question: str, information: str = ""):
    if information == "":
        return "Please select a location and retrieve the data first."

    prompt: str = _generate_prompt(
        user_question=user_question,
        information=information
        )
    messages.append({"role": "user", "content": prompt})
    return _model_res_generator(messages=messages)


def _generate_prompt(user_question: str, information: str):
    prompt: str = (
        _PROMPT
        + _INSTRUCTION
        + _CONTEXT_TEMPLATE.format(information=information)
        + _QUESTION_TEMPLATE.format(question=user_question)
    )
    return prompt


def _model_res_generator(messages):
    stream = ollama.chat(
        model="llama3.2",
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        yield chunk["message"]["content"]


_PROMPT: str = """skip
**Prompt:**
Act as an assistant with expertise in real estate development, urban planning, and analysis. 
Reply in formal and polite tone.
"""

_INSTRUCTION: str = """
**Instructions**
Answer these questions that user asked from the provided context.
Do not produce any answers that are not mentioned in the provided context.
Do not hallucinate.
"""

_CONTEXT_TEMPLATE: str = """
**Context**

{information}

"""

_QUESTION_TEMPLATE: str = """
**Question**

{question}

"""

_EXISTING_SERVICES: str = """
These are the available services:
* Floor area calculations.
* Population calculations.
"""
