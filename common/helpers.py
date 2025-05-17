def get_prompt(prompt: str, **kwargs):
    for k, v in kwargs.items():
        prompt = prompt.replace('{' + k + '}', str(v))

    return prompt
