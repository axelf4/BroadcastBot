import os
import re
import time
import praw
import traceback
import psycopg2
import urllib.parse
from apscheduler.schedulers.blocking import BlockingScheduler

reddit = praw.Reddit(
        client_id = os.environ["CLIENT_ID"],
        client_secret = os.environ["CLIENT_SECRET"],
        password = os.environ["PASSWORD"],
        user_agent="BroadcastBot v1.0 by /u/pwnedary",
        username = os.environ["USERNAME"])

urllib.parse.uses_netloc.append("postgres")
url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port)
cursor = conn.cursor()

sched = BlockingScheduler()

print("BroadcastBot v1.0 by Axel F")

replyMessage = (
        "Click [here](https://np.reddit.com/message/compose/?to=BroadcastBot&subject=Subscription&message=SubscribeTo! {id}) to subscribe!\n\n"
        "Click [here](https://np.reddit.com/message/compose/?to=BroadcastBot&subject=Broadcast&message=BroadcastTo! {id}, message:%0A%0APermalink: {permalink}) if you are /u/{user} and want to broadcast.\n\n")
broadcastMessage = (
        "{author} broadcasted a message in a channel that you've subscribed to!\n\n"
        "**The message:** \n\n>{message}")

blacklist = frozenset([
    "talesfromyourserver", "bmw", "anime", "asianamerican",
    "askhistorians", "askscience", "askreddit", "aww",
    "chicagosuburbs", "cosplay", "cumberbitches", "d3gf",
    "deer", "depression", "depthhub", "drinkingdollars",
    "forwardsfromgrandma", "geckos", "giraffes", "grindsmygears",
    "indianfetish", "me_irl", "misc", "movies",
    "mixedbreeds", "news", "newtotf2", "omaha",
    "petstacking", "pics", "pigs", "politicaldiscussion",
    "politics", "programmingcirclejerk", "raerthdev", "rants",
    "runningcirclejerk", "salvia", "science", "seiko",
    "shoplifting", "sketches", "sociopath", "suicidewatch",
    "talesfromtechsupport", "torrent", "torrents", "trackers",
    "tr4shbros", "unitedkingdom", "crucibleplaybook" "benfrick",
    "bsa", "futurology", "graphic_design", "historicalwhatif",
    "lolgrindr", "malifaux", "nfl", "toonami",
    "trumpet", "ps2ceres", "duelingcorner"
    ])

subscribeRegex = re.compile(r"^SubscribeTo! (?P<id>\w+)$")
broadcastRegex = re.compile(r"^BroadcastTo! (?P<id>\w+?), message:(?P<message>[\s\S]*)$")

def processPM(message):
    m = subscribeRegex.fullmatch(message.body)
    if m:
        print("Subscribing /u/{} to {}.".format(message.author, m.group("id")))
        sql = "INSERT INTO subscribers (name, id) \
                VALUES ('%s', '%s')" % \
                (message.author, m.group("id"))
        try:
            cursor.execute(sql)
            conn.commit()
        except:
            conn.rollback()
        return

    m = broadcastRegex.fullmatch(message.body)
    if m:
        # Only allow the original commenter to broadcast
        comment = praw.models.Comment(reddit, m.group("id"));
        if comment.author == message.author:
            print("Broadcast to {} by /u/{}.".format(m.group("id"), message.author))
            sql = "SELECT DISTINCT name FROM subscribers \
                    WHERE id = '%s'" % (m.group("id"))
            cursor.execute(sql)
            for row in cursor.fetchall():
                reddit.redditor(row[0]).message("New broadcast via yours truly.", m.group("message"))

def processMention(comment):
    print("Got mentioned in comment {} by {} on /r/{}.".format(comment.id, comment.author, comment.subreddit))
    if str(comment.subreddit) in blacklist: return
    comment.reply(replyMessage.format(
        user = comment.author,
        id = comment.id,
        permalink = comment.permalink()))

@sched.scheduled_job('interval', minutes = 5)
def main():
    try:
        for item in reddit.inbox.unread(limit = 100):
            if isinstance(item, praw.models.Message):
                processPM(item) # Received a PM
            if isinstance(item, praw.models.Comment):
                processMention(item) # Someone mentioned us
            item.mark_read()
    except Exception as err:
        print(traceback.format_exc())

sched.start()
conn.close()
