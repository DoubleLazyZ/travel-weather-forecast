from flask import Flask, render_template, jsonify
import os
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 保持原有的 get_weather_forecast 和 send_line_notify 函數不變

def send_daily_notify():
    access_token = os.environ.get('LINE_NOTIFY_TOKEN')
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    city = os.environ.get('CITY', '釜山')
    lat = float(os.environ.get('LAT', '35.1796'))
    lon = float(os.environ.get('LON', '129.0756'))

    weather_info = get_weather_forecast(city, lat, lon, api_key)
    
    if "error" in weather_info:
        print(f"Error getting weather forecast: {weather_info['error']}")
        return
    
    message = f"{weather_info['city']} 未來15小時天氣預報：\n\n"
    for forecast in weather_info['forecasts']:
        message += (
            f"時間：{forecast['time']}\n"
            f"天氣：{forecast['weather']}\n"
            f"溫度：{forecast['temp']}°C（體感 {forecast['feels_like']}°C）\n"
            f"濕度：{forecast['humidity']}%\n"
            f"風速：{forecast['wind_speed']} m/s\n\n"
        )
    
    result = send_line_notify(message, access_token)
    print(f"Daily notification result: {result}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=send_daily_notify, trigger="cron", hour=7, minute=0)
scheduler.start()

@app.route('/')
def index():
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    city = os.environ.get('CITY', '釜山')
    lat = float(os.environ.get('LAT', '35.1796'))
    lon = float(os.environ.get('LON', '129.0756'))

    weather_info = get_weather_forecast(city, lat, lon, api_key)
    return render_template('index.html', weather=weather_info)

@app.route('/send_notify', methods=['POST'])
def send_notify():
    access_token = os.environ.get('LINE_NOTIFY_TOKEN')
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    city = os.environ.get('CITY', '釜山')
    lat = float(os.environ.get('LAT', '35.1796'))
    lon = float(os.environ.get('LON', '129.0756'))

    weather_info = get_weather_forecast(city, lat, lon, api_key)
    
    if "error" in weather_info:
        return jsonify({"status": "error", "message": weather_info["error"]})
    
    message = f"{weather_info['city']} 未來15小時天氣預報：\n\n"
    for forecast in weather_info['forecasts']:
        message += (
            f"時間：{forecast['time']}\n"
            f"天氣：{forecast['weather']}\n"
            f"溫度：{forecast['temp']}°C（體感 {forecast['feels_like']}°C）\n"
            f"濕度：{forecast['humidity']}%\n"
            f"風速：{forecast['wind_speed']} m/s\n\n"
        )
    
    result = send_line_notify(message, access_token)
    return jsonify({"status": "success", "message": result})

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv("PORT", default=5000)), host='0.0.0.0')
