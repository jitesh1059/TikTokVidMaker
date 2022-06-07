import praw

reddit = praw.Reddit(
    client_id="8jrXecmLwkW93TuWPOJP6w",
    client_secret="EoUz2jn4WW2o23T56QqQ9-382nbEoA",
    password="Jitesh2910",
    user_agent="testscript by u/AudioDuck1059",
    username="AudioDuck1059",
)

print(reddit.user.me())

url = str(input("Please input the reddit URL: "))
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
print(content)