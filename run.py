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


def cleanup_logs():
    """清理超过1天的日志文件"""
    # 获取日志目录路径，默认在 data/logs 目录
    log_dir = os.getenv(
        "LOG_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"),
    )

    # 检查日志目录是否存在
    if not os.path.exists(log_dir):
        print(f"[yellow]⚠️  日志目录不存在: {log_dir}[/yellow]")
        return

    # 计算1天前的时间
    one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)

    # 查找所有日志文件
    log_files = glob.glob(os.path.join(log_dir, "*.log"))

    # 统计清理的文件数量
    cleaned_count = 0
    deleted_count = 0

    # 遍历日志文件
    for log_file in log_files:
        try:
            # 尝试获取文件的创建时间（birth time）
            if sys.platform == "win32":
                # Windows 平台
                import win32file
                import win32con

                handle = win32file.CreateFile(
                    log_file,
                    win32con.GENERIC_READ,
                    win32con.FILE_SHARE_READ
                    | win32con.FILE_SHARE_WRITE
                    | win32con.FILE_SHARE_DELETE,
                    None,
                    win32con.OPEN_EXISTING,
                    win32con.FILE_FLAG_BACKUP_SEMANTICS,
                    None,
                )
                creation_time = win32file.GetFileTime(handle)[0]
                file_time = datetime.datetime.fromtimestamp(
                    win32file.FileTimeToSystemTime(creation_time).GetTime()
                )
                win32file.CloseHandle(handle)
            else:
                # Unix 平台
                stat_info = os.stat(log_file)
                try:
                    # 尝试获取创建时间
                    file_time = datetime.datetime.fromtimestamp(stat_info.st_birthtime)
                except AttributeError:
                    # 如果不支持创建时间，则使用修改时间
                    file_time = datetime.datetime.fromtimestamp(stat_info.st_mtime)
        except Exception:
            # 如果获取创建时间失败，则使用修改时间作为备选
            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(log_file))

        # 如果文件时间超过1天，则清空或删除
        if file_time < one_day_ago:
            try:
                # 尝试清空文件内容
                with open(log_file, "w") as f:
                    f.truncate()
                cleaned_count += 1
                print(
                    f"[green]🗑️  清空过期日志文件: {os.path.basename(log_file)}[/green]"
                )
            except Exception as e:
                # 如果清空失败，则尝试删除文件
                try:
                    os.remove(log_file)
                    deleted_count += 1
                    print(
                        f"[yellow]⚠️  清空失败，删除过期日志文件: {os.path.basename(log_file)}[/yellow]"
                    )
                except Exception as e2:
                    print(
                        f"[red]❌  删除日志文件失败 {os.path.basename(log_file)}: {e2}[/red]"
                    )

    # 输出清理结果
    if cleaned_count > 0:
        print(f"[green]✅  清理完成，共清空 {cleaned_count} 个过期日志文件[/green]")
    if deleted_count > 0:
        print(f"[yellow]⚠️  清空失败，共删除 {deleted_count} 个过期日志文件[/yellow]")
    if cleaned_count == 0 and deleted_count == 0:
        print(f"[green]✅  无过期日志文件需要清理[/green]")


def check_git_update(ask_pull=False, restart_after_pull=False):
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
                            # 如果需要在 pull 后重新运行
                            if restart_after_pull:
                                print("[yellow]🔄  正在重新启动程序...[/yellow]")
                                # 使用当前 Python 解释器重新运行程序
                                # 使用 subprocess 启动新进程，确保当前进程完全退出
                                subprocess.Popen([sys.executable] + sys.argv)
                                # 退出当前进程
                                sys.exit(0)
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
@click.option("--no-log-cleanup", is_flag=True, default=False, help="跳过日志清理")
def main(no_update_check, no_log_cleanup):
    """Run bot or cli/gui helpers"""
    # 检查 .env 文件中的 NO_LOG_CLEANUP 环境变量
    env_no_log_cleanup = os.getenv("NO_LOG_CLEANUP", "").lower() == "true"
    # 如果 .env 中设置了 NO_LOG_CLEANUP，则使用其值
    if env_no_log_cleanup:
        no_log_cleanup = True

    # 检查 .env 文件中的 NO_UPDATE 环境变量
    env_no_update = os.getenv("NO_UPDATE", "").lower() == "true"
    # 如果 .env 中设置了 NO_UPDATE，则使用其值
    if env_no_update:
        no_update_check = True

    # 清理过期日志文件和检查 git 更新（仅针对非 bot 和非 check 命令）
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command not in ["bot", "check"]:
        if not no_log_cleanup:
            cleanup_logs()
        if not no_update_check:
            # 使用多线程在后台执行 git 更新检查
            git_thread = threading.Thread(target=check_git_update, daemon=True)
            git_thread.start()


def periodic_log_cleanup():
    """定期清理过期日志文件"""
    # 在后台线程中执行清理，避免阻塞
    cleanup_thread = threading.Thread(target=cleanup_logs, daemon=True)
    cleanup_thread.start()
    # 1小时后再次执行
    timer = threading.Timer(3600, periodic_log_cleanup)
    timer.daemon = True
    timer.start()


@main.command()
def bot():
    """Run the Telegram bot (polling)"""
    from src.bot import CookieBot

    token = os.getenv("BOT_TOKEN")
    print("[green]初始化 bot[/green]")
    b = CookieBot(token=token)
    print("[green]开始运行 bot[/green]")

    # 检查是否需要定期清理日志
    env_no_log_cleanup = os.getenv("NO_LOG_CLEANUP", "").lower() == "true"
    if not env_no_log_cleanup:
        # 立即执行一次日志清理
        cleanup_logs()
        # 启动定期日志清理任务
        timer = threading.Timer(3600, periodic_log_cleanup)
        timer.daemon = True
        timer.start()
        print("[green]已启动定期日志清理任务（每小时执行一次）[/green]")

    # 检查是否需要检查 git 更新
    env_no_update = os.getenv("NO_UPDATE", "").lower() == "true"
    if not env_no_update:
        # 使用多线程在后台执行 git 更新检查（询问是否 pull，pull 后重新运行）
        git_thread = threading.Thread(
            target=check_git_update, args=(True, True), daemon=True
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
    """检查更新和清理日志"""
    # 清理日志
    cleanup_logs()

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
