import re
import json
import time


from app.actions import api_call

def nutrient_worker(prompt: str):

    '''
    
    Worker to get the nutrition break down from AI, and format it correctly
    
    '''

    try:
        nutrition_details = api_call(prompt)
    except Exception as e:
        raise Exception(f"An unexpected error occurred during the Gemini API call: {e}") from e

    cleaned = re.sub(r'```json|```|\n|\s', '', nutrition_details)
    parsed_json = json.loads(cleaned)

    return parsed_json

    # time.sleep(4)

    # stuff = {
    #     "items": [
    #         {
    #         "name": "bread",
    #         "serving_size": "1 slice (~23 g)",
    #         "general": {
    #             "calories": 60,
    #             "protein": 2000
    #         },
    #         "vitamins": {
    #             "vitamin_a": 0,
    #             "vitamin_c": 0,
    #             "vitamin_d": 0,
    #             "vitamin_e": 0,
    #             "vitamin_k": 0,
    #             "vitamin_b1": 0,
    #             "vitamin_b2": 0,
    #             "vitamin_b3": 0,
    #             "vitamin_b5": 0,
    #             "vitamin_b6": 0,
    #             "vitamin_b9": 0,
    #             "vitamin_b12": 0
    #         },
    #         "minerals": {
    #             "sodium": 0,
    #             "calcium": 0,
    #             "copper": 0,
    #             "iodine": 0,
    #             "iron": 0,
    #             "magnesium": 0,
    #             "phosphorus": 0,
    #             "potassium": 0,
    #             "selenium": 0,
    #             "zinc": 0,
    #             "manganese": 0
    #         },
    #         "carbs": {
    #             "fiber": 100,
    #             "starch": 1100,
    #             "sugars": 0,
    #             "net_carbs": 1100
    #         },
    #         "fats": {
    #             "omega_3": 0,
    #             "omega_6": 0,
    #             "monounsaturated_fat": 0,
    #             "saturated_fat": 0,
    #             "trans_fat": 1000,
    #             "cholesterol": 0
    #         }
    #         },
    #         {
    #         "name": "peanut butter",
    #         "serving_size": "1 tbsp (~16 g)",
    #         "general": {
    #             "calories": 94,
    #             "protein": 4010
    #         },
    #         "vitamins": {
    #             "vitamin_a": 0,
    #             "vitamin_c": 0,
    #             "vitamin_d": 0,
    #             "vitamin_e": 0,
    #             "vitamin_k": 0,
    #             "vitamin_b1": 0,
    #             "vitamin_b2": 0,
    #             "vitamin_b3": 0,
    #             "vitamin_b5": 0,
    #             "vitamin_b6": 0,
    #             "vitamin_b9": 0,
    #             "vitamin_b12": 0
    #         },
    #         "minerals": {
    #             "sodium": 0,
    #             "calcium": 0,
    #             "copper": 0,
    #             "iodine": 0,
    #             "iron": 0,
    #             "magnesium": 0,
    #             "phosphorus": 0,
    #             "potassium": 0,
    #             "selenium": 0,
    #             "zinc": 0,
    #             "manganese": 0
    #         },
    #         "carbs": {
    #             "fiber": 0,
    #             "starch": 0,
    #             "sugars": 3130,
    #             "net_carbs": 3130
    #         },
    #         "fats": {
    #             "omega_3": 0,
    #             "omega_6": 0,
    #             "monounsaturated_fat": 10,
    #             "saturated_fat": 0,
    #             "trans_fat": 0,
    #             "cholesterol": 0
    #         }
    #         },
    #         {
    #         "name": "jelly",
    #         "serving_size": "1 tbsp (~20 g)",
    #         "general": {
    #             "calories": 53,
    #             "protein": 0
    #         },
    #         "vitamins": {
    #             "vitamin_a": 0.19,
    #             "vitamin_c": 0,
    #             "vitamin_d": 0,
    #             "vitamin_e": 0,
    #             "vitamin_k": 0.06,
    #             "vitamin_b1": 0,
    #             "vitamin_b2": 0.01,
    #             "vitamin_b3": 0.01,
    #             "vitamin_b5": 0.04,
    #             "vitamin_b6": 0,
    #             "vitamin_b9": 0.42,
    #             "vitamin_b12": 0
    #         },
    #         "minerals": {
    #             "sodium": 6.3,
    #             "calcium": 1.47,
    #             "copper": 0,
    #             "iodine": 0,
    #             "iron": 0.04,
    #             "magnesium": 1.26,
    #             "phosphorus": 1.26,
    #             "potassium": 11.34,
    #             "selenium": 0,
    #             "zinc": 0.01,
    #             "manganese": 0.03
    #         },
    #         "carbs": {
    #             "fiber": 0.2,
    #             "starch": 0,
    #             "sugars": 10200,
    #             "net_carbs": 10690
    #         },
    #         "fats": {
    #             "omega_3": 0,
    #             "omega_6": 0,
    #             "monounsaturated_fat": 10,
    #             "saturated_fat": 0,
    #             "trans_fat": 0,
    #             "cholesterol": 0
    #         }
    #         }
    #     ]
    # }

    # return stuff
