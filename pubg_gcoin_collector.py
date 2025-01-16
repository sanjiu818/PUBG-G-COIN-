import sys
import requests
import schedule
import time
import logging
import json
from urllib.parse import parse_qs, urlparse, quote
import traceback
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QTimeEdit, 
                           QTextEdit, QProgressBar, QSpinBox)
from PyQt5.QtCore import QThread, pyqtSignal, QTime, QTimer
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import ntplib
from datetime import datetime, timezone, timedelta
import os
from PyQt5.QtGui import QIcon

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gcoin_collector.log', encoding='utf-8', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包后的环境"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller会创建临时文件夹，将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CollectorThread(QThread):
    """收集器线程"""
    signal_log = pyqtSignal(str)  # 日志信号
    signal_box_status = pyqtSignal(int, str)  # 宝箱状态信号(box_number, status)
    signal_complete = pyqtSignal()  # 完成信号

    def __init__(self, collector, box_number, max_retries=50):
        super().__init__()
        self.collector = collector
        self.box_number = box_number
        self.max_retries = max_retries
        self.is_running = True
        self.success = False

    def run(self):
        retry_count = 0
        start_time = QTime.currentTime()
        
        while self.is_running and not self.success and retry_count < self.max_retries:
            try:
                result = self.collector.collect_gcoin(self.box_number)
                if result and isinstance(result, dict):
                    # 记录完整的响应信息
                    response_code = result.get('code')
                    response_msg = result.get('res', {}).get('smsg', '未知')
                    response_data = result.get('res', {}).get('data', {})
                    
                    self.signal_log.emit(f"宝箱{self.box_number}响应: code={response_code}, msg={response_msg}")
                    
                    if response_code == '00':
                        self.success = True
                        elapsed = start_time.msecsTo(QTime.currentTime()) / 1000.0
                        # 记录获得的具体奖励
                        reward_info = f"获得: {response_data}" if response_data else ""
                        self.signal_log.emit(f"宝箱{self.box_number}领取成功！{reward_info} [耗时: {elapsed:.3f}秒]")
                        self.signal_box_status.emit(self.box_number, f"成功")
                        break
                    else:
                        # 记录失败原因
                        self.signal_log.emit(f"宝箱{self.box_number}领取失败: {response_msg}")
                        self.signal_box_status.emit(self.box_number, "重试中")
                        # 如果是积分不足，直接停止尝试
                        if "积分不足" in response_msg:
                            self.signal_log.emit(f"宝箱{self.box_number}积分不足，停止尝试")
                            break
                        # 如果是未到开启时间，也停止尝试
                        if "开启时间" in response_msg:
                            self.signal_log.emit(f"宝箱{self.box_number}未到开启时间，停止尝试")
                            break
                
                retry_count += 1
                if not self.success:
                    interval = float(self.collector.request_interval)
                    time.sleep(interval)
                    
            except Exception as e:
                self.signal_log.emit(f"宝箱{self.box_number}出错: {str(e)}")
                retry_count += 1
                
        if not self.success:
            elapsed = start_time.msecsTo(QTime.currentTime()) / 1000.0
            self.signal_log.emit(f"宝箱{self.box_number}达到最大重试次数或停止尝试 [耗时: {elapsed:.3f}秒]")
            self.signal_box_status.emit(self.box_number, "失败")
        
        self.signal_complete.emit()

    def stop(self):
        self.is_running = False

class GCoinCollectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.collector = None
        self.collector_threads = []
        self.schedule_timer = None
        self.time_diff = 0  # 本地时间与北京时间的差值
        
        # 设置应用程序图标
        icon_path = resource_path('头像.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(QIcon(icon_path))
        else:
            logging.warning(f"找不到图标文件: {icon_path}")
            
        self.initUI()  # 先初始化UI
        self.sync_time()  # 再同步时间
        
    def sync_time(self):
        """同步北京时间"""
        try:
            ntp_client = ntplib.NTPClient()
            # 使用国内NTP服务器
            ntp_servers = [
                'ntp.aliyun.com',
                'ntp1.aliyun.com',
                'ntp2.aliyun.com',
                'ntp.tencent.com'
            ]
            
            for server in ntp_servers:
                try:
                    response = ntp_client.request(server, timeout=2)
                    # NTP时间戳是UTC时间
                    ntp_timestamp = response.tx_time
                    # 转换为datetime对象（UTC）
                    utc_time = datetime.fromtimestamp(ntp_timestamp, timezone.utc)
                    # 转换为北京时间（UTC+8）
                    beijing_time = utc_time.astimezone(timezone(timedelta(hours=8)))
                    # 计算本地时间与北京时间的差值
                    local_time = datetime.now(timezone.utc)
                    self.time_diff = (beijing_time - local_time.astimezone(timezone(timedelta(hours=8)))).total_seconds()
                    
                    self.log_message(f"成功同步北京时间: {beijing_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                    self.log_message(f"时间差: {self.time_diff:.3f}秒")
                    return True
                except Exception as e:
                    self.log_message(f"NTP服务器 {server} 同步失败: {str(e)}")
                    continue
                    
            self.log_message("警告：无法同步北京时间，将使用本地时间")
            return False
            
        except Exception as e:
            self.log_message(f"同步时间出错: {str(e)}")
            return False

    def get_beijing_time(self):
        """获取当前北京时间"""
        # 获取当前UTC时间
        now_utc = datetime.now(timezone.utc)
        # 转换为北京时间
        beijing_time = now_utc.astimezone(timezone(timedelta(hours=8)))
        # 应用时间差校正
        return beijing_time + timedelta(seconds=self.time_diff)

    def initUI(self):
        self.setWindowTitle('G-COIN自动收集器')
        self.setGeometry(300, 300, 1000, 800)  # 扩大窗口
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 参数配置区域
        config_layout = QVBoxLayout()
        
        # URL输入
        url_layout = QHBoxLayout()
        self.url_label = QLabel('URL:')
        self.url_input = QTextEdit()
        self.url_input.setMaximumHeight(60)
        self.url_input.setText("https://myfavoritepartner3.playbattlegrounds.com.cn/?siteinfo=VxAMK6ImVTFJd6tAbHdTnsiKnbCQyVtvz8Fng%2B%2BGhv30jsot8YItBTvy2e7qhlvoagyhonz%2BvyC18xq1xHvy0OPX%2BcM0GV5mi5SDJPx97OOwlXbV2EBZW4DG6lpbQO5Yy26H28g0grXyPJInwMynQ5HEwQfS%2FX6eIOlRcdWkotgV0s5Qie1DdJFKE3DEEdMbyTdMrh6QiHBR8mq4lYOoPEa%2FdaeadjfeQFrprltueDy410JcpXDLNm7MC7pwxO7rBiuHSz3WEC7606XOKhr2bw%3D%3D&rand=nnYCrJzlRFVXWPZPPhaSYA%3D%3D")
        url_layout.addWidget(self.url_label)
        url_layout.addWidget(self.url_input)
        config_layout.addLayout(url_layout)
        
        # UID输入
        uid_layout = QHBoxLayout()
        self.uid_label = QLabel('UID:')
        self.uid_input = QTextEdit()
        self.uid_input.setMaximumHeight(30)
        self.uid_input.setText("account.976728fcee584872a799ec5bfe95a0e4")
        uid_layout.addWidget(self.uid_label)
        uid_layout.addWidget(self.uid_input)
        config_layout.addLayout(uid_layout)
        
        # Token输入
        token_layout = QHBoxLayout()
        self.token_label = QLabel('Token:')
        self.token_input = QTextEdit()
        self.token_input.setMaximumHeight(30)
        self.token_input.setText("19b006162909605af9ce0f43070c9e2f")
        token_layout.addWidget(self.token_label)
        token_layout.addWidget(self.token_input)
        config_layout.addLayout(token_layout)

        # 请求频率设置
        freq_layout = QHBoxLayout()
        self.freq_label = QLabel('请求间隔(毫秒):')
        self.freq_input = QTextEdit()
        self.freq_input.setMaximumHeight(30)
        self.freq_input.setText("100")  # 默认100ms
        freq_layout.addWidget(self.freq_label)
        freq_layout.addWidget(self.freq_input)
        
        # 重试次数设置
        retry_layout = QHBoxLayout()
        self.retry_label = QLabel('最大重试次数:')
        self.retry_input = QTextEdit()
        self.retry_input.setMaximumHeight(30)
        self.retry_input.setText("50")  # 默认50次
        retry_layout.addWidget(self.retry_label)
        retry_layout.addWidget(self.retry_input)
        
        config_layout.addLayout(freq_layout)
        config_layout.addLayout(retry_layout)
        layout.addLayout(config_layout)

        # 时间设置区域
        time_layout = QHBoxLayout()
        self.time_label = QLabel('开始时间:')
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(21, 0))
        self.time_edit.setDisplayFormat("HH:mm:ss")  # 显示秒
        
        # 添加毫秒设置
        self.msec_label = QLabel('毫秒:')
        self.msec_edit = QSpinBox()
        self.msec_edit.setRange(0, 999)
        self.msec_edit.setValue(0)
        
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_edit)
        time_layout.addWidget(self.msec_label)
        time_layout.addWidget(self.msec_edit)
        layout.addLayout(time_layout)

        # 添加时间同步按钮
        self.sync_button = QPushButton('同步北京时间')
        self.sync_button.clicked.connect(self.sync_time)
        time_layout.addWidget(self.sync_button)
        
        # 显示当前时间
        self.current_time_label = QLabel()
        time_layout.addWidget(self.current_time_label)
        
        # 更新当前时间的定时器
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self.update_current_time)
        self.time_update_timer.start(100)  # 每100ms更新一次

        # 按钮区域
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('立即开始')
        self.schedule_button = QPushButton('定时启动')
        self.stop_button = QPushButton('停止')
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.schedule_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # 宝箱状态区域
        status_layout = QHBoxLayout()
        self.box_labels = []
        self.box_status = []
        self.box_details = []  # 新增：详细信息标签
        for i in range(3):
            box_layout = QVBoxLayout()
            self.box_labels.append(QLabel(f'宝箱{i+1}状态:'))
            self.box_status.append(QLabel('等待中'))
            self.box_details.append(QLabel('尚未开始'))  # 新增：详细信息
            box_layout.addWidget(self.box_labels[i])
            box_layout.addWidget(self.box_status[i])
            box_layout.addWidget(self.box_details[i])  # 新增：显示详细信息
            status_layout.addLayout(box_layout)
        layout.addLayout(status_layout)

        # 统计信息区域
        stats_layout = QVBoxLayout()  # 改为垂直布局
        self.stats_label = QLabel('运行统计:')
        self.stats_text = QLabel('尚未开始')
        
        # 添加详细统计信息
        self.stats_details = QTextEdit()
        self.stats_details.setReadOnly(True)
        self.stats_details.setMaximumHeight(100)
        
        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(self.stats_text)
        stats_layout.addWidget(self.stats_details)
        layout.addLayout(stats_layout)

        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # 绑定按钮事件
        self.start_button.clicked.connect(self.start_collection)
        self.schedule_button.clicked.connect(self.schedule_collection)
        self.stop_button.clicked.connect(self.stop_collection)

    def init_collector(self):
        try:
            url = self.url_input.toPlainText().strip()
            uid = self.uid_input.toPlainText().strip()
            token = self.token_input.toPlainText().strip()
            
            if not url or not uid or not token:
                self.log_message("错误：URL、UID和Token都不能为空")
                return
            
            self.collector = GCoinCollector(url, uid=uid, token=token)
            
            # 验证collector是否正确初始化
            if not self.collector.refresh_params():
                self.log_message("错误：无法获取最新参数，请检查URL是否正确")
                self.collector = None
                return
                
            self.log_message("收集器初始化完成")
            
        except Exception as e:
            self.log_message(f"收集器初始化失败: {str(e)}")
            self.collector = None

    def log_message(self, message):
        self.log_text.append(message)

    def update_box_status(self, box_number, status):
        current_time = QTime.currentTime().toString('HH:mm:ss.zzz')
        self.box_status[box_number-1].setText(status)
        self.box_details[box_number-1].setText(f'最后更新: {current_time}')
        
        # 更新统计信息
        success_count = sum(1 for status in self.box_status if status.text() == "成功")
        total_count = len(self.box_status)
        self.stats_text.setText(f'成功: {success_count}/{total_count}')
        
        # 添加详细事件记录
        event_text = f"[{current_time}] 宝箱{box_number}: {status}"
        self.stats_details.append(event_text)

    def start_collection(self):
        try:
            # 获取请求频率和重试次数
            request_interval = float(self.freq_input.toPlainText().strip()) / 1000.0
            max_retries = int(self.retry_input.toPlainText().strip())
            
            current_time = QTime.currentTime().toString('HH:mm:ss.zzz')
            self.stats_details.clear()  # 清空之前的统计
            self.stats_details.append(f"[{current_time}] 开始收集任务")
            self.stats_details.append(f"请求间隔: {request_interval}秒, 最大重试: {max_retries}次")
            
            self.log_message(f"开始收集G-COIN... [请求间隔: {request_interval}秒, 最大重试: {max_retries}次]")
            
            # 初始化收集器
            self.init_collector()
            
            # 检查收集器是否初始化成功
            if not self.collector:
                self.log_message("错误：收集器初始化失败")
                return
                
            self.start_button.setEnabled(False)
            self.schedule_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # 重置宝箱状态
            for i in range(3):
                self.update_box_status(i+1, "进行中")
                self.box_details[i].setText(f'开始时间: {QTime.currentTime().toString("HH:mm:ss.zzz")}')
            
            # 启动三个收集线程
            self.collector_threads = []
            for box_number in range(1, 4):
                thread = CollectorThread(self.collector, box_number, max_retries)
                thread.signal_log.connect(self.log_message)
                thread.signal_box_status.connect(self.update_box_status)
                thread.signal_complete.connect(self.check_all_complete)
                self.collector_threads.append(thread)
                thread.start()
                
        except ValueError as e:
            self.log_message(f"错误：请检查请求间隔和重试次数的输入格式 - {str(e)}")

    def schedule_collection(self):
        try:
            target_time = self.time_edit.time()
            target_msec = self.msec_edit.value()
            
            # 获取当前北京时间
            now = self.get_beijing_time()
            
            # 计算目标时间
            target_datetime = datetime.combine(
                now.date(),
                datetime.strptime(target_time.toString('HH:mm:ss'), '%H:%M:%S').time()
            )
            # 添加时区信息
            target_datetime = target_datetime.replace(microsecond=target_msec * 1000)
            target_datetime = target_datetime.replace(tzinfo=timezone(timedelta(hours=8)))
            
            # 如果目标时间已过，设置为明天
            if target_datetime <= now:
                target_datetime += timedelta(days=1)
            
            # 计算等待时间（毫秒）
            wait_msec = int((target_datetime - now).total_seconds() * 1000)
            
            if wait_msec < 0:
                self.log_message("错误：计算的等待时间小于0，请检查时间设置")
                return
            
            self.log_message(f"定时设置成功")
            self.log_message(f"当前北京时间: {now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            self.log_message(f"目标启动时间: {target_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
            self.log_message(f"等待时间: {wait_msec/1000:.3f}秒")
            
            # 设置定时器
            if self.schedule_timer:
                self.schedule_timer.stop()
            
            self.schedule_timer = QTimer()
            self.schedule_timer.setSingleShot(True)
            self.schedule_timer.timeout.connect(self.start_collection)
            self.schedule_timer.start(wait_msec)
            
            # 禁用开始按钮，启用取消按钮
            self.start_button.setEnabled(False)
            self.schedule_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
        except Exception as e:
            self.log_message(f"设置定时任务失败: {str(e)}")
            self.log_message(f"错误详情: {traceback.format_exc()}")

    def stop_collection(self):
        current_time = QTime.currentTime().toString('HH:mm:ss.zzz')
        self.stats_details.append(f"[{current_time}] 手动停止收集任务")
        self.log_message("正在停止收集...")
        # 停止定时器
        if self.schedule_timer:
            self.schedule_timer.stop()
        
        # 停止收集线程
        for thread in self.collector_threads:
            thread.stop()
        
        self.start_button.setEnabled(True)
        self.schedule_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def check_all_complete(self):
        all_complete = all(not thread.isRunning() for thread in self.collector_threads)
        if all_complete:
            current_time = QTime.currentTime().toString('HH:mm:ss.zzz')
            self.stats_details.append(f"[{current_time}] 所有收集任务已完成")
            self.log_message("所有收集任务已完成")
            self.start_button.setEnabled(True)
            self.schedule_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def update_current_time(self):
        """更新显示的当前时间"""
        try:
            current_time = self.get_beijing_time()
            time_str = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            self.current_time_label.setText(f"当前北京时间: {time_str}")
        except Exception as e:
            self.log_message(f"更新时间显示出错: {str(e)}")

class GCoinCollector:
    def __init__(self, url, uid=None, token=None, cookies=None, request_interval=0.1):
        self.base_url = "https://myfavoritepartner3.playbattlegrounds.com.cn"
        self.url = url
        self.uid = uid or "account.976728fcee584872a799ec5bfe95a0e4"
        self.token = token or "19b006162909605af9ce0f43070c9e2f"
        self.request_interval = request_interval  # 新增：请求间隔参数
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.base_url,
            'Referer': url,
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Connection': 'keep-alive'
        }
        self.session = requests.Session()
        
        if cookies:
            self.session.cookies.update(cookies)
        else:
            default_cookies = {
                'XSRF-TOKEN': 'eyJpdiI6IlltS0h0U0cyOStKWnZxemdXdmN5aVE9PSIsInZhbHVlIjoiaUhBSDZPdTBjZjBVQ2ROaXZ0N0h3VHVnZ1pxSkZBNjdKWnFyN3llYVdaaVorbTdNaWtmVmtTUzl4T2pKRk9QayIsIm1hYyI6IjdhNjE5YzVhNWNmMWY0NjhjNGFlMGFhYTk5OTY1NjdjN2Y0MmM1ZjM2ZDFkMDc4MmE2ZjgzYmY5MzU2OTRlZTgifQ%3D%3D',
                'laravel_session': 'eyJpdiI6IlR1MXBGQjRlQjFIaGhxbUtCR2JGSkE9PSIsInZhbHVlIjoieXNvY1IxUElTNlU1TElod2hXK0FVendXdmtNckZmWVllZUlJd2RQdUpCQm9OVWVxaG54NXBGb0p0YTRmRVBUOSIsIm1hYyI6IjZiMjFkZjA3MGE2MjlkOTQzYWYzZTVkZmU5OGQ5ODkzMGE0OGZkMmFkN2I3YmVmNzRlZGUwOGRlZWM3NWY1ZDAifQ%3D%3D'
            }
            self.session.cookies.update(default_cookies)
        
        self.refresh_params()

    def refresh_params(self):
        try:
            logging.info("正在获取最新参数...")
            response = self.session.get(self.url, headers=self.headers, timeout=30)
            if response.status_code != 200:
                logging.error(f"获取页面失败，状态码: {response.status_code}")
                return False
            
            response.encoding = 'utf-8'
            
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            parsed = urlparse(response.url)
            params = parse_qs(parsed.query)
            self.site_info = params.get('siteinfo', [None])[0]
            self.rand = params.get('rand', [None])[0]
            
            logging.debug(f"响应头: {dict(response.headers)}")
            
            logging.info(f"使用固定参数:")
            logging.info(f"uid: {self.uid}")
            logging.info(f"token: {self.token}")
            logging.info(f"siteinfo: {self.site_info}")
            logging.info(f"rand: {self.rand}")
            return True
            
        except Exception as e:
            logging.error(f"获取参数过程出错: {str(e)}")
            logging.error(f"错误堆栈: {traceback.format_exc()}")
            return False

    def collect_gcoin(self, box_number=1):
        try:
            points_required = {1: 15000, 2: 50000, 3: 200000}
            logging.info(f"尝试领取需要{points_required[box_number]}积分的青铜G-COIN宝箱...")
            
            collect_url = f"{self.base_url}/api/jan5424542/game/qexchange?"
            data = {
                'uid': self.uid,
                'token': self.token,
                'type': str(box_number)
            }
            
            collect_response = self.session.post(
                collect_url,
                data=data,
                headers=self.headers,
                timeout=30
            )
            
            logging.info(f"宝箱{box_number} 响应状态码: {collect_response.status_code}")
            logging.info(f"宝箱{box_number} 原始响应内容: {collect_response.text}")
            
            if collect_response.status_code == 200:
                try:
                    result = collect_response.json()
                    logging.info(f"宝箱{box_number} 解析后的JSON响应: {json.dumps(result, ensure_ascii=False)}")
                    return result
                except json.JSONDecodeError as e:
                    logging.error(f"宝箱{box_number} JSON解析错误: {str(e)}")
            else:
                logging.error(f"宝箱{box_number} 领取请求失败，状态码: {collect_response.status_code}")
                logging.error(f"错误信息: {collect_response.text}")
                
        except Exception as e:
            logging.error(f"宝箱{box_number} 领取过程出错: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序图标
    icon_path = resource_path('头像.ico')
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    else:
        logging.warning(f"找不到图标文件: {icon_path}")
    
    gui = GCoinCollectorGUI()
    gui.show()
    sys.exit(app.exec_()) 