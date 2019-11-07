import praw
from configparser import ConfigParser
from datetime import datetime, timedelta
import requests, requests.auth
from threading import Thread
import functools
import time


class Post_Bot():

    def __init__(self):
        self.user_agent = "'PostLockBot- EDIT FOR r/eFreebies//V1.02 by ScoopJr'"
        print('Starting up...', self.user_agent)
        CONFIG = ConfigParser()
        CONFIG.read('config.ini')
        self.user = CONFIG.get('main', 'USER')
        self.password = CONFIG.get('main', 'PASSWORD')
        self.client = CONFIG.get('main', 'CLIENT_ID')
        self.secret = CONFIG.get('main', 'SECRET')
        self.timelimit = timedelta(weeks=int(CONFIG.get('main', 'TIMELIMIT')))
        self.subreddit = CONFIG.get('main', 'SUBREDDIT')
        self.command = CONFIG.get('main', 'COMMAND')
        self.token_url = "https://www.reddit.com/api/v1/access_token"
        self.token = ""
        self.t_type = ""
        self.check_timer = datetime.utcnow()
        self.reddit = praw.Reddit(client_id=self.client,
                             client_secret=self.secret,
                             password=self.password,
                             user_agent=self.user_agent,
                             username=self.user)
        self.flair_id = CONFIG.get('main', 'FLAIR_ID')
        self.subs = {}
        self.need_flair = set()

    def get_token(self):
        client_auth = requests.auth.HTTPBasicAuth(self.client, self.secret)
        post_data = {'grant_type': 'password', 'username': self.user, 'password': self.password}
        headers = {'User-Agent': self.user_agent}
        response = requests.Session()
        response2 = response.post(self.token_url, auth=client_auth, data=post_data, headers=headers)
        self.token = response2.json()['access_token']
        self.t_type = response2.json()['token_type']

    def grab_posts(self):
        """Grabs all posts for the subreddit and puts their created_utc, archived status, locked status into a dictionary self.subs categorized under their post.id"""
        for post in self.reddit.subreddit(self.subreddit).new(limit=1000):
            post_time = datetime.utcfromtimestamp(int(post.created_utc)).strftime('%Y-%m-%d %H:%M:%S')
            post_time = datetime.strptime(post_time, '%Y-%m-%d %H:%M:%S')
            self.subs[post.id] = {'created': post_time, 'archived': post.archived, 'locked': post.locked, 'flair_id': post.link_flair_template_id, 'comments': post.comments}
        return self.subs

    def list_delta(self, subs):
        """Takes a list with a datetime object under 'created' and compares it to datetime.utcnow() and the timedelta of 1 week and returns a new list of that comparison."""
        for sub in subs:
            if ((self.check_timer - subs[sub]['created']) > self.timelimit) and (not subs[sub]['archived']) and (self.flair_id != subs[sub]['flair_id']):
                if subs[sub]['locked']:
                    continue
                else:
                    self.need_flair.add(sub)
        return self.need_flair

    def flair_list(self, sub_list):
        """Simply goes through each submission and flairs them with the flair_id setup in config."""
        if not sub_list:
            return print('Your subreddit has no submissions that need to be flaired.')
        else:
            for sub in sub_list:
                self.reddit.submission(sub).flair.select(self.flair_id)
            return print('Done.')

    def check_expired(self, sub_ids):
        """Runs through a dictionary of post comments and returns those that need flairs"""
        for sub in sub_ids:
            for comment in self.subs[sub]['comments']:
                if str(comment.body) == str(self.command):
                    self.need_flair.add(sub)
                elif str(comment.body) != str(self.command):
                    continue
        return self.need_flair

    def run_bot(self):
        list1 = self.grab_posts()
        Thread(target = functools.partial(self.list_delta, list1)).start()
        final_list = Thread(target = functools.partial(self.check_expired, self.need_flair)).start()
        return self.flair_list(final_list)







if __name__ == "__main__":
    bot = Post_Bot()
    while True:
        print('Your bot is running in the background.')
        bot.run_bot()
        print('Bot is done running, sleeping for 120 seconds.')
        time.sleep(120)


