from openai import OpenAI
from config import OPENAI_API_KEY
from api.constants import RECIPE_ASSEMBLY_TEXT, RECIPE_TRANSLATION_TEXT
from typing import Dict
import json

def escape_markdown(text):
    escaped_characters = "![]()-}{.~#|"
    for char in escaped_characters:
        text = text.replace(char, "\\" + char)
    return text

class GPTAPI:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def send(self, prompt: str, context: list[dict]):
        context += [{"role":"user", "content": prompt}]
    
        result = self.client.chat.completions.create(
            model = "gpt-4-1106-preview", 
            messages = context
        )

        return context + [{
            'role': 'assistant',
            'content': result.choices[0].message.content
        }]

    
class GPTConversation:
    def __init__(self, gpt: GPTAPI = GPTAPI()):
        self.gpt = gpt
        self.context = []
        self.language = 'en'

    def set_language(self, language: str):
        self.language = language

    def message(self, prompt):
        self.context = self.gpt.send(prompt, self.context)
        return self.context[-2:]
    
    def assemble_recipe(self, caption, transcription) -> str:
        # Clear context for the recipe generation.
        self.context.clear()
        self.context = self.gpt.send(
            RECIPE_ASSEMBLY_TEXT.format(description=caption, 
                                        transcription=transcription, 
                                        language=self.language.upper()), 
            self.context)
        return escape_markdown(self.response())
    
    def translate(self, recipe: str, from_lang: str, to_lang: str) -> str:
        self.context.clear()
        self.context = self.gpt.send(
            RECIPE_TRANSLATION_TEXT.format(original_language = from_lang, 
                                           translation_language = to_lang, 
                                           recipe = recipe), 
                                           self.context
        )
        return escape_markdown(self.response())
    
    def response(self) -> str:
       return self.context[-1]['content']
