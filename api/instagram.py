from instagrapi import Client
from config import ACCOUNT_USERNAME, ACCOUNT_PASSWORD

class InstagramAPI: 
  def __init__(self):
    self.cl = Client()
    self.cl.login(ACCOUNT_USERNAME, ACCOUNT_PASSWORD)

  def get_reel_info(self, link: str):
    media_pk = self.cl.media_pk_from_url(link)
    
    if not media_pk:
      return None
    
    media_info = self.cl.media_info(media_pk)

    if not media_info:
      return None
    
    return {
      'description': media_info.caption_text,
      'video_url': media_info.video_url,
    }
