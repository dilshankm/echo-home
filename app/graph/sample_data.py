"""Sample energy data based on UK ECUK 2025 statistics."""

# Energy Categories (from UK ECUK 2025 data)
CATEGORIES = [
    {
        "name": "heating",
        "kwh": 744,
        "gwh": 20838,
        "percentage": 61,
        "fuel": "gas"
    },
    {
        "name": "lighting",
        "kwh": 12,
        "gwh": 340,
        "percentage": 1,
        "fuel": "electricity"
    },
    {
        "name": "appliances",
        "kwh": 203,
        "gwh": 5689,
        "percentage": 17,
        "fuel": "electricity"
    },
    {
        "name": "water",
        "kwh": 210,
        "gwh": 5871,
        "percentage": 17,
        "fuel": "gas"
    },
    {
        "name": "cooking",
        "kwh": 45,
        "gwh": 1256,
        "percentage": 4,
        "fuel": "electricity"
    }
]

# Fuel Types
FUELS = [
    {
        "name": "gas",
        "rate_gbp_kwh": 0.06,
        "co2_kg_kwh": 0.184
    },
    {
        "name": "electricity",
        "rate_gbp_kwh": 0.24,
        "co2_kg_kwh": 0.233
    }
]

# Energy Saving Tips (20+ tips covering all categories)
TIPS = [
    # Heating Tips
    {
        "id": "tip_thermostat",
        "action": "Lower thermostat by 1°C",
        "description": "Reduces heating consumption by 10% without significant comfort loss",
        "savings_gbp": 45,
        "savings_co2": 83,
        "difficulty": "easy",
        "category": "heating"
    },
    {
        "id": "tip_smart_thermostat",
        "action": "Install smart thermostat",
        "description": "Automated scheduling reduces heating when away, saving up to 15%",
        "savings_gbp": 78,
        "savings_co2": 144,
        "difficulty": "medium",
        "category": "heating"
    },
    {
        "id": "tip_insulation",
        "action": "Improve loft insulation",
        "description": "Add 270mm insulation to reduce heat loss through roof by 25%",
        "savings_gbp": 150,
        "savings_co2": 277,
        "difficulty": "hard",
        "category": "heating"
    },
    {
        "id": "tip_draught_proof",
        "action": "Draught proof windows and doors",
        "description": "Seal gaps around windows and doors to prevent heat escape",
        "savings_gbp": 30,
        "savings_co2": 55,
        "difficulty": "easy",
        "category": "heating"
    },
    {
        "id": "tip_radiator_bleed",
        "action": "Bleed radiators regularly",
        "description": "Remove air bubbles to ensure efficient heat distribution",
        "savings_gbp": 12,
        "savings_co2": 22,
        "difficulty": "easy",
        "category": "heating"
    },
    {
        "id": "tip_heating_timer",
        "action": "Use heating timer efficiently",
        "description": "Program heating to turn off 30 minutes before leaving",
        "savings_gbp": 25,
        "savings_co2": 46,
        "difficulty": "easy",
        "category": "heating"
    },
    
    # Lighting Tips
    {
        "id": "tip_led_bulbs",
        "action": "Switch to LED bulbs",
        "description": "LEDs use 80% less energy than traditional bulbs and last 25x longer",
        "savings_gbp": 12,
        "savings_co2": 22,
        "difficulty": "easy",
        "category": "lighting"
    },
    {
        "id": "tip_turn_off_lights",
        "action": "Turn off lights when not in use",
        "description": "Simple habit can reduce lighting costs by 15-20%",
        "savings_gbp": 8,
        "savings_co2": 15,
        "difficulty": "easy",
        "category": "lighting"
    },
    {
        "id": "tip_motion_sensors",
        "action": "Install motion sensor lights",
        "description": "Automatic on/off for rooms with intermittent use",
        "savings_gbp": 5,
        "savings_co2": 9,
        "difficulty": "medium",
        "category": "lighting"
    },
    
    # Appliances Tips
    {
        "id": "tip_washing_cold",
        "action": "Wash clothes at 30°C",
        "description": "Modern detergents work at lower temperatures, saving 40% energy",
        "savings_gbp": 28,
        "savings_co2": 32,
        "difficulty": "easy",
        "category": "appliances"
    },
    {
        "id": "tip_dryer_air",
        "action": "Air dry clothes instead of tumble dryer",
        "description": "Tumble dryers are one of the most energy-intensive appliances",
        "savings_gbp": 55,
        "savings_co2": 64,
        "difficulty": "easy",
        "category": "appliances"
    },
    {
        "id": "tip_fridge_temp",
        "action": "Set fridge to 5°C, freezer to -18°C",
        "description": "Optimal temperatures that don't waste energy being too cold",
        "savings_gbp": 15,
        "savings_co2": 17,
        "difficulty": "easy",
        "category": "appliances"
    },
    {
        "id": "tip_dishwasher_full",
        "action": "Only run dishwasher when full",
        "description": "Run full loads to maximize efficiency per wash",
        "savings_gbp": 18,
        "savings_co2": 21,
        "difficulty": "easy",
        "category": "appliances"
    },
    {
        "id": "tip_appliance_upgrade",
        "action": "Upgrade to A+++ rated appliances",
        "description": "Newer appliances use 30-50% less energy than older models",
        "savings_gbp": 65,
        "savings_co2": 76,
        "difficulty": "hard",
        "category": "appliances"
    },
    {
        "id": "tip_unplug_standby",
        "action": "Unplug devices on standby",
        "description": "Standby mode can account for 5-10% of electricity use",
        "savings_gbp": 35,
        "savings_co2": 41,
        "difficulty": "easy",
        "category": "appliances"
    },
    {
        "id": "tip_washing_full",
        "action": "Wash full loads of laundry",
        "description": "Running full loads uses less energy per item washed",
        "savings_gbp": 10,
        "savings_co2": 12,
        "difficulty": "easy",
        "category": "appliances"
    },
    
    # Water Heating Tips
    {
        "id": "tip_shorter_showers",
        "action": "Take shorter showers (5 minutes)",
        "description": "Reduce shower time from 10 to 5 minutes to cut water heating costs",
        "savings_gbp": 35,
        "savings_co2": 65,
        "difficulty": "easy",
        "category": "water"
    },
    {
        "id": "tip_shower_aerator",
        "action": "Install low-flow shower head",
        "description": "Reduce water flow while maintaining pressure, saving water and heating",
        "savings_gbp": 22,
        "savings_co2": 41,
        "difficulty": "medium",
        "category": "water"
    },
    {
        "id": "tip_boiler_temp",
        "action": "Set boiler temperature to 60°C",
        "description": "Optimal temperature for hot water without excessive heating",
        "savings_gbp": 20,
        "savings_co2": 37,
        "difficulty": "easy",
        "category": "water"
    },
    {
        "id": "tip_tap_repair",
        "action": "Fix dripping taps",
        "description": "A dripping hot tap wastes both water and heating energy",
        "savings_gbp": 8,
        "savings_co2": 15,
        "difficulty": "easy",
        "category": "water"
    },
    {
        "id": "tip_insulate_boiler",
        "action": "Insulate hot water cylinder",
        "description": "Cylinder jacket reduces heat loss and saves energy",
        "savings_gbp": 25,
        "savings_co2": 46,
        "difficulty": "medium",
        "category": "water"
    },
    {
        "id": "tip_wash_cold_water",
        "action": "Use cold water for washing machine when possible",
        "description": "Cold water cycles use significantly less energy",
        "savings_gbp": 12,
        "savings_co2": 14,
        "difficulty": "easy",
        "category": "water"
    },
    
    # Cooking Tips
    {
        "id": "tip_lid_pans",
        "action": "Use lids on pans when cooking",
        "description": "Lids trap heat and reduce cooking time by 30%",
        "savings_gbp": 8,
        "savings_co2": 9,
        "difficulty": "easy",
        "category": "cooking"
    },
    {
        "id": "tip_oven_door",
        "action": "Avoid opening oven door frequently",
        "description": "Each opening loses heat and increases cooking time",
        "savings_gbp": 5,
        "savings_co2": 6,
        "difficulty": "easy",
        "category": "cooking"
    },
    {
        "id": "tip_microwave_over_oven",
        "action": "Use microwave instead of oven when possible",
        "description": "Microwaves use 50-80% less energy for reheating",
        "savings_gbp": 12,
        "savings_co2": 14,
        "difficulty": "easy",
        "category": "cooking"
    },
    {
        "id": "tip_kettle_water",
        "action": "Only boil needed amount of water",
        "description": "Boiling excess water wastes electricity unnecessarily",
        "savings_gbp": 6,
        "savings_co2": 7,
        "difficulty": "easy",
        "category": "cooking"
    },
    {
        "id": "tip_induction_hob",
        "action": "Use induction hob over gas",
        "description": "Induction hobs are more efficient and precise than gas",
        "savings_gbp": 15,
        "savings_co2": 17,
        "difficulty": "hard",
        "category": "cooking"
    },
    {
        "id": "tip_batch_cooking",
        "action": "Cook in batches and reheat",
        "description": "Cooking larger portions uses energy more efficiently",
        "savings_gbp": 10,
        "savings_co2": 12,
        "difficulty": "easy",
        "category": "cooking"
    }
]

# House Types
HOUSE_TYPES = [
    {
        "type": "flat",
        "avg_size_sqm": 800,
        "typical_occupants": 2,
        "heating_kwh_factor": 0.8  # Flats typically use less heating
    },
    {
        "type": "terraced",
        "avg_size_sqm": 1100,
        "typical_occupants": 3,
        "heating_kwh_factor": 0.9
    },
    {
        "type": "semi_detached",
        "avg_size_sqm": 1400,
        "typical_occupants": 3,
        "heating_kwh_factor": 1.0
    },
    {
        "type": "detached",
        "avg_size_sqm": 1800,
        "typical_occupants": 4,
        "heating_kwh_factor": 1.2
    }
]

