from flask import Flask, render_template, jsonify
import os
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# 保持原有的 get_weather_forecast 和 send_line_notify 函數不變

def get_weather_info(city, lat, lon, api_key):
    base_url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "zh_tw",
        "appid": api_key,
        "exclude": "minutely,alerts"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        current = data['current']
        hourly = data['hourly'][:24]  # 24小時預報
        daily = data['daily'][:7]  # 7天預報

        weather_info = {
            "city": city,
            "current": {
                "temp": round(current['temp'], 1),
                "feels_like": round(current['feels_like'], 1),
                "humidity": current['humidity'],
                "wind_speed": round(current['wind_speed'], 1),
                "weather": current['weather'][0]['description'],
                "uvi": round(current['uvi'], 1)
            },
            "hourly": [{
                "time": datetime.fromtimestamp(hour['dt']).strftime("%H:%M"),
                "temp": round(hour['temp'], 1),
                "weather": hour['weather'][0]['description']
            } for hour in hourly],
            "daily": [{
                "date": datetime.fromtimestamp(day['dt']).strftime("%m/%d"),
                "temp_max": round(day['temp']['max'], 1),
                "temp_min": round(day['temp']['min'], 1),
                "weather": day['weather'][0]['description']
            } for day in daily],
            "sunrise": datetime.fromtimestamp(current['sunrise']).strftime("%H:%M"),
            "sunset": datetime.fromtimestamp(current['sunset']).strftime("%H:%M")
        }
        
        return weather_info
    except requests.RequestException as e:
        logging.error(f"Error fetching weather data: {e}")
        return {"error": f"無法獲取天氣資訊。錯誤：{str(e)}"}
    
def get_weather_forecast(city, lat, lon, api_key):
    base_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "units": "metric",
        "lang": "zh_tw",
        "appid": api_key
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        city_name = data['city']['name']
        forecast_list = data['list'][:5]  # 獲取未來15小時的預報（5個3小時間隔）
        
        weather_info = {
            "city": city_name,
            "forecasts": []
        }
        
        for forecast in forecast_list:
            dt = datetime.fromtimestamp(forecast['dt'])
            weather_info["forecasts"].append({
                "time": dt.strftime("%m月%d日 %H:%M"),
                "weather": forecast['weather'][0]['description'],
                "temp": round(forecast['main']['temp'], 1),
                "feels_like": round(forecast['main']['feels_like'], 1),
                "humidity": forecast['main']['humidity'],
                "wind_speed": round(forecast['wind']['speed'], 1)
            })
        
        return weather_info
    except requests.RequestException as e:
        logging.error(f"Error fetching weather data: {e}")
        return {"error": f"無法獲取天氣預報。錯誤：{str(e)}"}

def send_line_notify(message, access_token):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {access_token}'}
    data = {'message': message}
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return "天氣預報通知發送成功!"
    except requests.RequestException as e:
        logging.error(f"Error sending LINE notification: {e}")
        return f"發送失敗。錯誤：{str(e)}"

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
    try:
        api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
        city = os.environ.get('CITY', '釜山')
        lat = float(os.environ.get('LAT', '35.1796'))
        lon = float(os.environ.get('LON', '129.0756'))

        logging.debug(f"API Key: {api_key[:5]}... (truncated)")
        logging.debug(f"City: {city}, Lat: {lat}, Lon: {lon}")

        weather_info = get_weather_info(city, lat, lon, api_key)
        logging.debug(f"Weather info: {weather_info}")
        
        if "error" in weather_info:
            return f"Error: {weather_info['error']}", 500
        
        return render_template('index.html', weather=weather_info)
    except Exception as e:
        logging.error(f"Error in index route: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@app.route('/send_notify', methods=['POST'])
def send_notify():
    try:
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
    except Exception as e:
        logging.error(f"Error in send_notify route: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=int(os.getenv("PORT", default=5000)), host='0.0.0.0')
