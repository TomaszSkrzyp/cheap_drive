const tankSizeInput = document.getElementById('id_tank_size');

function updateFuelAmountDisplay() {
    const tankSize = parseFloat(tankSizeInput.value) || 0;
    const percentage = parseFloat(percentageInput.value) || 0;
    const fuelAmount = (percentage / 100) * tankSize;
    fuelAmountDisplay.textContent = fuelAmount.toFixed(2);
}

percentageInput.addEventListener('input', updateFuelAmountDisplay);
tankSizeInput.addEventListener('input', updateFuelAmountDisplay);
