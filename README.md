Setup and config:
- Install the requirements through pip: `pip install -r requirements.txt`
- Enter your `ACCESS TOKEN` from https://twitchtokengenerator.com in the `OAUTH_TOKEN` field. Include the `oauth:` prefix.
- `USERNAME` is optional. `CHANNEL` is the channel you want to monitor.

Run:
`python3 twitch.py`. A tkinter window should pop up.

Default behavior:
- `RIGHT SHIFT` pauses chat.
- Pausing allows scrolling with `LEFT SHIFT` and `MOUSEWHEEL`.
- Press `RIGHT SHIFT` again to return to autoscroll.

