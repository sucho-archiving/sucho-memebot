# SUCHO Memebot

[![Post a Memes](https://github.com/simonwiles/sucho-memebot/actions/workflows/post_meme.yml/badge.svg)](https://github.com/simonwiles/sucho-memebot/actions/workflows/post_meme.yml)

Posts a random meme from the SUCHO Meme Wall to Mastodon every 2 hours.


<a rel="me" href="https://mastodon.online/@sucho_memes">
<img alt="" height="18" src="https://upload.wikimedia.org/wikipedia/commons/4/48/Mastodon_Logotype_%28Simple%29.svg" />
@sucho_memes@mastodon.online</a>


## How it works

* The [memebot script](memebot.py) fetches the [SUCHO Meme Wall RSS feed](https://memes.sucho.org/rss.xml) and selects a meme at random from those that haven't yet been posted.
* The bot uses the Mastodon REST API to post the media file and then to post a new status.
* If ths post is successful, [`posted.log`](posted.log) is updated with the ID of the posted meme, as well as the posted time and the post URI.
* A [GitHub Actions workflow](.github/workflows/post_meme.yml) is scheduled to run every two hours.  The workflow executes the memebot script and commits the updated `posted.log` back to the repo.
