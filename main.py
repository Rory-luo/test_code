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

start_date = os.getenv('START_DATE')
city = os.getenv('CITY')
city_location_dict = os.getenv('CITY_LOCATION_DICT')
city_location_dict = city_location_dict.replace("'", "\"")  # 将单引号替换为双引号
print(city_location_dict)
print(type(city_location_dict))
city_location_dict = json.loads(city_location_dict)
uv_key = os.getenv('UV_KEY')
birthday = os.getenv('BIRTHDAY')
period = os.getenv('PERIOD')

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')
after_template_id = os.getenv('AFTER_TEMPLATE_ID')
end_words = os.getenv('END_WORDS')


if app_id is None or app_secret is None:
    print('请设置 APP_ID 和 APP_SECRET')
    exit(422)

if not user_ids:
    print('请设置 USER_ID，若存在多个 ID 用回车分开')
    exit(422)

if template_id is None:
    print('请设置 TEMPLATE_ID')
    exit(422)

if after_template_id is None:
    print('请设置 AFTER_TEMPLATE_ID')
    exit(422)


# weather 直接返回对象，在使用的地方用字段进行调用。
def get_weather():
    if city is None:
        print('请设置城市')
        return None
    # # The way to access the infos has beed forbbiden
    # url = "http://autodev.openspeech.cn/csp/api/v2.1/weather?openId=aiuicus&clientType=android&sign=android&city=" + city
    # result = requests.get(url).json()
    # if result is None:
        # return None
    # weather_info = result['data']['list'][0]
    # return weather_info

    # # Use new ways to get the weather infomations}
    weather_styles = {'Clear': '晴朗', "Clouds": '多云', "Rain": '小雨', "Drizzle": '毛毛雨', "Snow": '雪', "Mist": '薄雾', "Haze": '霾', "Fog": '雾', "Thunderstorm": '雷暴', "Smoke": '大雾', "Dust": '扬尘', "Sand": '沙尘暴', "Ash": '火山灰', "Squall": '阵风', "Tornado": '龙卷风'}
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": "eaacc6730f1aabf5582aee1fe1472645",
        "units": "metric"
    }
    try:
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            temperature = data["main"]["temp"]
            description = data["weather"][0]["main"]
            weather = weather_styles[description]
            humidity = data['main']['humidity']
            highest = data['main']['temp_max']
            lowest = data['main']['temp_min']
            airQuality = evaluate_air_quality()
            airData = get_air_quality()
            wind = data['wind']['deg']
            uv_value = evaluate_uv_level(get_uv_index(), temperature)
            return {'weather': weather, 'temperature': temperature, 'humidity': humidity, 'high': highest, 'low': lowest, 'airQuality': airQuality, 'airData': airData, 'wind': wind, 'uv': uv_value}
        elif response.status_code == 401:
            print("API key is invalid or unauthorized. Please check your API key.")
            return exit(502)
        else:
            print(f"Failed to retrieve weather data. Status code: {response.status_code}")
            return exit(502)
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while making the request: {e}")
        return exit(502)

# 获取当前地区的紫外线强度
def get_uv_index():
    base_url = "https://api.openuv.io/api/v1/uv"            # The url is used to get the UV value
    headers = {
        "x-access-token": uv_key                            # The key is from the openuv.io
    }
    params = {
        "lat": city_location_dict[city]['lat'],
        "lng": city_location_dict[city]['lon']
    }

    try:
        response = requests.get(base_url, headers=headers, params=params)
        data = response.json()

        if response.status_code == 200:
            uv_index = data["result"]["uv"]
            return uv_index
        else:
            print(f"无法获取紫外线强度信息。")
            exit(422)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        exit(422)


# 判断紫外线的强度等级
def evaluate_uv_level(uv_value, temperature_value):
    if uv_value is None or temperature_value is None:
        exit(422)
    else:
        if 0 <= uv_value < 3 and temperature_value >= 15:
            return '1级，偏低，但是气温稍高，注意长时间外出的防晒工作哦~'
        elif 0 <= uv_value < 3 and temperature_value < 15:
            return '1级，偏低，气温也稍微低，适合外出'
        elif 3 <= uv_value < 6:
            return '2级，中等，注意减少阳光直晒*'
        elif 6 <= uv_value < 8:
            return '3级，高, 30~60秒便可晒红皮肤。外出请采取防护措施'
        elif 8 <= uv_value < 11:
            return '4级，甚高，只要30秒左右时间便可晒红皮肤，中午前后宜减少外出'
        else:
            return '5级，极高，不到20秒便可晒红皮肤，一般人都应避免外出，或采取特殊的防护'

            
# 获取当前地区的空气质量数值
def get_air_quality():
    # 使用AirVisual API获取空气质量，也可以获取当地的天气情况等
    weather_api_key = 'b9d8a3e0-aca4-4915-93e0-687b0ab35cd0'     # It'll expire on Nov 7, 2024, please goto https://dashboard.iqair.com/personal/api-keys to create a new from then on
    api_url = f"https://api.airvisual.com/v2/nearest_city?lat={city_location_dict[city]['lat']}&lon={city_location_dict[city]['lon']}&key={weather_api_key}"

    try:
        response = requests.get(api_url)
        data = response.json()

        if response.status_code == 200:
            air_quality = data['data']['current']['pollution']['aqius']
            return air_quality
        else:
            print(f"无法获取空气质量信息。")
            return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None


# 判断空气质量的优良状态
def evaluate_air_quality():
    aqi_value = get_air_quality()
    if aqi_value is None:
        exit(422)
    else:
        if 0 <= aqi_value <= 50:
            return "优"
        elif 51 <= aqi_value <= 100:
            return "良"
        elif 101 <= aqi_value <= 150:
            return "一般"
        elif 151 <= aqi_value <= 200:
            return "较差"
        elif 201 <= aqi_value <= 300:
            return "很差"
        else:
            return "无法评估"


# 纪念日正数
def get_memorial_days_count():
    if start_date is None:
        print('没有设置 START_DATE')
        return 0
    delta = today - datetime.strptime(start_date, "%Y-%m-%d")
    return delta.days


# 生日倒计时
def get_birthday_left():
    if birthday is None:
        print('没有设置 BIRTHDAY')
        return 0
    next_time = datetime.strptime(str(today.year) + "-" + birthday, "%Y-%m-%d")
    if next_time < nowtime:
        next_time = next_time.replace(year=next_time.year + 1)
    return (next_time - today).days


# 生理期倒计时
def get_period_left():
    if period is None:
        print('没有设置 PERIOD')
        return 0
    if str(today.month) == str(12):
        last_month_period = datetime.strptime(str(today.year) + "-" + str(today.month - 1) + "-" + period, "%Y-%m-%d")
        this_month_period = datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + period, "%Y-%m-%d")
        next_month_period = datetime.strptime(str(today.year + 1) + "-" + str(today.month - 11) + "-" + period, "%Y-%m-%d")
    elif str(today.month) == str(1):
        last_month_period = datetime.strptime(str(today.year - 1) + "-" + str(today.month + 11) + "-" + period, "%Y-%m-%d")
        this_month_period = datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + period, "%Y-%m-%d")
        next_month_period = datetime.strptime(str(today.year) + "-" + str(today.month + 1) + "-" + period, "%Y-%m-%d")
    else:
        last_month_period = datetime.strptime(str(today.year) + "-" + str(today.month - 1) + "-" + period, "%Y-%m-%d")
        this_month_period = datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + period, "%Y-%m-%d")
        next_month_period = datetime.strptime(str(today.year) + "-" + str(today.month + 1) + "-" + period, "%Y-%m-%d")
    interval_period = (nowtime - this_month_period).days
    words_list = ['辛苦我的瑶瑶了', '真棒，最后一天了', '抱抱瑶瑶~', '委屈瑶瑶啦']
    # words_list = ['辛苦我的小馋猫了', '真棒，最后一天了', '抱抱我的小美女', '委屈我的小美女啦']
    if 0 <= interval_period <= 6:
        if interval_period == 6:
            words_reply = "瑶瑶例假来了第{0}天，{1}".format(interval_period + 1, words_list[random.randint(0, 3)])
            # words_reply = "我家小美女大姨妈来了第{0}天，{1}".format(interval_period + 1, words_list[random.randint(0, 3)])
            return words_reply
        words_reply = "今天是瑶瑶例假来的第{0}天".format(interval_period + 1)
        # words_reply = "今天是小馋猫例假来的第{0}天".format(interval_period + 1)
        return words_reply
    elif interval_period < 0:
        if 0 <= (nowtime - last_month_period).days <= 6:
            if (nowtime - last_month_period).days == 6:
                words_reply = "瑶瑶大姨妈来了第{0}天，{1}".format(interval_period + 1, words_list[random.randint(0, 3)])
                # words_reply = "我家小美女大姨妈来了第{0}天，{1}".format(interval_period + 1, words_list[random.randint(0, 3)])
                return words_reply
            words_reply = "今天是瑶瑶例假来的第{0}天".format(interval_period + 1)
            # words_reply = "今天是小馋猫例假来的第{0}天".format(interval_period + 1)
            return words_reply
        words_reply = "报告，瑶瑶的例假预计还有{0}天到".format((this_month_period - nowtime).days + 1)
        # words_reply = "报告，小馋猫的大姨妈预计还有{0}天到".format((this_month_period - nowtime).days + 1)
        return words_reply
    else:
        words_reply = "报告瑶瑶，大姨妈预计还有{0}天到".format((next_month_period - nowtime).days + 1)
        # words_reply = "报告小馋猫，我家小美女的大姨妈预计还有{0}天到".format((next_month_period - nowtime).days + 1)
        return words_reply
# def get_period_left():
#     if period is None:
#         print('没有设置 PERIOD')
#         return 0
#     next_time = datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + period, "%Y-%m-%d")
#     next_time_period = (datetime.strptime(str(today.year) + "-" + str(today.month) + "-" + period, "%Y-%m-%d") + timedelta(days=7))
#     if next_time < nowtime < next_time_period:
#         words_reply = "今天是小馋猫例假来的第{0}天".format((today - next_time).days + 1)
#         return words_reply
#     if next_time.day > nowtime.day:
#         # next_time = next_time.replace(month=next_time.month + 1)
#         words_reply = "距离小馋猫的例假来临还有{0}天".format((next_time - today).days)
#         return words_reply


def get_end_words():
    if end_words is None:
        print('没有设置 END_WORDS')
        return 0
    words_list = end_words.split(',')
    words_choose = words_list[random.randint(0,len(words_list) - 1)]
    print(words_choose)
    return words_choose


# 获取今日的星期
def get_today_week():
    week_list = {'1':'一', '2':'二', '3':'三', '4':'四', '5':'五', '6':'六', '7':'天'}
    today_week = datetime.today().weekday()
    today_week = str(int(today_week) + 1)
    week_day = '星期' + week_list[today_week]
    return week_day


# 彩虹屁 接口不稳定，所以失败的话会重新调用，直到成功
def get_words():
    words = requests.get("https://api.shadiao.pro/chp")
    if words.status_code != 200:
        return get_words()
    return words.json()['data']['text']


def format_temperature(temperature):
    return math.floor(temperature)


# 随机颜色
def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


try:
    client = WeChatClient(app_id, app_secret)
except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

wm = WeChatMessage(client)
weather = get_weather()
if weather is None:
    print('获取天气失败')
    exit(422)
data = {
    "city": {
        "value": city,
        "color": get_random_color()
    },
    "date": {
        # "value": today.strftime('%Y年%m月%d日'),
        "value": nowtime.strftime('%Y年%m月%d日 %H:%M:%S'),
        "color": get_random_color()
    },
    "week_day": {
        "value": get_today_week(),
        "color": get_random_color()
    },
    "weather": {
        "value": weather['weather'],
        "color": get_random_color()
    },
    "temperature": {
        "value": math.floor(weather['temperature']),
        "color": get_random_color()
    },
    'humidity': {
        "value": weather['humidity'],
        "color": get_random_color()
    },
    "highest": {
        "value": math.floor(weather['high']),
         "color": get_random_color()
    },
    "lowest": {
        "value": math.floor(weather['low']),
         "color": get_random_color()
    },
    "air_quality": {
        "value": weather['airQuality'],
        "color": get_random_color()
    },
    "air_data": {
        "value": weather['airData'],
        "color": get_random_color()
    },
    "wind": {
        "value": weather['wind'],
        "color": get_random_color()
    },
    "uv": {
        "value": weather['uv'],
        "color": get_random_color()
    },
    "love_days": {
        "value": get_memorial_days_count(),
        "color": get_random_color()
    },
    "birthday_left": {
        "value": get_birthday_left(),
        "color": get_random_color()
    },
    "period":{
        "value": get_period_left(),
        "color": get_random_color()
    },
    "words": {
        "value": get_words(),
        "color": get_random_color()
    },
    "end_words": {
        "value": get_end_words(),
        "color": get_random_color()
    },
}

if __name__ == '__main__':
    count = 0
    try:
        for user_id in user_ids:
            if 0 <= int(nowtime.hour) < 12:
                res = wm.send_template(user_id, template_id, data)
                count += 1
            elif 12 < int(nowtime.hour) <= 18:
                res = wm.send_template(user_id, after_template_id, data)
                count += 1
            else:
                res = wm.send_template(user_id, after_template_id, data)
                count += 1
    except WeChatClientException as e:
        print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
        exit(502)

    print("发送了" + str(count) + "条消息")
