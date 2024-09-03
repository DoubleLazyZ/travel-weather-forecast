import os
from flask import Flask, render_template
import requests
from datetime import datetime

app = Flask(__name__)

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
        
        weather_info = f"{city_name} 未來15小時天氣預報：\n\n"
        
        for forecast in forecast_list:
            dt = datetime.fromtimestamp(forecast['dt'])
            date = dt.strftime("%m月%d日 %H:%M")
            temp = forecast['main']['temp']
            feels_like = forecast['main']['feels_like']
            humidity = forecast['main']['humidity']
            description = forecast['weather'][0]['description']
            wind_speed = forecast['wind']['speed']
            
            weather_info += (
                f"時間：{date}\n"
                f"天氣：{description}\n"
                f"溫度：{temp:.1f}°C（體感 {feels_like:.1f}°C）\n"
                f"濕度：{humidity}%\n"
                f"風速：{wind_speed:.1f} m/s\n\n"
            )
        
        return weather_info.strip()
    except requests.RequestException as e:
        return f"無法獲取天氣預報。錯誤：{e}"

def send_line_notify(message, access_token):
    url = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {access_token}'}
    data = {'message': message}
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return "天氣預報通知發送成功!"
    except requests.RequestException as e:
        return f"發送失敗。錯誤：{e}"

@app.route('/')
def index():
    access_token = os.environ.get('LINE_NOTIFY_TOKEN')
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    city = os.environ.get('CITY', '釜山')
    lat = float(os.environ.get('LAT', '35.1796'))
    lon = float(os.environ.get('LON', '129.0756'))

    weather = get_weather_forecast(city, lat, lon, api_key)
    result = send_line_notify(weather, access_token)

    return render_template('index.html', message=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
