from decimal import Decimal

def estimate_fuel_consumption(
    v: float,
    v_optimal_1: float = 60,
    v_optimal_2: float = 70,
    alpha_1: float = 1.6,
    alpha_2: float = 0.9
) -> Decimal:
    """
    Estimate the fuel consumption adjustment factor based on the speed of the vehicle.
    
    Args:
        v (float): The current speed of the vehicle.
        v_optimal_1 (float, optional): Lower optimal speed threshold. Defaults to 60.
        v_optimal_2 (float, optional): Upper optimal speed threshold. Defaults to 70.
        alpha_1 (float, optional): Adjustment coefficient for speeds below v_optimal_1. Defaults to 1.6.
        alpha_2 (float, optional): Adjustment coefficient for speeds above v_optimal_2. Defaults to 0.9.
    
    Returns:
        Decimal: The fuel consumption adjustment factor.
    """
    # Ensure the speed is a float.
    v = float(v)
    if v < v_optimal_1:
        adjustment_factor = 1 + alpha_1 * ((abs(v - v_optimal_1)) ** 2 / v_optimal_1 ** 2)
        return Decimal(adjustment_factor)
    elif v > v_optimal_2:
        adjustment_factor = 1 + alpha_2 * ((abs(v - v_optimal_2)) ** 2 / v_optimal_2 ** 2)
        return Decimal(adjustment_factor)
    else:
        return Decimal("1.0")

def calculate_real_fuel_consumption(driving_conditions: str, fuel_consumption: float) -> float:
    """
    Calculate the adjusted fuel consumption based on driving conditions.
    
    Args:
        driving_conditions (str): The driving condition ("city", "mixed", or "highway").
        fuel_consumption (float): The base fuel consumption value.
    
    Returns:
        float: The adjusted fuel consumption, rounded to 2 decimal places.
    """
    # Define estimated average speeds (in km/h) for different driving conditions.
    driving_speeds = {
        "city": 40,
        "mixed": 60,
        "highway": 90
    }
    speed = driving_speeds.get(driving_conditions, 60)
    adjustment_factor = estimate_fuel_consumption(speed)
    optimal_consumption = fuel_consumption / adjustment_factor
    return round(optimal_consumption, 2)

def calculate_form_fuel_consumption(driving_conditions: str, optimal_fuel_consumption: float) -> float:
    """
    Calculate the fuel consumption stated by the user based on driving conditions and optimal_fuel_consumption.
    
    Args:
        driving_conditions (str): The driving condition ("city", "mixed", or "highway").
        optimal_fuel_consumption (float): The optimal fuel consumption value.
    
    Returns:
        float: The original fuel consumption stated by the user.
    """
    # Define estimated average speeds (in km/h) for different driving conditions.
    driving_speeds = {
        "city": 40,
        "mixed": 60,
        "highway": 90
    }
    speed = driving_speeds.get(driving_conditions, 60)
    adjustment_factor = estimate_fuel_consumption(speed)
    optimal_consumption = optimal_fuel_consumption * adjustment_factor
    return round(optimal_consumption, 2)

def need_refill(fuel_left: float, safety_coeff: float, tank_size: float) -> bool:
    """
    Determine whether a vehicle needs a fuel refill based on current fuel left, a safety coefficient, and tank size.
    
    Args:
        fuel_left (float): The current amount of fuel left.
        safety_coeff (float): The safety coefficient (e.g., 0.1 for 10%).
        tank_size (float): The total fuel tank capacity.
    
    Returns:
        bool: True if a refill is needed; False otherwise.
    """
    return fuel_left <= safety_coeff * tank_size