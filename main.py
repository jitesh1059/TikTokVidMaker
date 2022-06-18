import praw
from gtts import gTTS
from pathlib import Path
from mutagen.mp3 import MP3
from rich.progress import track
import requests
import random
from playwright.sync_api import sync_playwright, ViewportSize
import json
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    concatenate_videoclips,
    concatenate_audioclips,
    CompositeAudioClip,
    CompositeVideoClip,
)
import random
from random import randrange
from pytube import YouTube
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip
import re
from os import listdir, environ
from moviepy.video.io import ffmpeg_tools

theme = "dark"
W, H = 1080, 1920
opacity = "0.9"

def reddit_object():
    name = str(input("Please input a name for your video: "))
    content = {}
    reddit = praw.Reddit(
        client_id="8jrXecmLwkW93TuWPOJP6w",
        client_secret="EoUz2jn4WW2o23T56QqQ9-382nbEoA",
        password="Jitesh2910",
        user_agent="testscript by u/AudioDuck1059",
        username="AudioDuck1059",
    )

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
    
    return content, url, name


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
    tts.save(f"assets/mp3/title.mp3")
    length += MP3(
        f"assets/mp3/title.mp3").info.length

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
        tts.save(f"assets/mp3/{idx}.mp3")
        length += MP3(
            f"assets/mp3/{idx}.mp3").info.length

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
                    path=f"assets/png/comment_{idx}.png"
                )
            
            print("Screenshots downloaded Successfully.")

def get_start_and_end_times(video_length, length_of_clip):
    random_time = randrange(180, int(length_of_clip) - int(video_length))
    return random_time, random_time + video_length

def download_background():
    """Downloads the backgrounds/s video from YouTube."""
    Path("./assets/backgrounds/").mkdir(parents=True, exist_ok=True)
    background_options = [  # uri , filename , credit
        ("https://www.youtube.com/watch?v=n_Dv4JMiwK8", "parkour.mp4", "bbswitzer"),
    ]
    # note: make sure the file name doesn't include an - in it
    if not len(listdir("./assets/backgrounds")) >= len(
        background_options
    ):  # if there are any background videos not installed
        print(
            "We need to download the backgrounds videos. they are fairly large but it's only done once. 😎"
        )
        print("Downloading the backgrounds videos... please be patient 🙏 ")
        for uri, filename, credit in background_options:
            if Path(f"assets/backgrounds/{credit}-{filename}").is_file():
                continue  # adds check to see if file exists before downloading
            print(f"Downloading {filename} from {uri}")
            YouTube(uri).streams.filter(res="1080p").first().download(
                "assets/backgrounds", filename=f"{credit}-{filename}"
            )

        print(
            "Background videos downloaded successfully! 🎉"
        )


def chop_background_video(video_length):
    print("Finding a spot in the backgrounds video to chop...✂️")

    background = VideoFileClip(f"assets/backgrounds/bbswitzer-parkour.mp4")

    start_time, end_time = get_start_and_end_times(video_length, background.duration)
    ffmpeg_extract_subclip(
        f"assets/backgrounds/bbswitzer-parkour.mp4",
        start_time,
        end_time,
        targetname="assets/temp/background.mp4",
    )
    print("Background video chopped successfully!")
    return True


def make_final_video(number_of_clips, length, name, url, new_obj):
    print_step("Creating the final video 🎥")
    VideoFileClip.reW = lambda clip: clip.resize(width=W)
    VideoFileClip.reH = lambda clip: clip.resize(width=H)
    background_clip = (
        VideoFileClip("assets/temp/background.mp4")
        .without_audio()
        .resize(height=H)
        .crop(x1=1166.6, y1=0, x2=2246.6, y2=1920)
    )

    # Gather all audio clips
    audio_clips = []
    for i in range(0, number_of_clips):
        audio_clips.append(AudioFileClip(f"assets/temp/mp3/{i}.mp3"))
    audio_clips.insert(0, AudioFileClip(f"assets/temp/mp3/title.mp3"))
    audio_concat = concatenate_audioclips(audio_clips)
    audio_composite = CompositeAudioClip([audio_concat])

    # Get sum of all clip lengths
    total_length = sum([clip.duration for clip in audio_clips])
    # round total_length to an integer
    int_total_length = round(total_length)
    # Output Length
    console.log(f"[bold green] Video Will Be: {int_total_length} Seconds Long")

    # add title to video
    image_clips = []
    # Gather all images
    if (
            opacity is None or float(opacity) >= 1
    ):  # opacity not set or is set to one OR MORE
        image_clips.insert(
            0,
            ImageClip(f"assets/temp/png/title.png")
            .set_duration(audio_clips[0].duration)
            .set_position("center")
            .resize(width=W - 100)
            .set_opacity(float(opacity)),
        )
    else:
        image_clips.insert(
            0,
            ImageClip(f"assets/temp/png/title.png")
            .set_duration(audio_clips[0].duration)
            .set_position("center")
            .resize(width=W - 100))

    for i in range(0, number_of_clips):
        if (
                opacity is None or float(opacity) >= 1
        ):  # opacity not set or is set to one OR MORE
            image_clips.append(
                ImageClip(f"assets/temp/png/comment_{i}.png")
                .set_duration(audio_clips[i + 1].duration)
                .set_position("center")
                .resize(width=W - 100),
            )
        else:
            image_clips.append(
                ImageClip(f"assets/temp/png/comment_{i}.png")
                .set_duration(audio_clips[i + 1].duration)
                .set_position("center")
                .resize(width=W - 100)
                .set_opacity(float(opacity)),
            )

    # if os.path.exists("assets/mp3/posttext.mp3"):
    #    image_clips.insert(
    #        0,
    #        ImageClip("assets/png/title.png")
    #        .set_duration(audio_clips[0].duration + audio_clips[1].duration)
    #        .set_position("center")
    #        .resize(width=W - 100)
    #        .set_opacity(float(opacity)),
    #    )
    # else:
    image_concat = concatenate_videoclips(image_clips).set_position(
        ("center", "center")
    )
    image_concat.audio = audio_composite
    final = CompositeVideoClip([background_clip, image_concat])

    def get_video_title() -> str:
        title = name
        if len(title) <= 35:
            return title
        else:
            return title[0:30] + "..."

    filename = f"{get_video_title()}.mp4"

    def save_data():
        with open("./video_creation/data/videos.json", "r+") as raw_vids:
            done_vids = json.load(raw_vids)
            if str(subreddit.submission.id) in [video["id"] for video in done_vids]:
                return  # video already done but was specified to continue anyway in the .env file
            payload = {
                "time": str(int(time.time())),
                "reddit_title": str(name),
                "filename": filename
            }
            done_vids.append(payload)
            raw_vids.seek(0)
            json.dump(done_vids, raw_vids, ensure_ascii=False, indent=4)

    save_data()
    if not exists("./results"):
        print_substep("the results folder didn't exist so I made it")
        os.mkdir("./results")

    final.write_videofile(
        "assets/temp/temp.mp4", fps=30, audio_codec="aac", audio_bitrate="192k"
    )
    ffmpeg_tools.ffmpeg_extract_subclip(
        "assets/temp/temp.mp4", 0, length, targetname=f"results/{filename}"
    )
    # os.remove("assets/temp/temp.mp4")

    print_step("Removing temporary files 🗑")
    cleanups = cleanup()
    print_substep(f"Removed {cleanups} temporary files 🗑")
    print_substep(f"See result in the results folder!")

    print_step(
        f"Reddit title: {name}"
    )

banner = """
██████╗ ███████╗██████╗ ██████╗ ██╗████████╗    ██╗   ██╗██╗██████╗ ███████╗ ██████╗     ███╗   ███╗ █████╗ ██╗  ██╗███████╗██████╗ 
██╔══██╗██╔════╝██╔══██╗██╔══██╗██║╚══██╔══╝    ██║   ██║██║██╔══██╗██╔════╝██╔═══██╗    ████╗ ████║██╔══██╗██║ ██╔╝██╔════╝██╔══██╗
██████╔╝█████╗  ██║  ██║██║  ██║██║   ██║       ██║   ██║██║██║  ██║█████╗  ██║   ██║    ██╔████╔██║███████║█████╔╝ █████╗  ██████╔╝
██╔══██╗██╔══╝  ██║  ██║██║  ██║██║   ██║       ╚██╗ ██╔╝██║██║  ██║██╔══╝  ██║   ██║    ██║╚██╔╝██║██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗
██║  ██║███████╗██████╔╝██████╔╝██║   ██║        ╚████╔╝ ██║██████╔╝███████╗╚██████╔╝    ██║ ╚═╝ ██║██║  ██║██║  ██╗███████╗██║  ██║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═════╝ ╚═╝   ╚═╝         ╚═══╝  ╚═╝╚═════╝ ╚══════╝ ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
"""
print(banner)
new_obj, url, name = reddit_object()
length, number_of_comments = save_text_to_mp3(new_obj)
download_screenshots_of_reddit_posts(
    new_obj, url,  number_of_comments, theme
)
download_background()
chop_background_video(length)
make_final_video(number_of_comments, length, name, url, new_obj)
