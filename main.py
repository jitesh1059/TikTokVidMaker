import praw
from gtts import gTTS
from pathlib import Path
from mutagen.mp3 import MP3
from rich.progress import track
import requests
from bs4 import BeautifulSoup


def reddit_object():
    content = {}
    reddit = praw.Reddit(
        client_id="8jrXecmLwkW93TuWPOJP6w",
        client_secret="EoUz2jn4WW2o23T56QqQ9-382nbEoA",
        password="Jitesh2910",
        user_agent="testscript by u/AudioDuck1059",
        username="AudioDuck1059",
    )

    print(reddit.user.me())

    url = str(input("Please input the reddit URL: "))
    substring = "comments"

    if url.find(substring) != -1:
        submission = reddit.submission(url=url)
        try:
            content["thread_url"] = submission.url
            content["thread_title"] = submission.title
            content["thread_post"] = submission.selftext
            content["comments"] = []

            for top_level_comment in submission.comments:
                if not top_level_comment.stickied:
                    content["comments"].append(
                        {
                            "comment_body": top_level_comment.body,
                            "comment_url": top_level_comment.permalink,
                            "comment_id": top_level_comment.id,
                        }
                    )

        except AttributeError as e:
            pass

        print("Received AskReddit threads successfully.")
    
    else:
        x = requests.get(url)
        print(x.text)


def save_text_to_mp3(reddit_obj):
    """Saves Text to MP3 files.
    Args:
        reddit_obj : The reddit object you received from the reddit API in the askreddit.py file.
    """
    print("Saving Text to MP3 files...")
    length = 0

    # Create a folder for the mp3 files.
    Path("assets/mp3").mkdir(parents=True, exist_ok=True)
    print(reddit_obj['thread_title'])

    tts = gTTS(text=reddit_obj["thread_title"], lang="en", slow=False)
    tts.save(f"assets/mp3/{reddit_obj['thread_title']}title.mp3")
    length += MP3(
        f"assets/mp3/{reddit_obj['thread_title']}title.mp3").info.length

    try:
        Path(f"assets/mp3/posttext.mp3").unlink()
    except OSError as e:
        pass

    if reddit_obj["thread_post"] != "":
        tts = gTTS(text=reddit_obj["thread_post"], lang="en", slow=False)
        tts.save(f"assets/mp3/posttext.mp3")
        length += MP3(f"assets/mp3/posttext.mp3").info.length

    for idx, comment in track(enumerate(reddit_obj["comments"]), "Saving..."):
        # ! Stop creating mp3 files if the length is greater than 50 seconds. This can be longer, but this is just a good starting point
        if length > 50:
            break
        tts = gTTS(text=comment["comment_body"], lang="en", slow=False)
        tts.save(f"assets/mp3/{reddit_obj['thread_title']}{idx}.mp3")
        length += MP3(
            f"assets/mp3/{reddit_obj['thread_title']}{idx}.mp3").info.length

    return idx, length

reddit_object()