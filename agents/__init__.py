from .content_agent import ContentAgent
from .base_agent import BaseMarketingAgent
from .fashion_agent import FashionAgent
from .beauty_agent import BeautyAgent
from .coaching_agent import CoachingAgent
from .b2b_manufacturing_agent import B2BManufacturingAgent
from .food_beverage_agent import FoodBeverageAgent
from .health_wellness_agent import HealthWellnessAgent
from .travel_agent import TravelAgent
from .real_estate_agent import RealEstateAgent
from .fintech_agent import FintechAgent
from .education_agent import EducationAgent

INDUSTRY_AGENTS: dict[str, type[BaseMarketingAgent]] = {
    "1": FashionAgent,
    "2": BeautyAgent,
    "3": CoachingAgent,
    "4": B2BManufacturingAgent,
    "5": FoodBeverageAgent,
    "6": HealthWellnessAgent,
    "7": TravelAgent,
    "8": RealEstateAgent,
    "9": FintechAgent,
    "10": EducationAgent,
}

__all__ = [
    "ContentAgent",
    "BaseMarketingAgent",
    "FashionAgent",
    "BeautyAgent",
    "CoachingAgent",
    "B2BManufacturingAgent",
    "FoodBeverageAgent",
    "HealthWellnessAgent",
    "TravelAgent",
    "RealEstateAgent",
    "FintechAgent",
    "EducationAgent",
    "INDUSTRY_AGENTS",
]
