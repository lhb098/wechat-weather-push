# -*- coding: utf-8 -*-
"""深圳天气定时推送：GitHub Actions cron 触发，调 Server酱 发送到微信。
数据源: open-meteo (免费无 key)。"""
import json, os, urllib.request, urllib.parse

KEY = os.environ.get("KEY", "")
SCHEDULE = os.environ.get("SCHEDULE", "").strip()

TITLES = {
    "noon":    "中午12:30·天气+吃药提醒",
    "evening": "晚上19:30·天气+吃药提醒",
    "offwork": "21:40·下班天气",
}
SLOT = "noon"
if SCHEDULE.startswith("30 11"):
    SLOT = "evening"
elif SCHEDULE.startswith("40 13"):
    SLOT = "offwork"

WMO = {0:"晴",1:"晴间多云",2:"多云",3:"阴",45:"雾",48:"雾凇",
       51:"毛毛雨",53:"毛毛雨",55:"毛毛雨",56:"冻毛毛雨",57:"冻毛毛雨",
       61:"小雨",63:"中雨",65:"大雨",66:"冻雨",67:"冻雨",
       71:"小雪",73:"中雪",75:"大雪",77:"雪粒",
       80:"阵雨",81:"强阵雨",82:"暴雨",85:"阵雪",86:"暴雪",
       95:"雷阵雨",96:"雷阵雨伴冰雹",99:"雷暴冰雹"}

def wx(code): return WMO.get(int(code), "未知")

def wind_level(kmh):
    kmh = float(kmh)
    for lv, hi in zip(range(1, 6), [7, 11, 19, 28, 38]):
        if kmh < hi: return lv
    return 6

def main():
    url = ("https://api.open-meteo.com/v1/forecast?latitude=22.5431&longitude=114.0579"
           "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
           "&hourly=precipitation_probability,temperature_2m,weather_code"
           "&timezone=Asia%2FShanghai&forecast_days=1")
    with urllib.request.urlopen(url, timeout=30) as r:
        d = json.load(r)
    c = d["current"]
    i = d["hourly"]["time"].index(d["current"]["time"])
    prob = max(d["hourly"]["precipitation_probability"][i:i+3])
    code = int(c["weather_code"])
    t = c["temperature_2m"]; hum = c["relative_humidity_2m"]
    lv = wind_level(c["wind_speed_10m"])
    rain = code in (51,53,55,61,63,65,66,67,80,81,82,95,96,99) or prob >= 40

    body = f"深圳当前{wx(code)}，气温{t}℃，湿度{hum}%，风力约{lv}级，降水概率{prob}%。\n"
    if SLOT == "noon":
        body += "药吃了吗？脂溢性皮炎和酒渣鼻的药记得按时吃，别断药。"
    elif SLOT == "evening":
        body += "今天药吃了吗？脂溢性皮炎和酒渣鼻的药按时吃，别断药。"
        if lv >= 4 or t <= 26:
            body += "晚上风较大/降温，出门注意添衣。"
    else:
        if rain:
            body += "☔ 今晚有降雨（概率%d%%），带伞！夜间%.0f℃左右，注意脚下湿滑。" % (prob, t - 2)
        else:
            body += "今晚无降雨，夜间%.0f℃左右，穿短袖即可。" % (t - 2)

    data = urllib.parse.urlencode({"title": TITLES[SLOT], "desp": body}).encode()
    req = urllib.request.Request(f"https://sctapi.ftqq.com/{KEY}.send", data=data)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(r.read().decode())
    except Exception as e:
        print("E", e)

main()
