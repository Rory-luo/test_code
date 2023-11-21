from datetime import datetime, timedelta
import math
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage
import requests
import os
import random
import json

nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
today = datetime.strptime(str(nowtime.date()), "%Y-%m-%d")  # 今天的日期

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

user_ids = os.getenv('USER_ID', '').split("\n")
test_template_id = os.getenv('TEST_TEMPLATE_ID')


if app_id is None or app_secret is None:
    print('请设置 APP_ID 和 APP_SECRET')
    exit(422)

if not user_ids:
    print('请设置 USER_ID，若存在多个 ID 用回车分开')
    exit(422)

if test_template_id is None:
    print('请设置 TEST_TEMPLATE_ID')
    exit(422)

def catch_holiday():
    url = "https://www.daojishi321.com"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the countdown element
        countdown_element = soup.find('div', class_='J_countdown')

        if countdown_element:
            # Extract countdown information
            countdown_text = countdown_element.get_text(strip=True)
            return countdown_text
        else:
            print("Countdown element not found on the page.")
            return exit(502)
    else:
        print("Failed to retrieve the webpage. Status code:", response.status_code)
        return exit(502)

# 随机颜色
def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


try:
    client = WeChatClient(app_id, app_secret)
except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

wm = WeChatMessage(client)
holiday = catch_holiday()
if holiday is None:
    print('获取节日倒计时失败')
    exit(422)
data = {
    "holiday": {
        "value": holiday,
        "color": get_random_color()
    },
}

if __name__ == '__main__':
    count = 0
    try:
        for user_id in user_ids:
            res = wm.send_template(user_id, test_template_id, data)
            count += 1
    except WeChatClientException as e:
        print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
        exit(502)

    print("发送了" + str(count) + "条消息")
