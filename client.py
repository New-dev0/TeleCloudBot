from swibots import Client, BotCommand, AppBar
from config import Config

app_bar = AppBar(
    "TeleCloud",
    left_icon="https://f004.backblazeb2.com/file/switch-bucket/b56ec7a0-c44f-11ee-9cb5-a4b7a49d7fec.png",
    secondary_icon="https://f004.backblazeb2.com/file/switch-bucket/baa3db33-c44f-11ee-837e-a4b7a49d7fec.png",
)

app = Client(Config.BOT_TOKEN, app_bar=app_bar, plugins=dict(root="plugins"))
app.set_bot_commands(
    [
        BotCommand("start", "Get start message", True),
        BotCommand("share", "View file by share link", True),
        BotCommand("folder", "Add folder by share link", True),
        #        BotCommand("add", "Add Telegram Chat", True),
    ]
)

# print(app.run(app.upload_media(r"C:\Users\Deves\Downloads\isometric-open-box.png")))

work_loads = {0: 0}
# multi_clients = {}
