#!/usr/bin/env python3
"""Cookie Bot 图形界面"""

import sys
import os
import csv
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QGroupBox,
    QGridLayout,
    QSpinBox,
    QMessageBox,
    QHeaderView,
    QMenu,
    QDialog,
    QFormLayout,
    QTextEdit,
    QDateEdit,
    QStyleFactory,
    QFileDialog,
)
from PySide6.QtGui import QAction, QPalette, QColor, QFont
from PySide6.QtCore import Qt, QDate
from src.database import Database
from src.core import midnight_range_for_yesterday, format_file_size


def setup_dark_theme(app):
    """设置深色主题"""
    # 设置融合样式
    app.setStyle(QStyleFactory.create("Fusion"))

    # 创建深色调色板
    palette = QPalette()

    # 基础颜色 - 稍微调亮背景以提高可读性
    palette.setColor(QPalette.Window, QColor(60, 60, 60))  # 稍微调亮背景
    palette.setColor(
        QPalette.WindowText, QColor(220, 220, 220)
    )  # 稍微调暗文本，避免过于刺眼
    palette.setColor(QPalette.Base, QColor(40, 40, 40))  # 稍微调亮基础背景
    palette.setColor(QPalette.AlternateBase, QColor(60, 60, 60))  # 稍微调亮交替背景
    palette.setColor(QPalette.ToolTipBase, QColor(220, 220, 220))
    palette.setColor(QPalette.ToolTipText, QColor(30, 30, 30))  # 提示文本使用深色
    palette.setColor(QPalette.Text, QColor(220, 220, 220))  # 稍微调暗文本

    # 按钮颜色 - 调整按钮和按钮文本颜色
    palette.setColor(QPalette.Button, QColor(70, 70, 70))  # 调亮按钮背景
    palette.setColor(QPalette.ButtonText, QColor(220, 220, 220))  # 调暗按钮文本

    # 其他颜色
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(30, 30, 30))  # 高亮文本使用深色

    app.setPalette(palette)


class CookieBotGUI(QMainWindow):
    """Cookie Bot 图形界面类"""

    def __init__(self):
        super().__init__()
        self.db = Database("data/chat.db")
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("Cookie Bot 管理工具")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QVBoxLayout(central_widget)

        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # 创建各个标签页
        self.create_groups_tab()
        self.create_users_tab()
        self.create_user_detail_tab()
        self.create_leaderboard_tab()
        self.create_user_operation_tab()
        self.create_batch_operation_tab()
        self.create_database_detail_tab()
        self.create_log_operation_tab()

    def create_groups_tab(self):
        """创建群组标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("群组列表")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)  # 减少底部边距
        layout.addWidget(title_label)

        # 创建刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_groups_table)
        layout.addWidget(refresh_button)

        # 创建表格
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(6)
        self.groups_table.setHorizontalHeaderLabels(
            ["群组ID", "群组名称", "消息数量", "最后活动时间", "经验总和", "操作"]
        )
        # 设置列宽
        for i in range(5):
            self.groups_table.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.Stretch
            )
        self.groups_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.groups_table.setColumnWidth(5, 100)
        layout.addWidget(self.groups_table)

        # 创建计数标签
        self.groups_count_label = QLabel("共 0 个群组")
        self.groups_count_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.groups_count_label)

        # 填充表格
        self.refresh_groups_table()

        self.tab_widget.addTab(tab, "群组")

    def refresh_groups_table(self):
        """刷新群组表格"""
        # 清空表格
        self.groups_table.setRowCount(0)

        # 获取所有群组信息
        groups = self.db.get_chats_info()

        # 填充表格
        for group in groups:
            chat_id = group[0]
            msg_count = group[1]
            last_ts = group[2]
            title = group[3] or "未知群组"

            # 计算该群组所有用户的经验总和
            exp_total = 0

            # 格式化最后活动时间
            last_time = (
                datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d %H:%M:%S")
                if last_ts
                else "未知"
            )

            # 添加行
            row_position = self.groups_table.rowCount()
            self.groups_table.insertRow(row_position)

            # 添加数据
            self.groups_table.setItem(row_position, 0, QTableWidgetItem(str(chat_id)))
            self.groups_table.setItem(row_position, 1, QTableWidgetItem(title))
            self.groups_table.setItem(row_position, 2, QTableWidgetItem(str(msg_count)))
            self.groups_table.setItem(row_position, 3, QTableWidgetItem(last_time))
            self.groups_table.setItem(row_position, 4, QTableWidgetItem(str(exp_total)))

            # 添加查看排行榜按钮
            view_leaderboard_button = QPushButton("查看排行榜")
            view_leaderboard_button.setFixedWidth(90)
            view_leaderboard_button.clicked.connect(
                lambda checked, cid=chat_id: self.view_group_leaderboard(cid)
            )
            self.groups_table.setCellWidget(row_position, 5, view_leaderboard_button)

        # 更新计数标签
        self.groups_count_label.setText(f"共 {len(groups)} 个群组")

    def create_users_tab(self):
        """创建用户标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("用户列表")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)  # 减少底部边距
        layout.addWidget(title_label)

        # 创建搜索和刷新按钮
        search_layout = QHBoxLayout()
        self.user_search_input = QLineEdit()
        self.user_search_input.setPlaceholderText("搜索用户名或ID")
        search_button = QPushButton("搜索")
        search_button.clicked.connect(self.search_users)
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_users_table)

        search_layout.addWidget(self.user_search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(refresh_button)
        layout.addLayout(search_layout)

        # 创建表格
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(
            ["用户ID", "用户名", "经验总和", "等级", "操作"]
        )
        # 设置列宽
        # 为用户ID设置固定宽度
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.users_table.setColumnWidth(0, 120)  # 设置用户ID列宽度为120像素

        # 让用户名自动拉伸
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # 为经验总和设置固定宽度
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.users_table.setColumnWidth(2, 100)  # 设置经验总和列宽度为100像素

        # 为等级设置固定宽度
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.users_table.setColumnWidth(3, 80)  # 调整等级列宽度为80像素

        # 为操作设置固定宽度
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.users_table.setColumnWidth(4, 160)  # 设置操作列宽度为160像素
        layout.addWidget(self.users_table)

        # 创建计数标签
        self.users_count_label = QLabel("共 0 个用户")
        self.users_count_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.users_count_label)

        # 填充表格
        self.refresh_users_table()

        self.tab_widget.addTab(tab, "用户")

    def refresh_users_table(self):
        """刷新用户表格"""
        # 清空表格
        self.users_table.setRowCount(0)

        # 获取所有用户
        users = self.db.get_all_users()

        # 填充表格
        for user in users:
            user_id = user[0]
            username = user[1]
            first_name = user[2]
            last_name = user[3]
            total_exp = user[4]
            level = user[5] if len(user) > 5 else 1

            # 格式化用户名
            name_parts = [p for p in [first_name, last_name] if p]
            full_name = " ".join(name_parts) if name_parts else ""
            if username and full_name:
                display_name = f"{username} ({full_name})"
            elif username:
                display_name = username
            elif full_name:
                display_name = full_name
            else:
                display_name = f"用户{user_id}"

            # 添加行
            row_position = self.users_table.rowCount()
            self.users_table.insertRow(row_position)

            # 添加数据
            self.users_table.setItem(row_position, 0, QTableWidgetItem(str(user_id)))
            self.users_table.setItem(row_position, 1, QTableWidgetItem(display_name))
            self.users_table.setItem(row_position, 2, QTableWidgetItem(str(total_exp)))
            self.users_table.setItem(row_position, 3, QTableWidgetItem(str(level)))

            # 添加操作按钮
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(0, 0, 0, 0)

            # 查看详细按钮
            view_detail_button = QPushButton("查看详细")
            view_detail_button.setFixedWidth(70)
            view_detail_button.clicked.connect(
                lambda checked, uid=user_id: self.view_user_detail(uid)
            )
            button_layout.addWidget(view_detail_button)

            # 用户操作按钮
            user_operation_button = QPushButton("操作")
            user_operation_button.setFixedWidth(70)
            user_operation_button.clicked.connect(
                lambda checked, uid=user_id: self.view_user_operation(uid)
            )
            button_layout.addWidget(user_operation_button)

            self.users_table.setCellWidget(row_position, 4, button_widget)

        # 更新计数标签
        self.users_count_label.setText(f"共 {len(users)} 个用户")

    def search_users(self):
        """搜索用户"""
        search_text = self.user_search_input.text().lower()
        if not search_text:
            self.refresh_users_table()
            return

        # 清空表格
        self.users_table.setRowCount(0)

        # 获取所有用户
        users = self.db.get_all_users()

        # 过滤用户
        filtered_users = []
        for user in users:
            user_id = user[0]
            username = user[1] or ""
            first_name = user[2] or ""
            last_name = user[3] or ""

            # 检查是否匹配
            if (
                search_text in str(user_id)
                or search_text in username.lower()
                or search_text in first_name.lower()
                or search_text in last_name.lower()
            ):
                filtered_users.append(user)

        # 填充表格
        for user in filtered_users:
            user_id = user[0]
            username = user[1]
            first_name = user[2]
            last_name = user[3]
            total_exp = user[4]
            level = user[5] if len(user) > 5 else 1

            # 格式化用户名
            name_parts = [p for p in [first_name, last_name] if p]
            full_name = " ".join(name_parts) if name_parts else ""
            if username and full_name:
                display_name = f"{username} ({full_name})"
            elif username:
                display_name = username
            elif full_name:
                display_name = full_name
            else:
                display_name = f"用户{user_id}"

            # 添加行
            row_position = self.users_table.rowCount()
            self.users_table.insertRow(row_position)

            # 添加数据
            self.users_table.setItem(row_position, 0, QTableWidgetItem(str(user_id)))
            self.users_table.setItem(row_position, 1, QTableWidgetItem(display_name))
            self.users_table.setItem(row_position, 2, QTableWidgetItem(str(total_exp)))
            self.users_table.setItem(row_position, 3, QTableWidgetItem(str(level)))

        # 更新计数标签
        self.users_count_label.setText(f"共 {len(filtered_users)} 个用户")

    def create_user_detail_tab(self):
        """创建用户详细信息标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("用户详细信息")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)  # 减少底部边距
        layout.addWidget(title_label)

        # 创建用户ID输入和查询按钮
        input_layout = QHBoxLayout()
        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("输入用户ID")
        query_button = QPushButton("查询")
        query_button.clicked.connect(self.query_user_detail)

        input_layout.addWidget(self.user_id_input)
        input_layout.addWidget(query_button)
        layout.addLayout(input_layout)

        # 创建用户信息组
        self.user_info_group = QGroupBox("用户信息")
        self.user_info_layout = QGridLayout()
        self.user_info_group.setLayout(self.user_info_layout)
        layout.addWidget(self.user_info_group)

        # 创建消息统计组
        self.message_stats_group = QGroupBox("消息统计")
        message_stats_layout = QVBoxLayout()

        # 创建消息统计表格
        self.message_stats_table = QTableWidget()
        self.message_stats_table.setColumnCount(4)
        self.message_stats_table.setHorizontalHeaderLabels(
            ["消息类型", "昨日数量", "今日数量", "累计数量"]
        )
        self.message_stats_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        message_stats_layout.addWidget(self.message_stats_table)

        self.message_stats_group.setLayout(message_stats_layout)
        layout.addWidget(self.message_stats_group)

        # 初始化用户信息
        self.init_user_info()

        self.tab_widget.addTab(tab, "用户详细")

    def init_user_info(self):
        """初始化用户信息"""
        # 清空用户信息布局
        for i in reversed(range(self.user_info_layout.count())):
            widget = self.user_info_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 添加默认提示
        self.user_info_layout.addWidget(QLabel("请输入用户ID并点击查询"), 0, 0, 1, 2)

        # 清空消息统计表格
        self.message_stats_table.setRowCount(0)

    def view_user_detail(self, user_id):
        """查看指定用户的详细信息"""
        # 切换到用户详细标签页
        self.tab_widget.setCurrentIndex(2)  # 假设用户详细是第3个标签页（索引2）
        # 填入用户ID
        self.user_id_input.setText(str(user_id))
        # 执行查询
        self.query_user_detail()

    def view_user_operation(self, user_id):
        """查看指定用户的操作界面"""
        # 切换到用户操作标签页
        self.tab_widget.setCurrentIndex(4)  # 假设用户操作是第5个标签页（索引4）
        # 填入用户ID
        self.operation_user_id_input.setText(str(user_id))
        # 执行查询
        self.query_user_for_operation()

    def query_user_detail(self):
        """查询用户详细信息"""
        # 获取用户ID
        user_id_text = self.user_id_input.text()
        if not user_id_text.isdigit():
            QMessageBox.warning(self, "警告", "请输入有效的用户ID")
            return

        user_id = int(user_id_text)

        # 获取用户信息
        user = self.db.get_user_by_id(user_id)
        if not user:
            QMessageBox.warning(self, "警告", f"未找到用户 ID: {user_id}")
            return

        # 清空用户信息布局
        for i in reversed(range(self.user_info_layout.count())):
            widget = self.user_info_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 格式化用户名
        username = user[1]
        first_name = user[2]
        last_name = user[3]
        name_parts = [p for p in [first_name, last_name] if p]
        full_name = " ".join(name_parts) if name_parts else ""
        if username and full_name:
            display_name = f"{username} ({full_name})"
        elif username:
            display_name = username
        elif full_name:
            display_name = full_name
        else:
            display_name = f"用户{user_id}"

        # 添加用户信息
        self.user_info_layout.addWidget(QLabel("用户名:"), 0, 0)
        self.user_info_layout.addWidget(QLabel(display_name), 0, 1)
        self.user_info_layout.addWidget(QLabel("用户ID:"), 1, 0)
        self.user_info_layout.addWidget(QLabel(str(user[0])), 1, 1)
        self.user_info_layout.addWidget(QLabel("经验总和:"), 2, 0)
        self.user_info_layout.addWidget(QLabel(str(user[4])), 2, 1)
        level = user[5] if len(user) > 5 else 1
        self.user_info_layout.addWidget(QLabel("等级:"), 3, 0)
        self.user_info_layout.addWidget(QLabel(str(level)), 3, 1)

        # 计算时间范围
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_ts = int(today_start.timestamp())
        yesterday_start, yesterday_end = midnight_range_for_yesterday()

        # 获取用户的消息统计
        yesterday_counts = self.db.get_user_counts(
            user_id, start_ts=yesterday_start, end_ts=yesterday_end
        )
        today_counts = self.db.get_user_counts(user_id, start_ts=today_ts, end_ts=None)
        total_counts = self.db.get_user_counts(user_id, start_ts=None, end_ts=None)

        # 清空消息统计表格
        self.message_stats_table.setRowCount(0)

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

            # 添加行
            row_position = self.message_stats_table.rowCount()
            self.message_stats_table.insertRow(row_position)

            # 添加数据
            self.message_stats_table.setItem(
                row_position, 0, QTableWidgetItem(msg_type)
            )
            self.message_stats_table.setItem(
                row_position, 1, QTableWidgetItem(str(yesterday))
            )
            self.message_stats_table.setItem(
                row_position, 2, QTableWidgetItem(str(today))
            )
            self.message_stats_table.setItem(
                row_position, 3, QTableWidgetItem(str(total))
            )

        # 添加总计
        yesterday_total = yesterday_counts.get("total", 0)
        today_total = today_counts.get("total", 0)
        total_total = total_counts.get("total", 0)

        # 添加行
        row_position = self.message_stats_table.rowCount()
        self.message_stats_table.insertRow(row_position)

        # 添加数据
        self.message_stats_table.setItem(row_position, 0, QTableWidgetItem("总计"))
        self.message_stats_table.setItem(
            row_position, 1, QTableWidgetItem(str(yesterday_total))
        )
        self.message_stats_table.setItem(
            row_position, 2, QTableWidgetItem(str(today_total))
        )
        self.message_stats_table.setItem(
            row_position, 3, QTableWidgetItem(str(total_total))
        )

    def create_leaderboard_tab(self):
        """创建排行榜标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("群组排行榜")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)  # 减少底部边距
        layout.addWidget(title_label)

        # 创建群组ID输入和查询按钮
        input_layout = QHBoxLayout()
        self.chat_id_input = QLineEdit()
        self.chat_id_input.setPlaceholderText("输入群组ID")
        query_button = QPushButton("查询")
        query_button.clicked.connect(self.query_leaderboard)

        input_layout.addWidget(self.chat_id_input)
        input_layout.addWidget(query_button)
        layout.addLayout(input_layout)

        # 创建排行榜标签页
        self.leaderboard_tabs = QTabWidget()

        # 创建昨日排行榜
        self.yesterday_leaderboard_tab = QWidget()
        yesterday_layout = QVBoxLayout(self.yesterday_leaderboard_tab)
        self.yesterday_leaderboard_table = QTableWidget()
        self.yesterday_leaderboard_table.setColumnCount(4)
        self.yesterday_leaderboard_table.setHorizontalHeaderLabels(
            ["排名", "用户名", "消息数", "经验值"]
        )
        self.yesterday_leaderboard_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        yesterday_layout.addWidget(self.yesterday_leaderboard_table)
        self.leaderboard_tabs.addTab(self.yesterday_leaderboard_tab, "昨日")

        # 创建今日排行榜
        self.today_leaderboard_tab = QWidget()
        today_layout = QVBoxLayout(self.today_leaderboard_tab)
        self.today_leaderboard_table = QTableWidget()
        self.today_leaderboard_table.setColumnCount(4)
        self.today_leaderboard_table.setHorizontalHeaderLabels(
            ["排名", "用户名", "消息数", "经验值"]
        )
        self.today_leaderboard_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        today_layout.addWidget(self.today_leaderboard_table)
        self.leaderboard_tabs.addTab(self.today_leaderboard_tab, "今日")

        # 创建全部排行榜
        self.all_leaderboard_tab = QWidget()
        all_layout = QVBoxLayout(self.all_leaderboard_tab)
        self.all_leaderboard_table = QTableWidget()
        self.all_leaderboard_table.setColumnCount(4)
        self.all_leaderboard_table.setHorizontalHeaderLabels(
            ["排名", "用户名", "消息数", "经验值"]
        )
        self.all_leaderboard_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        all_layout.addWidget(self.all_leaderboard_table)
        self.leaderboard_tabs.addTab(self.all_leaderboard_tab, "全部")

        # 初始化排行榜
        self.init_leaderboard()

        # 添加排行榜标签页到布局
        layout.addWidget(self.leaderboard_tabs)

        self.tab_widget.addTab(tab, "排行榜")

    def init_leaderboard(self):
        """初始化排行榜"""
        # 清空排行榜表格
        self.yesterday_leaderboard_table.setRowCount(0)
        self.today_leaderboard_table.setRowCount(0)
        self.all_leaderboard_table.setRowCount(0)

    def view_group_leaderboard(self, chat_id):
        """查看指定群组的排行榜"""
        # 切换到排行榜标签页
        self.tab_widget.setCurrentIndex(3)  # 假设排行榜是第4个标签页（索引3）
        # 填入群组ID
        self.chat_id_input.setText(str(chat_id))
        # 执行查询
        self.query_leaderboard()

    def query_leaderboard(self):
        """查询排行榜"""
        # 获取群组ID
        chat_id_text = self.chat_id_input.text()
        if not (chat_id_text.isdigit() or chat_id_text.startswith("-")):
            QMessageBox.warning(self, "警告", "请输入有效的群组ID")
            return

        chat_id = int(chat_id_text)

        # 计算时间范围
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_ts = int(today_start.timestamp())
        yesterday_start, yesterday_end = midnight_range_for_yesterday()

        # 获取排行榜数据
        yesterday_leaderboard = self.db.get_leaderboard_with_names(
            chat_id, start_ts=yesterday_start, end_ts=yesterday_end, limit=10
        )
        today_leaderboard = self.db.get_leaderboard_with_names(
            chat_id, start_ts=today_ts, end_ts=None, limit=10
        )
        all_leaderboard = self.db.get_leaderboard_with_names(
            chat_id, start_ts=None, end_ts=None, limit=10
        )

        # 填充昨日排行榜
        self.yesterday_leaderboard_table.setRowCount(0)
        for i, user in enumerate(yesterday_leaderboard, 1):
            username = user[1]
            first_name = user[2]
            last_name = user[3]
            exp = user[4]
            msg_count = user[5]

            # 格式化用户名
            name_parts = [p for p in [first_name, last_name] if p]
            full_name = " ".join(name_parts) if name_parts else ""
            if username and full_name:
                display_name = f"{username} ({full_name})"
            elif username:
                display_name = username
            elif full_name:
                display_name = full_name
            else:
                display_name = f"用户{user[0]}"

            # 添加行
            row_position = self.yesterday_leaderboard_table.rowCount()
            self.yesterday_leaderboard_table.insertRow(row_position)

            # 添加数据
            self.yesterday_leaderboard_table.setItem(
                row_position, 0, QTableWidgetItem(str(i))
            )
            self.yesterday_leaderboard_table.setItem(
                row_position, 1, QTableWidgetItem(display_name)
            )
            self.yesterday_leaderboard_table.setItem(
                row_position, 2, QTableWidgetItem(str(msg_count))
            )
            self.yesterday_leaderboard_table.setItem(
                row_position, 3, QTableWidgetItem(str(exp))
            )

        # 填充今日排行榜
        self.today_leaderboard_table.setRowCount(0)
        for i, user in enumerate(today_leaderboard, 1):
            username = user[1]
            first_name = user[2]
            last_name = user[3]
            exp = user[4]
            msg_count = user[5]

            # 格式化用户名
            name_parts = [p for p in [first_name, last_name] if p]
            full_name = " ".join(name_parts) if name_parts else ""
            if username and full_name:
                display_name = f"{username} ({full_name})"
            elif username:
                display_name = username
            elif full_name:
                display_name = full_name
            else:
                display_name = f"用户{user[0]}"

            # 添加行
            row_position = self.today_leaderboard_table.rowCount()
            self.today_leaderboard_table.insertRow(row_position)

            # 添加数据
            self.today_leaderboard_table.setItem(
                row_position, 0, QTableWidgetItem(str(i))
            )
            self.today_leaderboard_table.setItem(
                row_position, 1, QTableWidgetItem(display_name)
            )
            self.today_leaderboard_table.setItem(
                row_position, 2, QTableWidgetItem(str(msg_count))
            )
            self.today_leaderboard_table.setItem(
                row_position, 3, QTableWidgetItem(str(exp))
            )

        # 填充全部排行榜
        self.all_leaderboard_table.setRowCount(0)
        for i, user in enumerate(all_leaderboard, 1):
            username = user[1]
            first_name = user[2]
            last_name = user[3]
            exp = user[4]
            msg_count = user[5]

            # 格式化用户名
            name_parts = [p for p in [first_name, last_name] if p]
            full_name = " ".join(name_parts) if name_parts else ""
            if username and full_name:
                display_name = f"{username} ({full_name})"
            elif username:
                display_name = username
            elif full_name:
                display_name = full_name
            else:
                display_name = f"用户{user[0]}"

            # 添加行
            row_position = self.all_leaderboard_table.rowCount()
            self.all_leaderboard_table.insertRow(row_position)

            # 添加数据
            self.all_leaderboard_table.setItem(
                row_position, 0, QTableWidgetItem(str(i))
            )
            self.all_leaderboard_table.setItem(
                row_position, 1, QTableWidgetItem(display_name)
            )
            self.all_leaderboard_table.setItem(
                row_position, 2, QTableWidgetItem(str(msg_count))
            )
            self.all_leaderboard_table.setItem(
                row_position, 3, QTableWidgetItem(str(exp))
            )

    def create_user_operation_tab(self):
        """创建用户操作标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("用户操作")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)  # 与其他界面一致的边距
        layout.addWidget(title_label)

        # 创建用户ID输入和查询按钮
        input_layout = QHBoxLayout()
        self.operation_user_id_input = QLineEdit()
        self.operation_user_id_input.setPlaceholderText("输入用户ID")
        query_button = QPushButton("查询")
        query_button.clicked.connect(self.query_user_for_operation)

        input_layout.addWidget(self.operation_user_id_input)
        input_layout.addWidget(query_button)
        layout.addLayout(input_layout)

        # 创建用户信息组
        self.operation_user_info_group = QGroupBox("用户信息")
        self.operation_user_info_layout = QGridLayout()
        self.operation_user_info_group.setLayout(self.operation_user_info_layout)
        layout.addWidget(self.operation_user_info_group)

        # 创建操作组
        operation_group = QGroupBox("操作")
        operation_layout = QGridLayout()

        # 添加经验值操作
        operation_layout.addWidget(QLabel("经验值操作:"), 0, 0, 1, 2)

        # 增加经验值
        operation_layout.addWidget(QLabel("增加:"), 1, 0)
        self.add_exp_spinbox = QSpinBox()
        self.add_exp_spinbox.setMinimum(1)
        self.add_exp_spinbox.setMaximum(1000000)
        operation_layout.addWidget(self.add_exp_spinbox, 1, 1)

        add_exp_button = QPushButton("执行增加")
        add_exp_button.clicked.connect(self.add_exp)
        operation_layout.addWidget(add_exp_button, 1, 2)

        # 减少经验值
        operation_layout.addWidget(QLabel("减少:"), 2, 0)
        self.remove_exp_spinbox = QSpinBox()
        self.remove_exp_spinbox.setMinimum(1)
        self.remove_exp_spinbox.setMaximum(1000000)
        operation_layout.addWidget(self.remove_exp_spinbox, 2, 1)

        remove_exp_button = QPushButton("执行减少")
        remove_exp_button.clicked.connect(self.remove_exp)
        operation_layout.addWidget(remove_exp_button, 2, 2)

        # 设置经验值
        operation_layout.addWidget(QLabel("设置:"), 3, 0)
        self.set_exp_spinbox = QSpinBox()
        self.set_exp_spinbox.setMinimum(0)
        self.set_exp_spinbox.setMaximum(1000000)
        operation_layout.addWidget(self.set_exp_spinbox, 3, 1)

        set_exp_button = QPushButton("执行设置")
        set_exp_button.clicked.connect(self.set_exp)
        operation_layout.addWidget(set_exp_button, 3, 2)

        # 删除用户
        delete_user_button = QPushButton("删除用户")
        delete_user_button.setStyleSheet("background-color: #ff6b6b; color: white;")
        delete_user_button.clicked.connect(self.delete_user)
        operation_layout.addWidget(delete_user_button, 4, 0, 1, 3)

        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)

        # 初始化用户信息
        self.init_operation_user_info()

        self.tab_widget.addTab(tab, "用户操作")

    def init_operation_user_info(self):
        """初始化用户操作信息"""
        # 清空用户信息布局
        for i in reversed(range(self.operation_user_info_layout.count())):
            widget = self.operation_user_info_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 添加默认提示
        self.operation_user_info_layout.addWidget(
            QLabel("请输入用户ID并点击查询"), 0, 0, 1, 2
        )

        # 保存当前用户信息
        self.current_operation_user = None

    def query_user_for_operation(self):
        """查询用户操作信息"""
        # 获取用户ID
        user_id_text = self.operation_user_id_input.text()
        if not user_id_text.isdigit():
            QMessageBox.warning(self, "警告", "请输入有效的用户ID")
            return

        user_id = int(user_id_text)

        # 获取用户信息
        user = self.db.get_user_by_id(user_id)
        if not user:
            QMessageBox.warning(self, "警告", f"未找到用户 ID: {user_id}")
            return

        # 保存当前用户信息
        self.current_operation_user = user

        # 清空用户信息布局
        for i in reversed(range(self.operation_user_info_layout.count())):
            widget = self.operation_user_info_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 格式化用户名
        username = user[1]
        first_name = user[2]
        last_name = user[3]
        name_parts = [p for p in [first_name, last_name] if p]
        full_name = " ".join(name_parts) if name_parts else ""
        if username and full_name:
            display_name = f"{username} ({full_name})"
        elif username:
            display_name = username
        elif full_name:
            display_name = full_name
        else:
            display_name = f"用户{user_id}"

        # 添加用户信息
        self.operation_user_info_layout.addWidget(QLabel("用户名:"), 0, 0)
        self.operation_user_info_layout.addWidget(QLabel(display_name), 0, 1)
        self.operation_user_info_layout.addWidget(QLabel("用户ID:"), 1, 0)
        self.operation_user_info_layout.addWidget(QLabel(str(user[0])), 1, 1)
        self.operation_user_info_layout.addWidget(QLabel("当前经验值:"), 2, 0)
        self.operation_user_info_layout.addWidget(QLabel(str(user[4])), 2, 1)
        level = user[5] if len(user) > 5 else 1
        self.operation_user_info_layout.addWidget(QLabel("当前等级:"), 3, 0)
        self.operation_user_info_layout.addWidget(QLabel(str(level)), 3, 1)

    def add_exp(self):
        """增加经验值"""
        if not self.current_operation_user:
            QMessageBox.warning(self, "警告", "请先查询用户信息")
            return

        exp = self.add_exp_spinbox.value()
        user_id = self.current_operation_user[0]

        # 增加经验值
        self.db.add_user_exp(user_id, exp)

        # 更新用户信息
        self.query_user_for_operation()

        QMessageBox.information(self, "成功", f"已为用户增加 {exp} 经验值")

    def remove_exp(self):
        """减少经验值"""
        if not self.current_operation_user:
            QMessageBox.warning(self, "警告", "请先查询用户信息")
            return

        exp = self.remove_exp_spinbox.value()
        user_id = self.current_operation_user[0]

        # 减少经验值
        self.db.add_user_exp(user_id, -exp)

        # 更新用户信息
        self.query_user_for_operation()

        QMessageBox.information(self, "成功", f"已为用户减少 {exp} 经验值")

    def set_exp(self):
        """设置经验值"""
        if not self.current_operation_user:
            QMessageBox.warning(self, "警告", "请先查询用户信息")
            return

        exp = self.set_exp_spinbox.value()
        user_id = self.current_operation_user[0]

        # 设置经验值
        self.db.set_user_exp(user_id, exp)

        # 更新用户信息
        self.query_user_for_operation()

        QMessageBox.information(self, "成功", f"已将用户经验值设置为: {exp}")

    def delete_user(self):
        """删除用户"""
        if not self.current_operation_user:
            QMessageBox.warning(self, "警告", "请先查询用户信息")
            return

        user_id = self.current_operation_user[0]
        username = self.current_operation_user[1]

        # 确认删除
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除用户 {username} (ID: {user_id}) 吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 删除用户
            self.db.delete_user(user_id)

            # 初始化用户信息
            self.init_operation_user_info()

            QMessageBox.information(self, "成功", f"用户 {user_id} 已删除")

    def create_batch_operation_tab(self):
        """创建批量操作标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("批量操作")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)  # 减少底部边距
        layout.addWidget(title_label)

        # 创建操作组
        operation_group = QGroupBox("批量经验值操作")
        operation_layout = QGridLayout()

        # 添加经验值操作
        operation_layout.addWidget(QLabel("操作类型:"), 0, 0)
        self.batch_operation_combo = QComboBox()
        self.batch_operation_combo.addItems(["增加", "减少", "设置"])
        operation_layout.addWidget(self.batch_operation_combo, 0, 1)

        # 经验值数量
        operation_layout.addWidget(QLabel("经验值:"), 1, 0)
        self.batch_exp_spinbox = QSpinBox()
        self.batch_exp_spinbox.setMinimum(0)
        self.batch_exp_spinbox.setMaximum(1000000)
        operation_layout.addWidget(self.batch_exp_spinbox, 1, 1)

        # 执行按钮
        execute_button = QPushButton("执行批量操作")
        execute_button.setStyleSheet("background-color: #4ecdc4; color: white;")
        execute_button.clicked.connect(self.execute_batch_operation)
        operation_layout.addWidget(execute_button, 2, 0, 1, 2)

        operation_group.setLayout(operation_layout)
        layout.addWidget(operation_group)

        # 创建结果显示
        self.batch_result_text = QTextEdit()
        self.batch_result_text.setReadOnly(True)
        self.batch_result_text.setPlaceholderText("操作结果将显示在这里")
        layout.addWidget(self.batch_result_text)

        self.tab_widget.addTab(tab, "批量操作")

    def execute_batch_operation(self):
        """执行批量操作"""
        # 获取操作类型和经验值
        operation_type = self.batch_operation_combo.currentText()
        exp = self.batch_exp_spinbox.value()

        # 获取所有用户
        users = self.db.get_all_users()
        if not users:
            QMessageBox.warning(self, "警告", "没有用户可操作")
            return

        # 确认操作
        reply = QMessageBox.question(
            self,
            "确认批量操作",
            f"确定要对所有 {len(users)} 个用户执行 {operation_type} {exp} 经验值的操作吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # 执行批量操作
        success_count = 0
        failed_count = 0
        failed_users = []

        for user in users:
            user_id = user[0]
            try:
                if operation_type == "增加":
                    self.db.add_user_exp(user_id, exp)
                elif operation_type == "减少":
                    self.db.add_user_exp(user_id, -exp)
                elif operation_type == "设置":
                    self.db.set_user_exp(user_id, exp)
                success_count += 1
            except Exception as e:
                failed_count += 1
                failed_users.append((user_id, str(e)))

        # 显示结果
        result_text = f"批量操作完成！\n"
        result_text += f"成功: {success_count} 个用户\n"
        result_text += f"失败: {failed_count} 个用户\n"

        if failed_users:
            result_text += "\n失败用户:\n"
            for user_id, error in failed_users:
                result_text += f"用户 {user_id}: {error}\n"

        self.batch_result_text.setText(result_text)

        QMessageBox.information(
            self,
            "成功",
            f"批量操作已完成，成功 {success_count} 个用户，失败 {failed_count} 个用户",
        )

    def create_database_detail_tab(self):
        """创建数据库详细标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("数据库详细")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)  # 与其他界面一致的边距
        layout.addWidget(title_label)

        # 创建统计信息组
        stats_group = QGroupBox("统计信息")
        stats_layout = QGridLayout()

        # 创建统计标签
        self.total_messages_label = QLabel("所有群组消息总数: 0")
        self.total_users_label = QLabel("用户总数: 0")
        self.total_groups_label = QLabel("群组数量: 0")
        self.database_size_label = QLabel("占用空间: 0 MB")

        # 添加到布局
        stats_layout.addWidget(self.total_messages_label, 0, 0)
        stats_layout.addWidget(self.total_users_label, 0, 1)
        stats_layout.addWidget(self.total_groups_label, 1, 0)
        stats_layout.addWidget(self.database_size_label, 1, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 创建操作按钮组
        button_layout = QHBoxLayout()

        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_database_stats)
        button_layout.addWidget(refresh_button)

        # 导出到CSV按钮
        export_button = QPushButton("导出到CSV")
        export_button.clicked.connect(self.export_to_csv)
        button_layout.addWidget(export_button)

        layout.addLayout(button_layout)

        # 创建清空数据库组
        clear_group = QGroupBox("清空数据库")
        clear_layout = QVBoxLayout()

        # 创建警告信息
        warning_label = QLabel(
            "警告：此操作将清空整个数据库并重新初始化，所有数据将被删除！请谨慎操作！"
        )
        warning_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        warning_label.setWordWrap(True)
        clear_layout.addWidget(warning_label)

        # 创建确认输入
        confirm_layout = QVBoxLayout()
        self.confirm_input1 = QLineEdit()
        self.confirm_input1.setPlaceholderText("请输入 'DELETE' 确认")
        confirm_layout.addWidget(self.confirm_input1)

        self.confirm_input2 = QLineEdit()
        self.confirm_input2.setPlaceholderText("再次输入 'DELETE' 确认")
        confirm_layout.addWidget(self.confirm_input2)

        self.confirm_input3 = QLineEdit()
        self.confirm_input3.setPlaceholderText("第三次输入 'DELETE' 确认")
        confirm_layout.addWidget(self.confirm_input3)

        clear_layout.addLayout(confirm_layout)

        # 创建清空按钮
        clear_button = QPushButton("清空数据库")
        clear_button.setStyleSheet(
            "background-color: #ff6b6b; color: white; font-weight: bold;"
        )
        clear_button.clicked.connect(self.clear_database)
        clear_layout.addWidget(clear_button)

        clear_group.setLayout(clear_layout)
        layout.addWidget(clear_group)

        self.tab_widget.addTab(tab, "数据库详细")

    def create_log_operation_tab(self):
        """创建日志操作标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 创建标题
        title_label = QLabel("日志操作")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setContentsMargins(0, 0, 0, 10)
        layout.addWidget(title_label)

        # 创建操作按钮组
        button_layout = QHBoxLayout()

        # 刷新日志按钮
        self.refresh_log_button = QPushButton("刷新日志")
        self.refresh_log_button.clicked.connect(self.refresh_log_content)
        button_layout.addWidget(self.refresh_log_button)

        # 清理日志按钮
        self.clear_log_button = QPushButton("清理日志")
        self.clear_log_button.clicked.connect(self.clear_logs)
        self.clear_log_button.setStyleSheet("background-color: #ff6b6b; color: white;")
        button_layout.addWidget(self.clear_log_button)

        layout.addLayout(button_layout)

        # 创建日志预览区域
        log_preview_group = QGroupBox("日志预览")
        log_preview_layout = QVBoxLayout(log_preview_group)

        # 创建日志文本框
        self.log_textedit = QTextEdit()
        self.log_textedit.setReadOnly(True)
        self.log_textedit.setFont(QFont("Consolas", 10))
        log_preview_layout.addWidget(self.log_textedit)

        layout.addWidget(log_preview_group)

        # 创建日志文件大小标签
        self.log_size_label = QLabel("日志占用空间: 0 KB")
        self.log_size_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.log_size_label)

        # 填充日志内容
        self.refresh_log_content()

        self.tab_widget.addTab(tab, "日志操作")

    def refresh_database_stats(self):
        """刷新数据库统计信息"""
        # 获取统计信息
        try:
            # 获取所有群组的消息总数
            groups = self.db.get_chats_info()
            total_messages = sum(group[1] for group in groups)

            # 获取用户总数
            users = self.db.get_all_users()
            total_users = len(users)

            # 获取群组数量
            total_groups = len(groups)

            # 计算数据库大小

            db_path = "data/chat.db"
            if os.path.exists(db_path):
                database_size_bytes = os.path.getsize(db_path)
                database_size = format_file_size(database_size_bytes)
            else:
                database_size = "0 B"

            # 更新标签
            self.total_messages_label.setText(f"所有群组消息总数: {total_messages}")
            self.total_users_label.setText(f"用户总数: {total_users}")
            self.total_groups_label.setText(f"群组数量: {total_groups}")
            self.database_size_label.setText(f"占用空间: {database_size}")

            # 刷新成功，无需提示
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新数据库统计信息失败: {e}")

    def export_to_csv(self):
        """导出数据到CSV"""

        # 选择导出文件夹
        folder_path = QFileDialog.getExistingDirectory(self, "选择导出文件夹")
        if not folder_path:
            return

        # 导出群组数据
        groups_file = os.path.join(folder_path, "groups.csv")
        try:
            groups = self.db.get_chats_info()
            with open(groups_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["群组ID", "群组名称", "消息数量", "最后活动时间"])
                for group in groups:
                    chat_id = group[0]
                    msg_count = group[1]
                    last_ts = group[2]
                    title = group[3] or "未知群组"
                    last_time = (
                        datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d %H:%M:%S")
                        if last_ts
                        else "未知"
                    )
                    writer.writerow([chat_id, title, msg_count, last_time])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出群组数据失败: {e}")
            return

        # 导出用户数据
        users_file = os.path.join(folder_path, "users.csv")
        try:
            users = self.db.get_all_users()
            with open(users_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["用户ID", "用户名", "经验值"])
                for user in users:
                    user_id = user[0]
                    username = user[1] or ""
                    first_name = user[2] or ""
                    last_name = user[3] or ""
                    exp = user[4]
                    name_parts = [p for p in [username, first_name, last_name] if p]
                    full_name = " ".join(name_parts) if name_parts else f"用户{user_id}"
                    writer.writerow([user_id, full_name, exp])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出用户数据失败: {e}")
            return

        QMessageBox.information(self, "成功", f"数据已成功导出到 {folder_path}")

    def clear_database(self):
        """清空数据库"""
        # 检查确认输入
        if (
            self.confirm_input1.text() != "DELETE"
            or self.confirm_input2.text() != "DELETE"
            or self.confirm_input3.text() != "DELETE"
        ):
            QMessageBox.warning(self, "警告", "请正确输入 'DELETE' 进行确认")
            return

        # 确认清空
        reply = QMessageBox.question(
            self,
            "最终确认",
            "这是最后一次确认！确定要清空整个数据库吗？所有数据将被永久删除！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # 清空数据库
                self.db.clear_database()

                # 清空确认输入
                self.confirm_input1.clear()
                self.confirm_input2.clear()
                self.confirm_input3.clear()

                # 刷新所有表格
                self.refresh_groups_table()
                self.refresh_users_table()
                self.init_user_info()
                self.init_operation_user_info()
                self.init_leaderboard()

                QMessageBox.information(self, "成功", "数据库已成功清空并重新初始化")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清空数据库失败: {e}")

    def refresh_log_content(self):
        """刷新日志内容"""
        try:
            # 检查常见的日志文件位置
            log_files = ["logs/bot.log", "bot.log", "logs.log"]

            log_content = ""
            found = False
            total_size = 0  # 日志文件总大小（字节）

            for log_file in log_files:
                if os.path.exists(log_file) and os.path.isfile(log_file):
                    # 计算文件大小
                    file_size = os.path.getsize(log_file)
                    total_size += file_size

                    try:
                        with open(
                            log_file, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()
                            if content:
                                log_content += f"=== {log_file} ===\n"
                                log_content += content
                                log_content += "\n" * 2
                                found = True
                    except Exception as e:
                        log_content += f"读取日志文件 {log_file} 失败: {str(e)}\n\n"

            if not found:
                log_content = (
                    "未找到日志文件或日志内容为空。请确保日志文件存在于以下位置之一：\n"
                    + "\n".join(log_files)
                )

            # 显示日志内容
            self.log_textedit.setText(log_content)

            # 应用高亮（简单版本）
            self.apply_log_highlighting()

            # 更新日志文件大小标签
            if total_size > 0:
                size_str = format_file_size(total_size)
                self.log_size_label.setText(f"日志占用空间: {size_str}")
            else:
                self.log_size_label.setText("日志占用空间: 0 B")

        except Exception as e:
            self.log_textedit.setText(f"刷新日志失败: {str(e)}")

    def clear_logs(self):
        """清理日志文件"""
        # 询问用户确认
        reply = QMessageBox.question(
            self,
            "确认清理",
            "此操作将清空所有日志文件的内容！\n请谨慎操作！\n\n确认要清理日志文件吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # 清理日志文件
        try:
            # 检查常见的日志文件位置
            log_files = ["logs/bot.log", "bot.log", "logs.log"]

            cleaned = []
            errors = []

            for log_file in log_files:
                if os.path.exists(log_file) and os.path.isfile(log_file):
                    try:
                        with open(log_file, "w", encoding="utf-8") as f:
                            f.write("")
                        cleaned.append(log_file)
                    except Exception as e:
                        errors.append(f"{log_file}: {str(e)}")

            # 显示结果
            if cleaned:
                message = "日志文件已成功清理:\n" + "\n".join(cleaned)
                if errors:
                    message += "\n\n清理失败的文件:\n" + "\n".join(errors)
                QMessageBox.information(self, "成功", message)
            else:
                if errors:
                    message = "清理失败:\n" + "\n".join(errors)
                    QMessageBox.critical(self, "错误", message)
                else:
                    QMessageBox.information(self, "提示", "未找到需要清理的日志文件")

            # 刷新日志内容
            self.refresh_log_content()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"清理日志失败: {str(e)}")

    def apply_log_highlighting(self):
        """应用日志高亮显示"""
        try:
            # 获取当前文本
            content = self.log_textedit.toPlainText()

            # 创建HTML内容并添加高亮
            html_content = content

            # 简单的高亮规则
            # ERROR 高亮为红色
            html_content = html_content.replace(
                "ERROR", "<span style='color: #ff6b6b; font-weight: bold;'>ERROR</span>"
            )
            # WARNING 高亮为黄色
            html_content = html_content.replace(
                "WARNING",
                "<span style='color: #ffd93d; font-weight: bold;'>WARNING</span>",
            )
            # INFO 高亮为绿色
            html_content = html_content.replace(
                "INFO", "<span style='color: #6bcb77; font-weight: bold;'>INFO</span>"
            )
            # DEBUG 高亮为蓝色
            html_content = html_content.replace(
                "DEBUG", "<span style='color: #4d96ff; font-weight: bold;'>DEBUG</span>"
            )

            # 高亮时间格式，如 2026-02-04 10:40:05
            import re

            time_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
            html_content = re.sub(
                time_pattern,
                "<span style='color: #9775fa; font-weight: bold;'>\\1</span>",
                html_content,
            )

            # 替换换行符为HTML换行
            html_content = html_content.replace("\n", "<br>")

            # 设置为HTML内容
            self.log_textedit.setHtml(html_content)

        except Exception:
            # 如果高亮失败，不影响基本功能
            pass


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置深色主题
    # setup_dark_theme(app)

    window = CookieBotGUI()
    window.show()
    sys.exit(app.exec())


def run_gui():
    """运行图形界面"""
    main()


if __name__ == "__main__":
    main()
