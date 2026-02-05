import os
import sys
import subprocess
import click
from dotenv import load_dotenv
from rich import print

load_dotenv()


def check_git_update():
    """Check if git repository needs update"""
    try:
        # 检查是否在 git 仓库中
        subprocess.run(["git", "rev-parse"], check=True, capture_output=True, text=True)

        # 获取远程分支最新提交
        subprocess.run(["git", "fetch"], check=True, capture_output=True, text=True)

        # 比较本地和远程分支
        result = subprocess.run(
            ["git", "status", "--porcelain", "-b"],
            check=True,
            capture_output=True,
            text=True,
        )

        output = result.stdout

        # 检查是否有未推送的本地更改
        has_local_changes = False
        for line in output.split("\n"):
            if line.startswith("##"):
                if "ahead" in line:
                    print("[yellow]⚠️  本地分支领先于远程分支[/yellow]")
                    has_local_changes = True
                elif "behind" in line:
                    print("[green]🔄  发现远程更新，需要拉取[/green]")
                    return True
            elif line.strip():
                print("[yellow]⚠️  有未提交的本地更改[/yellow]")
                has_local_changes = True

        if not has_local_changes:
            print("[green]✅  代码已是最新版本[/green]")

        return False

    except subprocess.CalledProcessError:
        # git 命令失败，可能不是 git 仓库
        print("[yellow]⚠️  未检测到 git 仓库，跳过更新检查[/yellow]")
        return False
    except FileNotFoundError:
        # git 命令不存在
        print("[yellow]⚠️  未找到 git 命令，跳过更新检查[/yellow]")
        return False


@click.group()
@click.option("--no-update-check", is_flag=True, default=False, help="跳过更新检查")
def main(no_update_check):
    """Run bot or cli/gui helpers"""
    # 检查 .env 文件中的 NO_UPDATE 环境变量
    env_no_update = os.getenv("NO_UPDATE", "").lower() in ["true", "1", "yes", "y"]
    # 如果 .env 中设置了 NO_UPDATE，则使用其值
    if env_no_update:
        no_update_check = True
    if not no_update_check:
        check_git_update()


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
