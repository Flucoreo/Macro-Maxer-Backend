from pydantic import BaseModel, Field
from typing import Union

Number = Union[int, float]

class UserPassword(BaseModel):
    '''
    User's password
    '''
    password: str

    model_config = {
        "from_attributes": True
    }

class TokenData(BaseModel):
    '''
    JWT Token data
    '''
    username: str | None = None

    model_config = {
        "from_attributes": True
    }

class UserCreate(BaseModel):
    '''
    Used when creating a users
    '''
    username: str
    useremail: str
    userpassword: str

    model_config = {
        "from_attributes": True
    }

class UserReturn(BaseModel):
    '''
    Used when returned user info after account is created
    '''
    id: int
    username: str
    useremail: str

    model_config = {
        "from_attributes": True
    }

class UserReturnCredits(UserReturn):
    '''
    Normal UserReturn but with the number of credits the user has left
    '''
    credits: int

    model_config = {
        "from_attributes": True
    }

class UserReturnPassword(BaseModel):
    '''
    Used when returned user info after account is created (with password)
    '''
    id: int
    username: str
    useremail: str
    userpassword: str

    model_config = {
        "from_attributes": True
    }

class UserPasswordChange(BaseModel):
    '''
    Used when the user wants to change their password
    '''

    oldpassword: str
    password: str

    model_config = {
        "from_attributes": True
    }

class GeneralSchema(BaseModel):
    Protein: Number
    Calories: Number

    model_config = {
        "from_attributes": True
    }

class CarbsSchema(BaseModel):
    Added_Sugars: Number = Field(alias="Added Sugars")
    Fiber: Number
    Net_Carbs: Number = Field(alias="Net Carbs")
    Starch: Number

    model_config = {
        "from_attributes": True
    }

class MineralsSchema(BaseModel):
    Calcium: Number
    Copper: Number
    Iodine: Number
    Iron: Number
    Magnesium: Number
    Manganese: Number
    Phosphorus: Number
    Potassium: Number
    Selenium: Number
    Sodium: Number
    Zinc: Number

    model_config = {
        "from_attributes": True
    }

class FatsSchema(BaseModel):
    Cholesterol: Number
    Total_Fat: Number = Field(alias="Total Fat")
    Saturated_Fat: Number = Field(alias="Saturated Fat")
    Omega_3: Number = Field(alias="Omega 3")
    Omega_6: Number = Field(alias="Omega 6")
    Monounsaturated_Fat: Number = Field(alias="Monounsaturated Fat")
    Trans_Fat: Number = Field(alias="Trans Fat")

    model_config = {
        "from_attributes": True
    }

class VitaminsSchema(BaseModel):
    Vitamin_A: Number = Field(alias="Vitamin A")
    Vitamin_B1: Number = Field(alias="Vitamin B1 (Thiamine)")
    Vitamin_B2: Number = Field(alias="Vitamin B2 (Riboflavin)")
    Vitamin_B3: Number = Field(alias="Vitamin B3 (Niacin)")
    Vitamin_B5: Number = Field(alias="Vitamin B5 (Pantothenic acid)")
    Vitamin_B6: Number = Field(alias="Vitamin B6 (Pyridoxine)")
    Vitamin_B9: Number = Field(alias="Vitamin B9 (Folate)")
    Vitamin_B12: Number = Field(alias="Vitamin B12 (Cobalamin)")
    Vitamin_C: Number = Field(alias="Vitamin C")
    Vitamin_D: Number = Field(alias="Vitamin D")
    Vitamin_E: Number = Field(alias="Vitamin E")
    Vitamin_K: Number = Field(alias="Vitamin K")

    model_config = {
        "from_attributes": True
    }

class UserPreferences(BaseModel):
    '''
    Used when the user sends their target nutrition preferences
    '''
    general: GeneralSchema
    carbs: CarbsSchema
    minerals: MineralsSchema
    fats: FatsSchema
    vitamins: VitaminsSchema

    model_config = {
        "from_attributes": True
    }
