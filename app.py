from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_ai_response(prompt):
    """Get response from Groq's free Llama 3 model"""
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=2500,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Groq API Error: {str(e)}")


def build_prompt(city, mode):
    if mode == "travel":
        return f"""
You are EarthWell, a sustainability assistant for travelers.

IMPORTANT: Today's date is April 2026. You MUST verify and provide ONLY information that is CURRENT and ACCURATE for 2026. If a service, app, or regulation has changed or no longer exists in 2026, do NOT mention it. Be specific with resources. 

City: {city}
Mode: Short-term travel (3-7 days)

**CRITICAL FORMATTING RULES:**
1. Use **bold** for ALL location names (cities, counties, neighborhoods, specific places)
   Example: "In **Oswego County**, recycling is handled by **OCRRA**"
2. Use ### headers (###) for category titles like "### 🚲 TRANSPORT RESOURCES"
3. Use bullet points (• or -) for lists
4. Always include specific names, apps, websites, and exact locations
5. **CURRENCY CHECK: Only include apps, services, and regulations that are active**

Create a PRACTICAL sustainability guide for a tourist in **{city}** (current as of 2026):

### 🌿 TRANSPORT OPTIONS
• **{city}** public transit: [specific app names, routes, costs - VERIFY these exist in 2026]
• Bike sharing: [specific service names, how to rent - CONFIRM still operating ]
• What to avoid: [specific services to skip]

### ♻️ RECYCLING & WASTE
• Bin colors in **{city}**: [exact colors and what goes where - CURRENT for 2026]
• Key locations: [specific drop-off points - VERIFY they still exist]
• Helpful apps: [download names - CHECK they are still supported in 2026]

### 💡 QUICK TIPS
• [3 specific, actionable tips with **bolded** locations or follow sustainable values- all CONFIRMED for 2026]

Make every tip contain a specific name, place, or app that is ACTIVE and CURRENT in 2026. Be detailed and practical. If you are unsure about a service's current status in 2026, leave it out. 
"""
    else:
        return f"""
You are EarthWell, a sustainability assistant for people relocating.

IMPORTANT: Today's date is April 2026. You MUST verify and provide ONLY information that is CURRENT and ACCURATE for 2026. If a service, app, regulation, or business has changed or no longer exists in 2026, do NOT mention it.

City: {city}
Mode: Long-term resident (moving there)

**CRITICAL FORMATTING RULES:**
1. Use **bold** for ALL location names (cities, counties, neighborhoods, specific businesses)
   Example: "**Oswego County** residents should visit **Hannibal Transfer Station**"
2. Use ### headers (###) for category titles like "### 🚲 TRANSPORT RESOURCES"
3. Use bullet points (• or -) for lists
4. Always include specific names, websites, addresses where possible
5. **CURRENCY CHECK: Only include businesses, apps, and regulations that are active in 2026**

Create a DETAILED sustainability guide for someone moving to **{city}** (current as of 2026):

### 🚲 TRANSPORT RESOURCES
• Public transit in **{city}**: [specific app names, pass costs, where to buy - VERIFY 2026 availability]
• Bike infrastructure: [specific bike share names, membership fees - CONFIRM still operating]
• Car sharing: [specific service names - CHECK they exist in 2026]

### 🗑️ RECYCLING SYSTEM
• **{city}** waste management: [official website, bin colors - CURRENT for 2026]
• Special disposal: [specific locations for electronics/batteries - VERIFY still open]
• Recycling app: [download name and how to use - CHECK 2026 support]

### 🏠 HOME SUSTAINABILITY
• Green energy: [specific provider names in **{city}** - CONFIRM available in 2026]
• Bulk shopping: [specific store names and neighborhoods - VERIFY still in business]
• Farmers markets: [specific names, days, locations - CHECK 2026 schedules]

### 🌱 LOCAL INITIATIVES
• Community gardens: [specific names and how to join - VERIFY active in 2026]
• Repair cafes: [specific locations and schedules - CONFIRM still running]
• Environmental groups: [specific NGOs in **{city}** - CHECK active status]

### ⚡ PRO TIPS FOR **{city}**
• [5 specific tips with **bolded** locations, fines, and warnings - ALL CURRENT for 2026]

Make EVERY tip contain a specific name, app, website, or location that is ACTIVE and CURRENT in 2026. If you are unsure about a service's current status, leave it out. Do NOT provide outdated information.
"""


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

        print(f"Generating guide for {city} in {mode} mode...")
        prompt = build_prompt(city, mode)
        guide_text = get_ai_response(prompt)

        return jsonify({
            'success': True,
            'guide': guide_text,
            'city': city,
            'mode': mode
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🌍 EarthWell Starting with Groq...")
    app.run(debug=True)



