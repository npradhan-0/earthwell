from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from groq import Groq
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ============================================
# CONFIGURE APIS
# ============================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Gemini API configured")

if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq API configured")
else:
    groq_client = None

# ============================================
# PERSISTENT CACHE
# ============================================
CACHE_FILE = 'response_cache.json'

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        response_cache = json.load(f)
    print(f"📦 Loaded {len(response_cache)} cached responses")
else:
    response_cache = {}


def save_cache():
    with open(CACHE_FILE, 'w') as f:
        json.dump(response_cache, f)


# ============================================
# MOCK DATA FOR DEMO (Air Quality & Carbon)
# ============================================

def get_air_quality(city):
    """Mock air quality data for demo"""
    city_data = {
        'berlin': {'aqi': 42, 'level': 'Good', 'emoji': '🟢',
                   'message': 'Perfect weather for exploring Berlin\'s parks!', 'temp': 18},
        'tokyo': {'aqi': 68, 'level': 'Moderate', 'emoji': '🟡', 'message': 'Consider a mask if sensitive.', 'temp': 22},
        'london': {'aqi': 55, 'level': 'Moderate', 'emoji': '🟡', 'message': 'A walk in Hyde Park would be lovely!',
                   'temp': 15},
        'paris': {'aqi': 48, 'level': 'Good', 'emoji': '🟢', 'message': 'Perfect for a Seine river walk!', 'temp': 20},
        'singapore': {'aqi': 35, 'level': 'Good', 'emoji': '🟢', 'message': 'Enjoy the gardens by the bay!', 'temp': 28},
        'oswego': {'aqi': 45, 'level': 'Good', 'emoji': '🟢', 'message': 'Fresh Lake Ontario breeze!', 'temp': 16},
    }
    info = city_data.get(city.lower(),
                         {'aqi': 50, 'level': 'Good', 'emoji': '🟢', 'message': f'Good air quality in {city}!',
                          'temp': 20})
    return {
        'aqi': info['aqi'],
        'level': f"{info['level']} {info['emoji']}",
        'message': info['message'],
        'temperature': info['temp']
    }


def get_carbon_savings(city, mode):
    """Mock carbon savings data for demo"""
    if mode == 'travel':
        savings = {'berlin': 12.5, 'tokyo': 11.8, 'london': 13.2, 'paris': 11.5, 'singapore': 10.5, 'oswego': 9.5}.get(
            city.lower(), 11.0)
        return {'savings_kg': savings,
                'message': f"🚲 Public transit saves ~{savings}kg CO₂/day! Like charging {int(savings * 120)} phones."}
    else:
        savings = {'berlin': 2.8, 'tokyo': 2.5, 'london': 3.0, 'paris': 2.6, 'singapore': 2.3, 'oswego': 2.0}.get(
            city.lower(), 2.5)
        return {'savings_tons': savings,
                'message': f"🏡 Living car-free saves ~{savings} tons CO₂/year! Like planting {int(savings * 45)} trees."}


# ============================================
# HYBRID AI RESPONSE
# ============================================

def get_ai_response(prompt, city, mode):
    cache_key = f"{city}_{mode}"
    if cache_key in response_cache:
        print(f"📦 Cached: {city}")
        return response_cache[cache_key]

    # Try Gemini
    if GEMINI_API_KEY:
        try:
            print(f"🌐 Gemini: {city}...")
            model = genai.GenerativeModel('gemini-1.5-flash-002')
            response = model.generate_content(prompt)
            result = response.text
            response_cache[cache_key] = result
            save_cache()
            return result
        except Exception as e:
            print(f"⚠️ Gemini failed: {str(e)[:50]}...")

    # Fallback to Groq
    if groq_client:
        try:
            print(f"🔄 Groq: {city}...")
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=2000,
            )
            result = chat_completion.choices[0].message.content
            response_cache[cache_key] = result
            save_cache()
            return result
        except Exception as e:
            print(f"⚠️ Groq failed: {str(e)[:50]}...")

    # Final fallback
    result = get_fallback_response(city, mode)
    response_cache[cache_key] = result
    save_cache()
    return result


def get_fallback_response(city, mode):
    if mode == "travel":
        return f"""
### 🌿 SUSTAINABILITY GUIDE FOR {city.upper()}

### 🌍 CARBON FOOTPRINT
• Daily CO2 with taxis: ~15 kg
• Daily CO2 with transit: ~3 kg
• You save: ~12 kg CO₂ per day!

### 🚲 TRANSPORT
• Download **Citymapper** or **Google Maps**
• Look for **Lime** or **Bird** e-scooters
• Walk for distances under 1km

### ♻️ RECYCLING
• Blue bins: Paper, glass
• Green bins: Food waste
• Check local website for rules

### 💡 TIPS FOR {city}
1. Carry a reusable water bottle
2. Use public transit
3. Support local farmers markets
"""
    else:
        return f"""
### 🌿 SUSTAINABILITY GUIDE FOR {city.upper()}

### 🌍 CARBON FOOTPRINT
• Annual CO2 with car: ~3.5 tons
• Annual CO2 with transit: ~0.8 tons
• Yearly savings: ~2.7 tons CO₂!

### 🚲 TRANSPORT
• Get a monthly transit pass
• Join local bike share

### 🗑️ RECYCLING
• Visit city website for bin colors
• Find e-waste drop-off locations

### 🏠 HOME TIPS
• Switch to LED bulbs
• Buy in bulk

### ⚡ PRO TIPS
1. Get reusable bags
2. Use public transit
3. Compost food scraps
4. Repair instead of replace
5. Shop at farmers markets
"""


# ============================================
# BUILD PROMPT
# ============================================

def build_prompt(city, mode):
    air = get_air_quality(city)
    carbon = get_carbon_savings(city, mode)

    badge_text = f"\n\n**Air Quality:** AQI {air['aqi']} ({air['level']}) - {air['message']}\n**Carbon:** {carbon['message']}"

    if mode == "travel":
        return f"""
You are EarthWell. Create a sustainability guide for a tourist in {city}.{badge_text}

Format:
### 🌍 CARBON FOOTPRINT
• Daily CO2 with taxis: [X] kg
• Daily CO2 with transit: [Y] kg

### 🌿 TRANSPORT
• Specific app names for {city}
• Bike share programs

### ♻️ RECYCLING
• Bin colors and rules
• Drop-off locations

### 💡 TIPS FOR {city}
• 3 specific tips

Be specific with names and apps for {city}.
"""
    else:
        return f"""
You are EarthWell. Create a sustainability guide for someone moving to {city}.{badge_text}

Format:
### 🌍 CARBON FOOTPRINT
• Annual CO2 with car: [X] tons
• Annual CO2 with transit: [Y] tons

### 🚲 TRANSPORT
• Transit app names, pass costs
• Bike share names

### 🗑️ RECYCLING
• Official website
• Bin colors

### 🏠 HOME
• Green energy providers
• Bulk stores

### 🌱 LOCAL
• Community gardens
• Environmental groups

### ⚡ TIPS FOR {city}
• 5 specific tips

Be specific with names and websites for {city}.
"""


# ============================================
# ROUTES
# ============================================

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_guide', methods=['POST'])
def get_guide():
    try:
        data = request.json
        city = data.get('city')
        mode = data.get('mode')

        if not city:
            return jsonify({'error': 'Please enter a city'}), 400

        print(f"\n🔍 Generating guide for {city} ({mode})...")

        air = get_air_quality(city)
        carbon = get_carbon_savings(city, mode)
        prompt = build_prompt(city, mode)
        guide_text = get_ai_response(prompt, city, mode)

        return jsonify({
            'success': True,
            'guide': guide_text,
            'city': city,
            'mode': mode,
            'air_quality': air,
            'carbon': carbon
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🌍 EARTHWELL - Sustainable Living Companion")
    print("=" * 50)
    print(f"Gemini: {'✅' if GEMINI_API_KEY else '❌'}")
    print(f"Groq: {'✅' if GROQ_API_KEY else '❌'}")
    print(f"Cache: {len(response_cache)} responses")
    print("=" * 50)
    print("\n📍 http://localhost:5000\n")
    app.run(debug=True)