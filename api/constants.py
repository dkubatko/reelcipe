RECIPE_ASSEMBLY_TEXT = '''
Hello ChatGPT. Your task is to assemble a recipe given the following description and transcription of a short video.
Description: {description}
Transcription: {transcription}

Use the following template
<Recipe Title>
<Ingredients>
<Instructions>
with appropriate formatting. Use emoji as you see fit.

Given those, please provide me a concise step-by-step recipe with a title, ingredients, and instructions in {language} locale.
Please use Telegram MarkdownV2 compliant formatting for the recipe. Only use options form this ruleset:
*bold \*text*
_italic \*text_
__underline__
~strikethrough~
||spoiler||
'''

RECIPE_TRANSLATION_TEXT = '''
This is a generated recipe that needs translation to {original_language}. Please translate it to {translation_language} and send it back to me.
*Please make sure to preserve formatting, emoji and structure.*

{recipe}
'''

START_MESSAGE = 'Welcome to Reelcipe! Send me a link to an Instagram reel and I will transcribe it into a step-by-step recipe.'
INVALID_MESSAGE = 'Hmm... Does not look like an Instagram Reel link to me! Please send me a link to an Instagram Reel and I will convert it to a recipe.'
ERROR_MESSAGE = 'Error processing the reel. Please try again with a different link.'