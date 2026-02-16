import os
import sys
import subprocess
import click
import threading
from dotenv import load_dotenv
from rich import print
import datetime
import glob

load_dotenv()


def check_git_update(ask_pull=False):
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
                    # 询问用户是否要 pull
                    if ask_pull and click.confirm(
                        "是否要拉取远程更新？", default=False
                    ):
                        try:
                            subprocess.run(
                                ["git", "pull"],
                                check=True,
                                capture_output=True,
                                text=True,
                            )
                            print("[green]✅  已成功拉取远程更新[/green]")
                        except subprocess.CalledProcessError as e:
                            print(f"[red]❌  拉取远程更新失败: {e}[/red]")
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
    env_no_update = os.getenv("NO_UPDATE", "").lower() == "true"
    # 如果 .env 中设置了 NO_UPDATE，则使用其值
    if env_no_update:
        no_update_check = True

    # 检查 git 更新（仅针对非 bot 和非 check 命令）
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command not in ["bot", "check"]:
        if not no_update_check:
            # 使用多线程在后台执行 git 更新检查
            git_thread = threading.Thread(target=check_git_update, daemon=True)
            git_thread.start()


@main.command()
def bot():
    """Run the Telegram bot (polling)"""
    from src.bot import CookieBot

    token = os.getenv("BOT_TOKEN")
    print("[green]初始化 bot[/green]")
    b = CookieBot(token=token)
    print("[green]开始运行 bot[/green]")

    # 检查是否需要检查 git 更新
    env_no_update = os.getenv("NO_UPDATE", "").lower() == "true"
    if not env_no_update:
        # 使用多线程在后台执行 git 更新检查（询问是否 pull，pull 后重新运行）
        git_thread = threading.Thread(
            target=check_git_update, args=(True,), daemon=True
        )
        git_thread.start()
        print("[green]已启动 git 更新检查（后台运行）[/green]")

    try:
        b.app.run_polling()
    except KeyboardInterrupt:
        print("[yellow]⚠️  收到中断信号，正在退出...[/yellow]")
    except Exception as e:
        print(f"[red]❌  运行出错: {e}[/red]")


@main.command()
def check():
    """检查更新"""
    # 检查 git 更新（询问是否 pull）
    check_git_update(ask_pull=True)


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
