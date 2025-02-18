function validateAddress(address) {
    // Trim the address to remove leading/trailing whitespaces
    const trimmedAddress = address.trim();

    // Check if the address is empty
    if (!trimmedAddress) {
        alert("Address cannot be empty.");
        return false;
    }

    // Check if the address is too short (you can adjust the length as necessary)
    if (trimmedAddress.length < 5) {
        alert("Address is too short. Please provide a valid address.");
        return false;
    }

    // Basic validation to ensure the address contains letters, numbers, and spaces
    const addressPattern = /^[\p{L}\p{N}\s,.'-]*$/u;


    if (!addressPattern.test(trimmedAddress)) {
        alert("Address contains invalid characters. Only letters, numbers, spaces, and certain punctuation are allowed.");
        return false;
    }


    return true;
}

function validateNumber(value, fieldName) {
    const num = parseFloat(value);
    if (isNaN(num) || !isFinite(num)) {
        alert(`${fieldName} must be a valid number.`);
        return false;
    }
    if (num < 0) {
        alert(`${fieldName} must be a non-negative number.`);
        return false;
    }
    return true;
}



function getFuelInputType() {
    const litersChecked = document.getElementById('id_cur_fuel_liters_check').checked;
    const percentageChecked = document.getElementById('id_cur_fuel_percentage_check').checked;

    if (litersChecked) {
        return 'liters';
    } else if (percentageChecked) {
        return 'percentage';
    } else {
        return null; // Handle the case where neither is checked (optional)
    }
}

function submitform() {
    let form = document.getElementById('load-data-form');

    // Perform client-side validation before submission
    if (!validateForm()) return;

    // Show loading spinner
    document.getElementById("loadingOverlay").style.display = "flex";

    // Submit the form after a short delay for smooth UI
    setTimeout(() => form.submit(), 500);
    setTimeout(() => {
        document.getElementById("loadingOverlay").style.display = "none";
    }, 15000);
}
function validateInputType(fuelInputType, curFuel, curFuelPercentage) {
    // Check for required fuel input based on selected type

    if (fuelInputType === 'liters' && !curFuel) {
        alert("Current fuel is required when 'liters' is selected.");
        return false;
    }
    if (fuelInputType === 'percentage' && !curFuelPercentage) {
        alert("Current fuel percentage is required when 'percentage' is selected.");
        return false;
    }
    return true;
}
function validateFuelAmount(fuelInputType, curFuel, curFuelPercentage, tankSize) {
    // Check if current fuel amount is not higher than tank_size

    if (fuelInputType === 'liters') {
        if (!validateNumber(curFuel, "Current Fuel")) return false;
        if (parseFloat(curFuel) > parseFloat(tankSize)) {
            alert("Current fuel cannot exceed tank size ");
            return false
        }
    }
    if (fuelInputType === 'percentage') {
        if (!validateNumber(curFuelPercentage, "Current fuel percentage")) return false;
        if (parseFloat(curFuelPercentage) > 100) {
            alert("Fuel percentage cannot exceed 100% ");
            return false;
        }
    }
    return true;
}
function validateCondition(drivingCondition) {
    if (!drivingCondition) {
        alert("Driving condition must be checked");
        return false;
    }
    return true;
}
function validateFuelType(fuelType) {
    if (fuelType === null) {
        alert("Please select a fuel input type.");
        return false;
    }
    return true;

}

function validateForm() {
    // Get form data using IDs that match your Django form field IDs.
    const startingAddress = document.getElementById('id_origin_address').value;
    const finishingAddress = document.getElementById('id_destination_address').value;
    const tankSize = document.getElementById('id_tank_size').value;
    const fuelType = document.getElementById('id_fuel_type').value;
    const currency = document.getElementById('id_currency').value;
    const fuelConsumption = document.getElementById('id_fuel_consumption_per_100km').value;
    const priceOfFuel = document.getElementById('id_price_of_fuel').value;
    const fuelInputType = getFuelInputType();
    const curFuel = document.getElementById('id_cur_fuel').value;
    const curFuelPercentage = document.getElementById('id_cur_fuel_percentage').value;
    const drivingCondition =  document.querySelector('input[name="driving_conditions"]:checked');
   
    //Validate
    if (!validateAddress(startingAddress)) return false;
    if (!validateAddress(finishingAddress)) return false;
    if (!validateNumber(tankSize, "Tank Size")) return false;
    if (!validateNumber(fuelConsumption, "Fuel Consumption")) return false;
    if (!validateNumber(priceOfFuel, "Price of Fuel")) return false;
    
    if (!validateCondition(drivingCondition)) return false;
    if (!validateFuelType(fuelType)) return false; 
    if (!validateInputType(fuelInputType, curFuel, curFuelPercentage)) return false;
    if (!validateFuelAmount(fuelInputType, curFuel, curFuelPercentage, tankSize)) return false;



    return true;
}
