import os
import sys
import subprocess
import click
from dotenv import load_dotenv
from rich import print

load_dotenv()


@click.group()
def main():
    """Run bot or cli/gui helpers"""


@main.command()
def bot():
    """Run the Telegram bot (polling)"""
    from src.bot import CookieBot

    token = os.getenv("BOT_TOKEN")
    b = CookieBot(token=token)
    print("[green]开始运行 bot[/green]")
    b.app.run_polling()


@main.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.pass_context
def cli(ctx):
    """Delegate to the CLI (src.cli) - forwards remaining args"""
    args = ctx.args
    cmd = [sys.executable, "-m", "src.cli"] + list(args)
    subprocess.run(cmd)


@main.command()
def gui():
    """Launch the GUI (PySide6)"""
    from src.gui import run_gui

    run_gui()


if __name__ == "__main__":
    main()
