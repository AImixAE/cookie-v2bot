import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from datetime import datetime, timedelta
from src.database import Database
from src.core import midnight_range_for_yesterday

console = Console()
db = Database("data/chat.db")


def format_username(user):
    """格式化用户名"""
    username = user.get("username", "")
    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")
    name_parts = [p for p in [first_name, last_name] if p]
    full_name = " ".join(name_parts) if name_parts else ""
    if username and full_name:
        return f"{username} ({full_name})"
    elif username:
        return username
    elif full_name:
        return full_name
    else:
        return f"用户{user.get('user_id', '未知')}"


@click.group()
def cli():
    """Cookie Bot 管理工具"""
    pass


@cli.command()
def list_groups():
    """列出所有群组"""
    console.print("[bold cyan]=== 群组列表 ===[/bold cyan]")

    # 获取所有群组信息
    groups = db.get_chats_info()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("群组ID", style="dim")
    table.add_column("群组名称")
    table.add_column("消息数量")
    table.add_column("最后活动时间")
    table.add_column("经验总和")

    for group in groups:
        chat_id = group[0]
        msg_count = group[1]
        last_ts = group[2]
        title = group[3] or "未知群组"
        exp_total = group[4] or 0

        # 格式化最后活动时间
        last_time = (
            datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d %H:%M:%S")
            if last_ts
            else "未知"
        )

        table.add_row(str(chat_id), title, str(msg_count), last_time, str(exp_total))

    console.print(table)


@cli.command()
def list_users():
    """列出所有用户"""
    console.print("[bold cyan]=== 用户列表 ===[/bold cyan]")

    # 获取所有用户
    users = db.get_all_users()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("用户ID", style="dim")
    table.add_column("用户名")
    table.add_column("经验总和")
    table.add_column("等级")

    for user in users:
        user_id = user[0]
        username = user[1]
        first_name = user[2]
        last_name = user[3]
        total_exp = user[4]
        level = user[5] if len(user) > 5 else 1

        # 格式化用户名
        formatted_name = format_username(
            {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": user_id,
            }
        )

        table.add_row(str(user_id), formatted_name, str(total_exp), str(level))

    console.print(table)


@cli.command()
@click.argument("user_id", type=int)
def user_detail(user_id):
    """查看用户详细信息"""
    console.print(f"[bold cyan]=== 用户 {user_id} 详细信息 ===[/bold cyan]")

    # 获取用户信息
    user = db.get_user_by_id(user_id)
    if not user:
        console.print(f"[bold red]未找到用户 ID: {user_id}[/bold red]")
        return

    # 格式化用户名
    formatted_name = format_username(
        {
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "user_id": user[0],
        }
    )

    # 显示基本信息
    console.print(f"[bold green]用户:[/bold green] {formatted_name}")
    console.print(f"[bold green]用户ID:[/bold green] {user[0]}")
    console.print(f"[bold green]经验总和:[/bold green] {user[4]}")
    level = user[5] if len(user) > 5 else 1
    console.print(f"[bold green]等级:[/bold green] {level}")

    # 计算时间范围
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_ts = int(today_start.timestamp())
    yesterday_start, yesterday_end = midnight_range_for_yesterday()

    # 获取用户的消息统计
    yesterday_counts = db.get_user_counts(
        user_id, start_ts=yesterday_start, end_ts=yesterday_end
    )
    today_counts = db.get_user_counts(user_id, start_ts=today_ts, end_ts=None)
    total_counts = db.get_user_counts(user_id, start_ts=None, end_ts=None)

    # 显示消息统计
    console.print("\n[bold green]消息统计:[/bold green]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("消息类型")
    table.add_column("昨日数量")
    table.add_column("今日数量")
    table.add_column("累计数量")

    # 获取所有消息类型
    msg_types = set()
    msg_types.update(yesterday_counts.keys())
    msg_types.update(today_counts.keys())
    msg_types.update(total_counts.keys())
    msg_types.discard("total")  # 移除总计，单独处理

    # 添加每种消息类型的统计
    for msg_type in msg_types:
        yesterday = yesterday_counts.get(msg_type, 0)
        today = today_counts.get(msg_type, 0)
        total = total_counts.get(msg_type, 0)
        table.add_row(msg_type, str(yesterday), str(today), str(total))

    # 添加总计
    yesterday_total = yesterday_counts.get("total", 0)
    today_total = today_counts.get("total", 0)
    total_total = total_counts.get("total", 0)
    table.add_row("总计", str(yesterday_total), str(today_total), str(total_total))

    console.print(table)


@cli.command()
@click.argument("chat_id", type=str)
@click.option(
    "--sort", "sort_by", default="exp", help="排序方式: exp (经验值) 或 msg (消息数)"
)
@click.option(
    "--limit", "limit", default=10, type=int, help="排行榜最大显示数量 (默认: 10)"
)
def leaderboard(chat_id, sort_by, limit):
    """查看群组排行榜"""
    try:
        chat_id_int = int(chat_id)
    except ValueError:
        console.print(f"[bold red]无效的chat_id: {chat_id}[/bold red]")
        return
    console.print(f"[bold cyan]=== 群组 {chat_id_int} 排行榜 ===[/bold cyan]")

    # 计算时间范围
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_ts = int(today_start.timestamp())
    yesterday_start, yesterday_end = midnight_range_for_yesterday()

    # 获取排行榜数据
    yesterday_leaderboard = db.get_leaderboard_with_names(
        chat_id_int,
        start_ts=yesterday_start,
        end_ts=yesterday_end,
        limit=limit if limit > 0 else None,
        sort_by=sort_by,
    )
    today_leaderboard = db.get_leaderboard_with_names(
        chat_id_int, start_ts=today_ts, end_ts=None, limit=limit if limit > 0 else None, sort_by=sort_by
    )
    all_leaderboard = db.get_leaderboard_with_names(
        chat_id_int, start_ts=None, end_ts=None, limit=limit if limit > 0 else None, sort_by=sort_by
    )

    # 显示昨日排行榜
    console.print("\n[bold green]昨日排行榜:[/bold green]")
    table_yesterday = Table(show_header=True, header_style="bold magenta")
    table_yesterday.add_column("排名", style="dim")
    table_yesterday.add_column("用户名")
    table_yesterday.add_column("消息数")
    table_yesterday.add_column("经验值")

    for i, user in enumerate(yesterday_leaderboard, 1):
        username = user[1]
        first_name = user[2]
        last_name = user[3]
        exp = user[4]
        msg_count = user[5]

        formatted_name = format_username(
            {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": user[0],
            }
        )
        table_yesterday.add_row(str(i), formatted_name, str(msg_count), str(exp))

    console.print(table_yesterday)

    # 显示今日排行榜
    console.print("\n[bold green]今日排行榜:[/bold green]")
    table_today = Table(show_header=True, header_style="bold magenta")
    table_today.add_column("排名", style="dim")
    table_today.add_column("用户名")
    table_today.add_column("消息数")
    table_today.add_column("经验值")

    for i, user in enumerate(today_leaderboard, 1):
        username = user[1]
        first_name = user[2]
        last_name = user[3]
        exp = user[4]
        msg_count = user[5]

        formatted_name = format_username(
            {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": user[0],
            }
        )
        table_today.add_row(str(i), formatted_name, str(msg_count), str(exp))

    console.print(table_today)

    # 显示全部排行榜
    console.print("\n[bold green]全部排行榜:[/bold green]")
    table_all = Table(show_header=True, header_style="bold magenta")
    table_all.add_column("排名", style="dim")
    table_all.add_column("用户名")
    table_all.add_column("消息数")
    table_all.add_column("经验值")

    for i, user in enumerate(all_leaderboard, 1):
        username = user[1]
        first_name = user[2]
        last_name = user[3]
        exp = user[4]
        msg_count = user[5]

        formatted_name = format_username(
            {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "user_id": user[0],
            }
        )
        table_all.add_row(str(i), formatted_name, str(msg_count), str(exp))

    console.print(table_all)


@cli.command()
@click.argument("user_id", type=int)
@click.option("--add", type=int, help="增加经验值")
@click.option("--remove", type=int, help="减少经验值")
@click.option("--set", type=int, help="设置经验值")
@click.option("--delete", is_flag=True, help="删除用户")
def user_operation(user_id, add, remove, set, delete):
    """用户操作"""
    console.print(f"[bold cyan]=== 用户 {user_id} 操作 ===[/bold cyan]")

    # 检查用户是否存在
    user = db.get_user_by_id(user_id)
    if not user:
        console.print(f"[bold red]未找到用户 ID: {user_id}[/bold red]")
        return

    # 显示当前用户信息
    formatted_name = format_username(
        {
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "user_id": user[0],
        }
    )
    console.print(f"[bold green]当前用户:[/bold green] {formatted_name}")
    console.print(f"[bold green]当前经验值:[/bold green] {user[4]}")
    level = user[5] if len(user) > 5 else 1
    console.print(f"[bold green]当前等级:[/bold green] {level}")

    # 执行操作
    if delete:
        # 询问用户确认
        if not Confirm.ask("确定要删除该用户吗？此操作不可恢复！"):
            console.print("[bold yellow]操作已取消[/bold yellow]")
            return

        # 删除用户
        db.delete_user(user_id)
        console.print(f"[bold green]用户 {user_id} 已删除[/bold green]")
    elif add is not None:
        # 增加经验值
        db.add_user_exp(user_id, add)
        new_exp = user[4] + add
        console.print(
            f"[bold green]已为用户增加 {add} 经验值，当前经验值: {new_exp}[/bold green]"
        )
    elif remove is not None:
        # 减少经验值
        db.add_user_exp(user_id, -remove)
        new_exp = user[4] - remove
        console.print(
            f"[bold green]已为用户减少 {remove} 经验值，当前经验值: {new_exp}[/bold green]"
        )
    elif set is not None:
        # 设置经验值
        db.set_user_exp(user_id, set)
        console.print(f"[bold green]已将用户经验值设置为: {set}[/bold green]")
    else:
        console.print("[bold yellow]请指定操作类型，使用 --help 查看帮助[/bold yellow]")


@cli.command()
def clear_database():
    """清空数据库"""
    console.print("[bold red]=== 警告：清空数据库 ===[/bold red]")
    console.print("此操作将清空整个数据库并重新初始化，所有数据将被删除！")
    console.print("请谨慎操作！")

    # 询问用户3次
    for i in range(3):
        if not Confirm.ask(f"确认要清空数据库吗？({i+1}/3)"):
            console.print("[bold yellow]操作已取消[/bold yellow]")
            return

    # 清空数据库
    try:
        db.clear_database()
        console.print("[bold green]数据库已成功清空并重新初始化[/bold green]")
    except Exception as e:
        console.print(f"[bold red]清空数据库失败: {e}[/bold red]")


if __name__ == "__main__":
    cli()
