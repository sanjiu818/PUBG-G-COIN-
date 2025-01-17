# 星月汇聚活动助手

一个用于PUBG星月汇聚活动的自动化工具，支持自动签到、宝箱领取和物品兑换功能。

## 功能特点

- 自动签到
  - 支持单次签到
  - 支持持续签到（自动重试）
  - 实时显示签到状态和积分

- 宝箱领取
  - 支持定时领取
  - 可选择多个宝箱同时领取
  - 自定义领取间隔
  - 实时显示领取状态

- 物品兑换
  - 支持手动兑换
  - 支持自动兑换（积分达到300时）
  - 可选择兑换物品
  - 自定义兑换重试间隔

## 使用说明

1. 获取用户信息
   - 从活动页面复制网址
   - 点击"获取基本信息"按钮
   - 系统会自动填充用户信息

2. 签到功能
   - 点击"立即签到"进行单次签到
   - 点击"持续签到"进行自动重试签到
   - 可设置重试间隔时间

3. 宝箱领取
   - 设置目标时间（格式：YYYY-MM-DD日HH时MM分SS秒）
   - 设置领取间隔（建议500-1000毫秒）
   - 选择要领取的宝箱
   - 点击"开始领取"
   - 可随时点击"停止领取"终止任务

4. 物品兑换
   - 手动兑换：直接点击"我要兑换"按钮
   - 自动兑换：
     - 勾选"开启自动兑换"
     - 选择要兑换的物品
     - 设置重试间隔
     - 系统将在积分达到300时自动兑换

## 注意事项

1. 请合理设置领取和兑换间隔，避免请求过于频繁
2. 定时领取功能请提前设置好时间
3. 使用自动兑换功能时请确保选择了要兑换的物品
4. 程序会自动记录所有操作日志

## 系统要求

- Windows 操作系统
- 管理员权限（用于运行程序）
- 网络连接

## 版本信息

- 当前版本：1.0.0
- 更新日期：2024年
- 版权所有：© 2024 星月汇聚

## 免责声明

本程序仅供学习交流使用，请勿用于商业用途。使用本程序产生的任何后果由用户自行承担。 