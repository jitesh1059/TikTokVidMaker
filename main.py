import praw
from gtts import gTTS
from pathlib import Path
from mutagen.mp3 import MP3
from rich.progress import track
import requests
import random
from playwright.sync_api import sync_playwright, ViewportSize
import json

theme = "dark"

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

        print("Received threads successfully.")

    else:
        name = str(input("Please input a name for your video: "))
        num = int(input("Please input the number of threads you would like to use (Recommended value is 5-8): "))
        buggy_name = url.split("/r/",1)[1]
        import requests
        
        # note that CLIENT_ID refers to 'personal use script' and SECRET_TOKEN to 'token'
        auth = requests.auth.HTTPBasicAuth('8jrXecmLwkW93TuWPOJP6w', 'EoUz2jn4WW2o23T56QqQ9-382nbEoA')

        # here we pass our login method (password), username, and password
        data = {'grant_type': 'password',
                'username': 'AudioDuck1059',
                'password': 'Jitesh2910'}

        # setup our header info, which gives reddit a brief description of our app
        headers = {'User-Agent': 'MyBot/0.0.1'}

        # send our request for an OAuth token
        res = requests.post('https://www.reddit.com/api/v1/access_token',
                            auth=auth, data=data, headers=headers)

        # convert response to JSON and pull access_token value
        TOKEN = res.json()['access_token']

        # add authorization to our headers dictionary
        headers = {**headers, **{'Authorization': f"bearer {TOKEN}"}}

        # while the token is valid (~2 hours) we just add headers=headers to our requests
        requests.get('https://oauth.reddit.com/api/v1/me', headers=headers)

        res = requests.get(f"https://oauth.reddit.com/r/{buggy_name}new",
                    headers=headers, params = {"limit": num})

        item = res.json()['data']['children'][0]
        print(item['data']['id'])
        
        try:
            content["thread_title"] = f"{name}"
            content["thread_url"] = url
            content["comments"] = []
            content["thread_post"] = ""
            new_list = []
            for post in res.json()['data']['children']:
            #     new_list.append(post["data"]["title"])
            
            # newest_list = random.choices(new_list, weights=None, cum_weights = None, k = num)

            # for i in range(len(newest_list)):
                content["comments"].append(
                    {
                        "comment_body": post["data"]["title"], #newest_list[i]
                        "comment_id": post["data"]["id"]
                    }
                )
            

        except AttributeError as e:
            pass

        print("Received threads successfully.")
    
    return content, url


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
        tts.save(f"assets/mp3/{reddit_obj['thread_title']}-{idx}.mp3")
        length += MP3(
            f"assets/mp3/{reddit_obj['thread_title']}-{idx}.mp3").info.length

    return idx, length


def download_screenshots_of_reddit_posts(reddit_object, url, screenshot_num, theme):
    """Downloads screenshots of reddit posts as they are seen on the web.
    Args:
        reddit_object: The Reddit Object you received in askreddit.py
        screenshot_num: The number of screenshots you want to download.
    """
    print("Downloading Screenshots of Reddit Posts 📷")

    # ! Make sure the reddit screenshots folder exists
    Path("assets/png").mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        print("Launching Headless Browser...")

        browser = p.chromium.launch()
        context = browser.new_context()

        if theme.casefold() == "dark":
            cookie_file = open('video_creation/cookies.json')
            cookies = json.load(cookie_file)
            context.add_cookies(cookies)

        # Get the thread screenshot
        page = context.new_page()
        page.goto(reddit_object["thread_url"])
        page.set_viewport_size(ViewportSize(width=1920, height=1080))
        

        substring = "comments"
        if url.find(substring) != -1:
            if page.locator('[data-testid="content-gate"]').is_visible():
                # This means the post is NSFW and requires to click the proceed button.

                print("Post is NSFW. You are spicy...")
                page.locator('[data-testid="content-gate"] button').click()

            page.locator('[data-test-id="post-content"]').screenshot(
                path="assets/png/title.png"
            )

            for idx, comment in track(
                enumerate(reddit_object["comments"]), "Downloading screenshots..."
            ):

                # Stop if we have reached the screenshot_num
                if idx >= screenshot_num:
                    break

                if page.locator('[data-testid="content-gate"]').is_visible():
                    page.locator('[data-testid="content-gate"] button').click()

                page.goto(f'https://reddit.com{comment["comment_url"]}')
                page.locator(f"#t1_{comment['comment_id']}").screenshot(
                    path=f"assets/png/comment_{idx}.png"
                )

            print("Screenshots downloaded Successfully.")
        
        else:
            buggy_name = url.split("/r/",1)[1]
            buggy_name = buggy_name[:-1]
            url = url + "new"
            page.locator("h1", has_text=f"{buggy_name}").screenshot(
                path="assets/png/title.png"
            )
            
            for idx, comment in track(
                enumerate(reddit_object["comments"]), "Downloading screenshots..."
            ):
                # Stop if we have reached the screenshot_num
                if idx >= screenshot_num:
                    break
                
                page.goto(url)
                page.locator(f'#t3_{comment["comment_id"]}').screenshot(
                    path=f"assets/png/{buggy_name}comment_{idx}.png"
                )
            
            print("Screenshots downloaded Successfully.")


new_obj, url = reddit_object()
length, number_of_comments = save_text_to_mp3(new_obj)
download_screenshots_of_reddit_posts(
    new_obj, url,  number_of_comments, theme
)
