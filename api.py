from livekit.agents import function_tool, Agent, RunContext
from prompts import INSTRUCTIONS
import enum
from typing import Annotated
import logging
from db_driver import DatabaseDriver

logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()

class CarDetails(enum.Enum):
    VIN = "vin"
    MAKE = "make"
    MODEL = "model"
    YEAR = "year"

class Assistant(Agent):
    def __init__(self):
        super().__init__(instructions=INSTRUCTIONS)

        self._car_details = {
            CarDetails.VIN: None,
            CarDetails.MAKE: None,
            CarDetails.MODEL: None,
            CarDetails.YEAR: None
        }

    def get_car_str(self):
        car_str = ""
        for key, value in self._car_details.items():
            car_str += f"{key.value.capitalize()}: {value}\n"

        return car_str
    
    @function_tool()
    async def lookup_car(self, 
                         context: RunContext, 
                         vin: Annotated[str, "The VIN of the car to look up."]) -> str:
        """Look up a car by its VIN."""
        logger.info(f"Looking up car with VIN: {vin}")
        car = DB.get_car_by_vin(vin)
        if not car:
            return f"No car found with VIN {vin}."
        
        self._car_details[CarDetails.VIN] = car.vin
        self._car_details[CarDetails.MAKE] = car.make
        self._car_details[CarDetails.MODEL] = car.model
        self._car_details[CarDetails.YEAR] = car.year
        
        return f"The car details are: {self.get_car_str()}."
    
    @function_tool()
    async def create_car(self, 
                         context: RunContext, 
                         vin: Annotated[str, "The VIN of the car."],
                         make: Annotated[str, "The make of the car."],
                         model: Annotated[str, "The model of the car."],
                         year: Annotated[int, "The year of the car."]) -> str:
        """Create a new car entry."""
        logger.info(f"Creating car with VIN: {vin}, Make: {make}, Model: {model}, Year: {year}")
        car = DB.create_car(vin=vin, make=make, model=model, year=year)

        if not car:
            return "Failed to create car. Please check the details and try again."
        
        self._car_details[CarDetails.VIN] = car.vin
        self._car_details[CarDetails.MAKE] = car.make
        self._car_details[CarDetails.MODEL] = car.model
        self._car_details[CarDetails.YEAR] = car.year
        
        return f"Car created successfully: {self.get_car_str()}."
    
    @function_tool()
    def has_car(self):
        """Check if the car details are available."""
        return all(value is not None for value in self._car_details.values())
    
    @function_tool()
    def get_car_details(self) -> str:
        """Get the car details as a string."""
        if not self.has_car():
            return "No car details available."
        
        return self.get_car_str()
    