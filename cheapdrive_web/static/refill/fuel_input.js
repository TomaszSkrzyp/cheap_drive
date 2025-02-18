// Get references to the checkboxes, inputs, and visualisation element
const litersCheckbox = document.getElementById('id_cur_fuel_liters_check');
const litersInput = document.getElementById('id_cur_fuel');
const percentageCheckbox = document.getElementById('id_cur_fuel_percentage_check');
const percentageInput = document.getElementById('id_cur_fuel_percentage');
const fuelAmountDisplay = document.getElementById('fuel-amount-display');


// Function to update the visibility of the visualisation
function toggleVisualisation() {
    fuelAmountDisplay.style.display = percentageCheckbox.checked ? 'inline' : 'none';
}

// Function to update inputs and ensure mutual exclusivity
function updateCheckboxesAndInputs(changedCheckbox) {
    if (changedCheckbox === litersCheckbox ) {
        litersCheckbox.checked = true;
        percentageCheckbox.checked = false; // Uncheck the other checkbox
    } else if (changedCheckbox === percentageCheckbox ) {
        litersCheckbox.checked = false; // Uncheck the other checkbox
        percentageCheckbox.checked = true;
    }

    // Enable or disable inputs based on the checkboxes
    litersInput.disabled = !litersCheckbox.checked;
    percentageInput.disabled = !percentageCheckbox.checked;

    // Clear the value of the disabled input
    if (litersInput.disabled) litersInput.value = '';
    if (percentageInput.disabled) percentageInput.value = '';

    toggleVisualisation();
}

// Function to initialize the state of checkboxes and inputs
function initializeCheckboxes() {
    // Set the default state on page load
    litersCheckbox.checked = true;
    percentageCheckbox.checked = false;

    updateCheckboxesAndInputs(litersCheckbox);
}

// Event listener for liters checkbox
litersCheckbox.addEventListener('change', () => updateCheckboxesAndInputs(litersCheckbox));

// Event listener for percentage checkbox
percentageCheckbox.addEventListener('change', () => updateCheckboxesAndInputs(percentageCheckbox));

// Initialize on page load
initializeCheckboxes();
