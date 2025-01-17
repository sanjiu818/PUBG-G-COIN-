import sys
import time
import requests
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit,
                           QGroupBox, QCheckBox, QTabWidget, QGridLayout, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime, Qt
from PyQt5.QtGui import QIcon
import threading
import ctypes
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

class ApiClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://myfavoritepartner3.playbattlegrounds.com.cn"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://myfavoritepartner3.playbattlegrounds.com.cn",
            "Referer": "https://myfavoritepartner3.playbattlegrounds.com.cn/"
        }

    def parse_url_params(self, url):
        """解析URL中的参数"""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            siteinfo = params.get('siteinfo', [''])[0]
            rand = params.get('rand', [''])[0]
            return siteinfo, rand
        except Exception as e:
            raise Exception(f"URL解析失败: {str(e)}")

    def get_user_info(self, url):
        """获取用户信息"""
        try:
            siteinfo, rand = self.parse_url_params(url)
            
            # 调用init接口获取token
            current_time = int(time.time() * 1000)  # 获取当前毫秒时间戳
            
            # 修改API路径
            init_url = f"{self.base_url}/api/jan5424542/init"
            
            # 构建请求头
            headers = {
                **self.headers,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }
            
            # 对参数进行额外的URL编码
            encoded_siteinfo = requests.utils.quote(requests.utils.quote(siteinfo, safe=''))
            encoded_rand = requests.utils.quote(requests.utils.quote(rand, safe=''))
            
            # 构建表单数据
            data = {
                "siteinfo": encoded_siteinfo,
                "rand": encoded_rand,
                "t": str(current_time)
            }
            
            # 使用POST方法
            response = self.session.post(
                init_url,
                data=data,
                headers=headers
            )
            
            # 打印请求信息用于调试
            print(f"请求URL: {response.url}")
            print(f"请求方法: POST")
            print(f"请求头: {response.request.headers}")
            print(f"请求数据: {data}")
            print(f"状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
            print(f"响应内容: {response.text}")  # 打印完整响应内容
            
            response.raise_for_status()
            
            try:
                data = response.json()
                # 检查登录状态
                if data.get("code") == "03":
                    error_msg = None
                    if data.get("res"):
                        error_msg = data["res"].get("smsg") or data["res"].get("tmsg")
                    if not error_msg:
                        error_msg = "登录已过期"
                    raise Exception(error_msg)
                
                if data.get("code") == "00" and data.get("res"):
                    uid = data["res"].get("uid")
                    token = data["res"].get("ticket")  # 使用ticket作为token
                    nickname = data["res"].get("user", {}).get("nickname", "")  # 获取昵称
                    scores = data["res"].get("user", {}).get("scores", "0")  # 获取积分
                    if uid and token:
                        return uid, token, nickname, scores
                    
                raise Exception(f"接口返回数据格式错误: {response.text}")
            except json.JSONDecodeError:
                raise Exception(f"接口返回数据解析失败: {response.text}")

        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"获取用户信息失败: {str(e)}")

    def log_request_error(self, response):
        """记录请求错误信息"""
        try:
            print(f"请求URL: {response.url}")
            print(f"请求方法: {response.request.method}")
            print(f"请求头: {response.request.headers}")
            print(f"状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
            print(f"响应内容: {response.text[:500]}...")
        except:
            pass

    def do_signin(self, uid, token):
        """执行签到"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/jan5424542/activity/dailyfcard",  # 修改为正确的签到接口
                data={
                    "uid": uid,
                    "token": token,
                    "type": "303"  # 添加type参数
                },
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin"
                }
            )
            
            # 打印请求信息用于调试
            print(f"签到请求URL: {response.url}")
            print(f"签到请求方法: POST")
            print(f"签到请求头: {response.request.headers}")
            print(f"签到请求数据: {{'uid': {uid}, 'token': {token}, 'type': '303'}}")
            print(f"签到响应状态码: {response.status_code}")
            print(f"签到响应头: {response.headers}")
            print(f"签到响应内容: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == "00":  # 修改成功响应码
                return data["res"].get("points", 0)  # 从res中获取积分
            else:
                error_msg = None
                if data.get("res"):
                    error_msg = data["res"].get("smsg") or data["res"].get("tmsg")
                if not error_msg:
                    error_msg = data.get("message") or data.get("msg") or "未知错误"
                raise Exception(f"{error_msg} (错误码: {data.get('code')})")
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应数据解析失败: {str(e)}, 响应内容: {response.text}")
        except Exception as e:
            raise Exception(f"签到失败: {str(e)}")

    def claim_box(self, uid, token, box_id):
        """领取宝箱"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/jan5424542/game/qexchange",  # 修正API路径
                data={
                    "uid": uid,
                    "token": token,
                    "type": str(box_id)  # 修正参数
                },
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest"
                }
            )
            
            # 打印请求信息用于调试
            print(f"宝箱领取请求URL: {response.url}")
            print(f"宝箱领取请求数据: {{'uid': {uid}, 'token': {token}, 'type': {box_id}}}")
            print(f"宝箱领取响应内容: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == "00":
                return data["res"].get("item", "领取成功")
            else:
                error_msg = None
                if data.get("res"):
                    error_msg = data["res"].get("smsg") or data["res"].get("tmsg")
                if not error_msg:
                    error_msg = data.get("message") or data.get("msg") or "未知错误"
                raise Exception(f"{error_msg} (错误码: {data.get('code')})")
        except Exception as e:
            raise Exception(f"领取宝箱失败: {str(e)}")

    def exchange_item(self, uid, token, item_id):
        """兑换物品"""
        try:
            # 打印请求信息
            print("开始兑换请求:")
            print(f"UID: {uid}")
            print(f"Token: {token}")
            print(f"Item ID: {item_id}")
            
            response = self.session.post(
                f"{self.base_url}/api/jan5424542/game/exchangedl",
                data={
                    "uid": uid,
                    "token": token,
                    "type": item_id
                },
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest",
                    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "Sec-Fetch-Dest": "empty",
                    "Sec-Fetch-Mode": "cors",
                    "Sec-Fetch-Site": "same-origin"
                }
            )
            
            # 打印响应信息
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
            print(f"响应内容: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            # 打印解析后的数据
            print(f"解析后的数据: {data}")
            
            if data["code"] == "00":  # 修改成功响应码
                return "兑换成功"
            else:
                # 获取错误信息
                error_msg = None
                if data.get("res"):
                    error_msg = data["res"].get("smsg") or data["res"].get("tmsg")
                if not error_msg:
                    error_msg = data.get("message") or data.get("msg") or "未知错误"
                raise Exception(f"{error_msg} (错误码: {data.get('code')})")
        except requests.RequestException as e:
            raise Exception(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"响应数据解析失败: {str(e)}, 响应内容: {response.text}")
        except Exception as e:
            raise Exception(str(e))

    def get_signin_status(self, uid, token):
        """获取签到状态"""
        try:
            print("\n获取用户信息请求:")
            print(f"UID: {uid}")
            print(f"Token: {token}")
            
            response = self.session.post(
                f"{self.base_url}/api/jan5424542/myinfo",
                data={
                    "uid": uid,
                    "token": token
                },
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest"
                }
            )
            
            # 打印请求和响应信息
            print(f"请求URL: {response.url}")
            print(f"请求方法: POST")
            print(f"请求头: {response.request.headers}")
            print(f"请求数据: {{'uid': {uid}, 'token': {token}}}")
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
            print(f"响应内容: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            if data["code"] == "00":
                return data["res"]
            return None
        except Exception as e:
            print(f"获取用户信息失败: {str(e)}")
            return None

    def check_login_status(self, uid, token):
        """检查登录状态"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/jan5424542/myinfo",
                data={
                    "uid": uid,
                    "token": token
                },
                headers={
                    **self.headers,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest"
                }
            )
            
            data = response.json()
            if data.get("code") == "03":
                error_msg = None
                if data.get("res"):
                    error_msg = data["res"].get("smsg") or data["res"].get("tmsg")
                if not error_msg:
                    error_msg = "登录已过期"
                return False, error_msg
            return True, None
        except Exception:
            return False, "检查登录状态失败"

class SignInWorker(QThread):
    log_signal = pyqtSignal(str)
    score_update_signal = pyqtSignal(str)
    status_update_signal = pyqtSignal(str)
    auto_exchange_signal = pyqtSignal(int)
    
    def __init__(self, api_client, uid, token):
        super().__init__()
        self.api_client = api_client
        self.uid = uid
        self.token = token
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        try:
            # 先获取签到前的积分
            before_status = self.api_client.get_signin_status(self.uid, self.token)
            if before_status:
                before_scores = int(before_status.get("scores", "0"))
                dailyLogin = before_status.get("dailyLogin")
                if dailyLogin == "1":
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 今日已签到")
                    self.status_update_signal.emit("今日已签到")
                    # 即使已经签到，也要发送积分检查信号
                    self.auto_exchange_signal.emit(before_scores)
                    return

            # 执行签到
            self.api_client.do_signin(self.uid, self.token)
            
            # 获取签到后的积分
            after_status = self.api_client.get_signin_status(self.uid, self.token)
            if after_status:
                after_scores = int(after_status.get("scores", "0"))
                # 计算获得的积分用于显示
                gained_scores = after_scores - before_scores
                self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 签到成功! 获得{gained_scores}积分")
                # 直接发送新的积分值
                self.score_update_signal.emit(str(after_scores))
                # 发送自动兑换检查信号
                self.auto_exchange_signal.emit(after_scores)
                self.status_update_signal.emit("今日已签到")
            
        except Exception as e:
            if self.is_running:
                self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 签到错误: {str(e)}")

    def __del__(self):
        self.is_running = False
        self.wait()

class ExchangeWorker(QThread):
    log_signal = pyqtSignal(str)
    score_update_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, api_client, uid, token, item_id, item_name, retry_interval=100):
        super().__init__()
        self.api_client = api_client
        self.uid = uid
        self.token = token
        self.item_id = item_id
        self.item_name = item_name
        self.retry_interval = retry_interval
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                # 执行兑换
                result = self.api_client.exchange_item(self.uid, self.token, self.item_id)
                self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.item_name} {result}")
                
                # 兑换成功后更新积分并停止
                if result == "兑换成功":
                    status = self.api_client.get_signin_status(self.uid, self.token)
                    if status:
                        new_scores = status.get("scores", "0")
                        self.score_update_signal.emit(str(new_scores))
                    self.is_running = False
                    return
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    # 遇到429错误继续重试
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 兑换请求过于频繁，{self.retry_interval}毫秒后重试...")
                    time.sleep(self.retry_interval / 1000)
                    continue
                elif "积分不足" in error_msg:
                    # 积分不足时停止
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 兑换错误: {error_msg}")
                    self.error_signal.emit(error_msg)
                    self.is_running = False
                    return
                else:
                    # 其他错误也继续重试
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 兑换错误: {error_msg}，将继续重试...")
                    time.sleep(self.retry_interval / 1000)
                    continue

    def stop(self):
        self.is_running = False

    def __del__(self):
        self.is_running = False
        self.wait()

class JacketWorker(QThread):
    log_signal = pyqtSignal(str)
    
    def __init__(self, api_client, uid, token, box_id, delay, target_time=None):
        super().__init__()
        self.api_client = api_client
        self.uid = uid
        self.token = token
        self.box_id = box_id
        self.delay = delay
        self.target_time = target_time
        self.is_running = True

    def run(self):
        # 如果设置了目标时间，等待直到目标时间
        if self.target_time:
            while datetime.now() < self.target_time and self.is_running:
                time.sleep(0.1)
                
            if not self.is_running:
                return
                
            self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 到达目标时间，开始领取宝箱")

        last_time = 0
        while self.is_running:
            try:
                current_time = time.time() * 1000
                
                # 检查是否达到延迟时间
                if current_time - last_time < self.delay:
                    time.sleep((self.delay - (current_time - last_time)) / 1000)
                
                result = self.api_client.claim_box(self.uid, self.token, self.box_id)
                self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 宝箱{self.box_id}领取成功: {result}")
                
                # 更新上次请求时间
                last_time = time.time() * 1000
                
                # 领取成功后停止
                if "领取成功" in result:
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 宝箱{self.box_id}已成功领取，停止任务")
                    self.is_running = False
                    return
                
                # 等待指定延迟时间
                time.sleep(self.delay / 1000)
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    # 请求过于频繁，继续重试
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 宝箱{self.box_id}请求过于频繁，{self.delay}毫秒后重试...")
                    time.sleep(self.delay / 1000)
                    continue
                elif "已领取" in error_msg:
                    # 宝箱已被领取，停止任务
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 宝箱{self.box_id}已被领取，停止任务")
                    self.is_running = False
                    return
                else:
                    # 其他错误继续重试
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 宝箱{self.box_id}领取失败: {error_msg}，将继续重试...")
                    time.sleep(self.delay / 1000)
                    continue

    def stop(self):
        self.is_running = False

    def __del__(self):
        self.is_running = False
        self.wait()

class ContinuousSignInWorker(QThread):
    log_signal = pyqtSignal(str)
    score_update_signal = pyqtSignal(str)
    status_update_signal = pyqtSignal(str)
    auto_exchange_signal = pyqtSignal(int)
    
    def __init__(self, api_client, uid, token, interval):
        super().__init__()
        self.api_client = api_client
        self.uid = uid
        self.token = token
        self.interval = interval
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        while self.is_running:
            try:
                # 获取签到前的积分
                before_status = self.api_client.get_signin_status(self.uid, self.token)
                if before_status:
                    before_scores = int(before_status.get("scores", "0"))
                    dailyLogin = before_status.get("dailyLogin")
                    if dailyLogin == "1":
                        self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 今日已签到")
                        self.status_update_signal.emit("今日已签到")
                        self.auto_exchange_signal.emit(before_scores)
                        self.is_running = False
                        return

                # 执行签到
                self.api_client.do_signin(self.uid, self.token)
                
                # 获取签到后的积分
                after_status = self.api_client.get_signin_status(self.uid, self.token)
                if after_status:
                    after_scores = int(after_status.get("scores", "0"))
                    gained_scores = after_scores - before_scores
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 签到成功! 获得{gained_scores}积分")
                    self.score_update_signal.emit(str(after_scores))
                    self.auto_exchange_signal.emit(after_scores)
                    self.status_update_signal.emit("今日已签到")
                    self.is_running = False
                    return
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 请求过于频繁，等待重试...")
                    time.sleep(self.interval / 1000)
                    continue
                elif "已领取" in error_msg:
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 今日已签到")
                    self.status_update_signal.emit("今日已签到")
                    status = self.api_client.get_signin_status(self.uid, self.token)
                    if status:
                        current_scores = int(status.get("scores", "0"))
                        self.auto_exchange_signal.emit(current_scores)
                    self.is_running = False
                    return
                else:
                    self.log_signal.emit(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 签到错误: {error_msg}")
                    time.sleep(self.interval / 1000)

    def stop(self):
        self.is_running = False

    def __del__(self):
        self.is_running = False
        self.wait()

class MainWindow(QMainWindow):
    # 添加log_signal定义
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("星月汇聚活动助手")
        # 修改窗口大小和位置
        screen = QApplication.primaryScreen().geometry()
        # 计算窗口位置，使其居中显示
        x = (screen.width() - 600) // 2
        y = (screen.height() - 500) // 2
        self.setGeometry(x, y, 600, 500)
        # 设置窗口固定大小，防止用户调整
        self.setFixedSize(600, 500)
        self.workers = []
        self.api_client = ApiClient()
        # 使用绝对路径设置图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '头像.ico')
        self.setWindowIcon(QIcon(icon_path))
        self.initUI()
        # 添加初始化检查
        self.check_auto_exchange_status()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建标签页
        tab_widget = QTabWidget()
        
        # 用户信息标签页
        user_info_tab = QWidget()
        user_info_layout = QVBoxLayout()
        
        # 用户信息区域
        user_group = QGroupBox("用户个人信息区")
        user_layout = QVBoxLayout()

        # 网址输入
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("网页:"))
        self.url_input = QLineEdit()
        url_layout.addWidget(self.url_input)
        user_layout.addLayout(url_layout)

        # 获取信息按钮
        get_info_btn = QPushButton("获取基本信息")
        get_info_btn.clicked.connect(self.get_user_info)
        user_layout.addWidget(get_info_btn)

        # 昵称显示
        nickname_layout = QHBoxLayout()
        nickname_layout.addWidget(QLabel("昵称:"))
        self.nickname_input = QLineEdit()
        self.nickname_input.setReadOnly(True)
        nickname_layout.addWidget(self.nickname_input)
        user_layout.addLayout(nickname_layout)

        # UID和TOKEN显示
        uid_layout = QHBoxLayout()
        uid_layout.addWidget(QLabel("UID:"))
        self.uid_input = QLineEdit()
        uid_layout.addWidget(self.uid_input)
        user_layout.addLayout(uid_layout)

        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("TOKEN:"))
        self.token_input = QLineEdit()
        token_layout.addWidget(self.token_input)
        user_layout.addLayout(token_layout)

        # 积分显示
        scores_layout = QHBoxLayout()
        scores_layout.addWidget(QLabel("当前积分:"))
        self.scores_input = QLineEdit()
        self.scores_input.setReadOnly(True)
        scores_layout.addWidget(self.scores_input)
        user_layout.addLayout(scores_layout)

        user_group.setLayout(user_layout)
        user_info_layout.addWidget(user_group)
        user_info_tab.setLayout(user_info_layout)
        
        # 签到标签页
        signin_tab = QWidget()
        signin_layout = QVBoxLayout()
        
        signin_group = QGroupBox("每日签到")
        signin_inner_layout = QVBoxLayout()
        
        # 签到状态显示
        self.signin_status = QLabel("今日未签到")
        signin_inner_layout.addWidget(self.signin_status)
        
        # 持续签到设置
        continuous_signin_settings = QHBoxLayout()
        continuous_signin_settings.addWidget(QLabel("重试间隔(毫秒):"))
        self.continuous_signin_interval = QLineEdit("100")
        continuous_signin_settings.addWidget(self.continuous_signin_interval)
        signin_inner_layout.addLayout(continuous_signin_settings)
        
        # 签到按钮布局
        signin_buttons_layout = QHBoxLayout()
        
        # 普通签到按钮
        signin_btn = QPushButton("立即签到")
        signin_btn.clicked.connect(self.do_signin)
        signin_buttons_layout.addWidget(signin_btn)
        
        # 持续签到按钮
        continuous_signin_btn = QPushButton("持续签到")
        continuous_signin_btn.clicked.connect(self.do_continuous_signin)
        signin_buttons_layout.addWidget(continuous_signin_btn)
        
        signin_inner_layout.addLayout(signin_buttons_layout)
        signin_group.setLayout(signin_inner_layout)
        signin_layout.addWidget(signin_group)
        signin_tab.setLayout(signin_layout)

        # 兑换标签页
        exchange_tab = QWidget()
        exchange_layout = QGridLayout()
        
        # 添加兑换物品
        self.add_exchange_items(exchange_layout)
        exchange_tab.setLayout(exchange_layout)

        # 宝箱标签页
        box_tab = QWidget()
        box_layout = QVBoxLayout()
        
        # 宝箱领取区域
        box_group = QGroupBox("宝箱领取区域")
        box_inner_layout = QVBoxLayout()

        # 时间设置
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("时间:"))
        self.time_input = QLineEdit("2025-1-16日20时59分57秒")
        time_layout.addWidget(self.time_input)
        box_inner_layout.addLayout(time_layout)

        # 延迟设置
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("延迟(ms):"))
        self.delay_input = QLineEdit("700")
        delay_layout.addWidget(self.delay_input)
        box_inner_layout.addLayout(delay_layout)

        # 延迟说明
        delay_info = QLabel("说明: 延迟时间决定了两次请求之间的最小间隔，建议设置在500-1000毫秒之间")
        delay_info.setWordWrap(True)
        box_inner_layout.addWidget(delay_info)

        # 宝箱选择区域
        box_select_group = QGroupBox("选择要领取的宝箱")
        box_select_layout = QVBoxLayout()
        
        # 复选框
        self.checkboxes = []
        box_names = ["宝箱1", "宝箱2", "宝箱3"]
        for i in range(3):
            cb = QCheckBox(f"{box_names[i]}")
            self.checkboxes.append(cb)
            box_select_layout.addWidget(cb)
        
        box_select_group.setLayout(box_select_layout)
        box_inner_layout.addWidget(box_select_group)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始领取")
        self.start_btn.clicked.connect(self.start_tasks)
        button_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止领取")
        self.stop_btn.clicked.connect(self.stop_tasks)
        button_layout.addWidget(self.stop_btn)
        
        box_inner_layout.addLayout(button_layout)

        box_group.setLayout(box_inner_layout)
        box_layout.addWidget(box_group)
        box_tab.setLayout(box_layout)

        # 添加所有标签页
        tab_widget.addTab(user_info_tab, "用户信息")
        tab_widget.addTab(signin_tab, "每日签到")
        tab_widget.addTab(box_tab, "宝箱领取")
        tab_widget.addTab(exchange_tab, "物品兑换")
        
        layout.addWidget(tab_widget)

        # 日志区域
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def add_exchange_items(self, layout):
        # 自动兑换控制区域
        auto_exchange_group = QGroupBox("自动兑换设置")
        auto_layout = QVBoxLayout()
        
        # 开启自动兑换的开关
        self.auto_exchange_checkbox = QCheckBox("开启自动兑换（积分达到300时自动兑换）")
        self.auto_exchange_checkbox.stateChanged.connect(self.on_auto_exchange_changed)
        auto_layout.addWidget(self.auto_exchange_checkbox)
        
        # 添加重试间隔设置
        retry_interval_layout = QHBoxLayout()
        retry_interval_layout.addWidget(QLabel("兑换重试间隔(毫秒):"))
        self.exchange_retry_interval = QLineEdit("100")
        retry_interval_layout.addWidget(self.exchange_retry_interval)
        auto_layout.addLayout(retry_interval_layout)
        
        # 夹克选择区域
        jacket_group = QGroupBox("选择要自动兑换的夹克")
        jacket_layout = QVBoxLayout()
        self.godv_checkbox = QCheckBox("GODV的摩托夹克(永久)")
        self.pigff_checkbox = QCheckBox("pigff的摩托夹克(永久)")
        jacket_layout.addWidget(self.godv_checkbox)
        jacket_layout.addWidget(self.pigff_checkbox)
        jacket_group.setLayout(jacket_layout)
        auto_layout.addWidget(jacket_group)
        
        # 自动兑换状态显示
        self.exchange_status = QLabel("自动兑换状态：未开启")
        self.exchange_status.setStyleSheet("color: gray;")
        auto_layout.addWidget(self.exchange_status)
        
        auto_exchange_group.setLayout(auto_layout)
        layout.addWidget(auto_exchange_group, 0, 0, 1, 4)
        
        # 手动兑换区域
        manual_exchange_group = QGroupBox("手动兑换")
        manual_layout = QGridLayout()
        
        items = [
            {"name": "GODV的摩托夹克(永久)", "points": "300", "limit": "限量500名", "id": "37"},
            {"name": "pigff的摩托夹克(永久)", "points": "300", "limit": "限量500名", "id": "38"}
        ]

        for i, item in enumerate(items):
            info_label = QLabel(f"{item['name']}\n{item['points']}积分 ({item['limit']})")
            exchange_btn = QPushButton("我要兑换")
            exchange_btn.clicked.connect(lambda checked, x=item: self.do_exchange(x))
            
            manual_layout.addWidget(info_label, i, 0)
            manual_layout.addWidget(exchange_btn, i, 1)
        
        manual_exchange_group.setLayout(manual_layout)
        layout.addWidget(manual_exchange_group, 1, 0, 1, 4)

    def handle_auto_exchange(self, scores):
        """处理自动兑换逻辑"""
        if not hasattr(self, 'auto_exchange_checkbox') or not self.auto_exchange_checkbox.isChecked():
            return
        
        if not hasattr(self, 'exchange_in_progress'):
            self.exchange_in_progress = False
        
        if self.exchange_in_progress:
            return
            
        if scores >= 300:
            self.exchange_in_progress = True
            self.exchange_status.setText("自动兑换状态：正在尝试兑换...")
            self.exchange_status.setStyleSheet("color: blue;")
            
            try:
                retry_interval = int(self.exchange_retry_interval.text())
                if retry_interval < 0:
                    raise ValueError("间隔时间不能为负数")
            except ValueError:
                self.exchange_status.setText("自动兑换状态：请输入有效的重试间隔时间")
                self.exchange_status.setStyleSheet("color: red;")
                self.exchange_in_progress = False
                return
            
            # 获取用户选择的夹克
            selected_items = []
            if self.godv_checkbox.isChecked():
                selected_items.append({"id": "37", "name": "GODV的摩托夹克(永久)"})
            if self.pigff_checkbox.isChecked():
                selected_items.append({"id": "38", "name": "pigff的摩托夹克(永久)"})
            
            if not selected_items:
                self.exchange_status.setText("自动兑换状态：请选择要兑换的夹克")
                self.exchange_status.setStyleSheet("color: red;")
                self.exchange_in_progress = False
                return
            
            # 创建兑换任务
            for item in selected_items:
                worker = ExchangeWorker(self.api_client, self.uid_input.text(), 
                                      self.token_input.text(), item["id"], 
                                      item["name"], retry_interval)
                worker.log_signal.connect(self.update_log)
                worker.score_update_signal.connect(self.update_scores)
                worker.error_signal.connect(self.handle_exchange_error)
                worker.finished.connect(self.handle_exchange_finished)
                worker.start()
                self.workers.append(worker)
    
    def handle_exchange_error(self, error_msg):
        """处理兑换错误"""
        self.exchange_status.setText(f"自动兑换状态：兑换失败 - {error_msg}")
        self.exchange_status.setStyleSheet("color: red;")
        self.exchange_in_progress = False
    
    def handle_exchange_finished(self):
        """处理兑换完成"""
        self.exchange_status.setText("自动兑换状态：兑换完成")
        self.exchange_status.setStyleSheet("color: green;")
        self.exchange_in_progress = False
        self.auto_exchange_checkbox.setChecked(False)

    def get_user_info(self):
        url = self.url_input.text()
        try:
            uid, token, nickname, scores = self.api_client.get_user_info(url)
            self.uid_input.setText(uid)
            self.token_input.setText(token)
            self.nickname_input.setText(nickname)
            self.scores_input.setText(scores)  # 改回显示真实积分
            self.log_text.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 成功获取用户信息: {nickname} (积分: {scores})")
            
            # 如果自动兑换已开启，检查真实积分
            if hasattr(self, 'auto_exchange_checkbox') and self.auto_exchange_checkbox.isChecked():
                try:
                    current_scores = int(scores)
                    if current_scores >= 300:
                        self.handle_auto_exchange(current_scores)
                except ValueError:
                    pass
            
        except Exception as e:
            self.log_text.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 获取用户信息失败: {str(e)}")
            QMessageBox.warning(self, "错误", str(e))

    def do_signin(self):
        uid = self.uid_input.text()
        token = self.token_input.text()
        
        if not uid or not token:
            QMessageBox.warning(self, "错误", "请先获取用户信息")
            return

        worker = SignInWorker(self.api_client, uid, token)
        worker.log_signal.connect(self.update_log)
        worker.score_update_signal.connect(self.update_scores)
        worker.status_update_signal.connect(self.update_signin_status)
        worker.auto_exchange_signal.connect(self.handle_auto_exchange)
        worker.start()
        self.workers.append(worker)

    def do_exchange(self, item):
        uid = self.uid_input.text()
        token = self.token_input.text()
        
        if not uid or not token:
            QMessageBox.warning(self, "错误", "请先获取用户信息")
            return

        # 检查登录状态
        is_logged_in, error_msg = self.api_client.check_login_status(uid, token)
        if not is_logged_in:
            self.log_text.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
            QMessageBox.warning(self, "错误", error_msg)
            return
            
        try:
            retry_interval = int(self.exchange_retry_interval.text())
            if retry_interval < 0:
                raise ValueError("间隔时间不能为负数")
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的重试间隔时间（毫秒）")
            return

        # 创建兑换任务
        worker = ExchangeWorker(self.api_client, uid, token, item["id"], 
                              item["name"], retry_interval)
        worker.log_signal.connect(self.update_log)
        worker.score_update_signal.connect(self.update_scores)
        worker.error_signal.connect(self.show_exchange_error)
        worker.start()
        self.workers.append(worker)

    def show_exchange_error(self, error_msg):
        """显示兑换错误对话框"""
        QMessageBox.warning(self, "兑换失败", error_msg)

    def start_tasks(self):
        uid = self.uid_input.text()
        token = self.token_input.text()
        
        if not uid or not token:
            QMessageBox.warning(self, "错误", "请先获取用户信息")
            return

        try:
            # 解析目标时间
            target_time_str = self.time_input.text().replace("日", " ").replace("时", ":").replace("分", ":").replace("秒", "")
            target_time = datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S")
            
            delay = int(self.delay_input.text())

            for i, checkbox in enumerate(self.checkboxes):
                if checkbox.isChecked():
                    worker = JacketWorker(self.api_client, uid, token, i+1, delay, target_time)
                    worker.log_signal.connect(self.update_log)
                    worker.start()
                    self.workers.append(worker)

            # 直接使用update_log方法而不是发送信号
            self.update_log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 任务已启动，将在 {target_time_str} 开始领取宝箱")
        except ValueError as e:
            QMessageBox.warning(self, "错误", "时间格式错误，请使用正确的格式，例如：2025-1-16日20时59分57秒")
            return

    def stop_tasks(self):
        for worker in self.workers[:]:
            try:
                if hasattr(worker, 'stop'):
                    worker.stop()
                    # 添加超时等待
                    if not worker.wait(3000):  # 等待最多3秒
                        worker.terminate()  # 强制终止
                    self.workers.remove(worker)
                else:
                    # 对于没有stop方法的worker，直接终止
                    worker.terminate()
                    self.workers.remove(worker)
            except Exception as e:
                self.log_text.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 停止任务时出错: {str(e)}")
        
        self.log_text.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 停止所有任务")

    def update_log(self, message):
        self.log_text.append(message)

    def update_scores(self, scores):
        """更新积分显示"""
        try:
            # 直接设置新的积分值
            self.scores_input.setText(scores)
        except ValueError:
            pass

    def update_signin_status(self, status):
        """更新签到状态显示"""
        self.signin_status.setText(status)

    def do_continuous_signin(self):
        uid = self.uid_input.text()
        token = self.token_input.text()
        
        if not uid or not token:
            QMessageBox.warning(self, "错误", "请先获取用户信息")
            return
            
        try:
            interval = int(self.continuous_signin_interval.text())
            if interval < 0:
                raise ValueError("间隔时间不能为负数")
        except ValueError as e:
            QMessageBox.warning(self, "错误", "请输入有效的间隔时间（毫秒）")
            return

        worker = ContinuousSignInWorker(self.api_client, uid, token, interval)
        worker.log_signal.connect(self.update_log)
        worker.score_update_signal.connect(self.update_scores)
        worker.status_update_signal.connect(self.update_signin_status)
        worker.auto_exchange_signal.connect(self.handle_auto_exchange)
        worker.start()
        self.workers.append(worker)

    def check_auto_exchange_status(self):
        """检查并更新自动兑换状态"""
        if hasattr(self, 'auto_exchange_checkbox') and hasattr(self, 'exchange_status'):
            if self.auto_exchange_checkbox.isChecked():
                self.exchange_status.setText("自动兑换状态：已开启")
                self.exchange_status.setStyleSheet("color: green;")
            else:
                self.exchange_status.setText("自动兑换状态：未开启")
                self.exchange_status.setStyleSheet("color: gray;")

    def on_auto_exchange_changed(self, state):
        """处理自动兑换状态变化"""
        if state == Qt.Checked:
            self.exchange_status.setText("自动兑换状态：已开启")
            self.exchange_status.setStyleSheet("color: green;")
            # 检查当前积分，如果已经达到300就立即触发兑换
            try:
                current_scores = int(self.scores_input.text())
                if current_scores >= 300:
                    self.handle_auto_exchange(current_scores)
            except ValueError:
                pass
        else:
            self.exchange_status.setText("自动兑换状态：未开启")
            self.exchange_status.setStyleSheet("color: gray;")

    def __del__(self):
        self.is_running = False
        self.wait()

if __name__ == '__main__':
    # 确保主程序在这里运行
    app = QApplication(sys.argv)
    
    # 设置应用程序图标（这会影响任务栏和窗口图标）
    myappid = 'mycompany.starmoongather.app.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    # 使用绝对路径设置图标
    icon_path = r'E:\token\头像.ico'
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)
    
    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()
    sys.exit(app.exec_()) 