from api.instagram import InstagramAPI
from api.vtt import VideoToText
from api.chatgpt import GPTConversation

api = InstagramAPI()
reel_info = api.get_reel_info('https://www.instagram.com/reel/CzZWZaNIfiX/')
print(reel_info)
print("recognizing...")
vtt = VideoToText()
transcription = vtt.transcribe_video(reel_info['video_url'])
print(transcription)

print("Asking chatgpt for a recipe...")

conv = GPTConversation()
print(conv.assemble_recipe(reel_info['description'], transcription))

