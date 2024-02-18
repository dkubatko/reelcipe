from instagrapi import Client
from config import ACCOUNT_USERNAME, ACCOUNT_PASSWORD
from instagrapi.exceptions import LoginRequired
import logging
import os


class InstagramAPI:
    def __init__(self):
        self.cl = Client()

        session = None
        if os.path.exists("session.json"):
            session = self.cl.load_settings("session.json")
            logging.info("Instagram session found!")

        try:
            if session:
                self.login_via_session(session)
                logging.info("Logged in to Instagram via existing session.")
            else:
                self.login_via_password()
                logging.info("Logged in to Instagram via login / password with no session.")
        # If the session is invalid, we need to login via password reusing old session data.
        except LoginRequired:
            old_session = self.cl.get_settings()
            self.login_via_password(old_session)
            logging.info("Logged in to Instagram via login / password with existing session data.")
        except Exception as e:
            logging.error(f"Error logging in to Instagram: {e}")
            raise e

        # Save Instagram setting to reuse across application restarts.
        self.cl.dump_settings("session.json")

    def login_via_session(self, session=None) -> bool:
        if not session:
            return False

        self.cl.set_settings(session)
        self.cl.login(ACCOUNT_USERNAME, ACCOUNT_PASSWORD)

        # This can throw LoginRequired
        self.cl.get_timeline_feed()

    def login_via_password(self, old_session=None) -> bool:
        if old_session:
            self.cl.set_settings({})
            self.cl.set_uuids(old_session["uuids"])

        self.cl.login(ACCOUNT_USERNAME, ACCOUNT_PASSWORD)
        self.cl.get_timeline_feed()

    def get_reel_info(self, link: str):
        media_pk = self.cl.media_pk_from_url(link)

        if not media_pk:
            return None

        media_info = self.cl.media_info(media_pk)

        if not media_info:
            return None

        return {
            "description": media_info.caption_text,
            "video_url": media_info.video_url,
        }
