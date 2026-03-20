document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculatorForm');
    form.addEventListener('submit', handleCalculate);
    const copyButtons = document.querySelectorAll('.btn-copy-callout');
    copyButtons.forEach((button) => {
        button.addEventListener('click', () => copyDrawingCallout(button));
    });

    // Set default values for easier testing
    setPreconfiguredValues();
});

function setPreconfiguredValues() {
    // Optional: Pre-fill with example values for demo
    // Uncomment to enable
    /*
    document.getElementById('majorDiameter').value = '#10';
    document.getElementById('tpi').value = '24';
    document.getElementById('series').value = 'UNC';
    document.getElementById('threadType').value = 'E';
    document.getElementById('minPlating').value = '0.0002';
    document.getElementById('maxPlating').value = '0.0004';
    */
}

async function handleCalculate(event) {
    event.preventDefault();

    const formData = {
        majorDiameter: document.getElementById('majorDiameter').value,
        tpi: document.getElementById('tpi').value,
        series: document.getElementById('series').value,
        threadType: document.getElementById('threadType').value,
        minPlating: document.getElementById('minPlating').value,
        maxPlating: document.getElementById('maxPlating').value
    };

    // Validation
    const validation = validateForm(formData);
    if (!validation.valid) {
        showError(validation.message);
        return;
    }

    // Clear previous error
    hideError();

    // Disable button and show loading state
    const button = document.querySelector('.btn-calculate');
    button.disabled = true;
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculating...';

    try {
        const response = await fetch('/api/tools/un-thread-calculator/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Calculation failed');
        }

        const result = await response.json();
        displayResults(result);
        
        // Scroll to results
        setTimeout(() => {
            document.getElementById('results').scrollIntoView({ behavior: 'smooth' });
        }, 100);

    } catch (error) {
        showError(error.message);
    } finally {
        button.disabled = false;
        button.innerHTML = originalHTML;
    }
}

function validateForm(data) {
    if (!data.majorDiameter.trim()) {
        return { valid: false, message: 'Please enter a major diameter' };
    }

    if (!data.tpi || parseFloat(data.tpi) <= 0) {
        return { valid: false, message: 'TPI must be a positive number' };
    }

    if (!data.series) {
        return { valid: false, message: 'Please select a thread series' };
    }

    if (!data.threadType) {
        return { valid: false, message: 'Please select internal or external' };
    }

    if (data.minPlating === '' || isNaN(parseFloat(data.minPlating))) {
        return { valid: false, message: 'Min plating thickness must be a number' };
    }

    if (data.maxPlating === '' || isNaN(parseFloat(data.maxPlating))) {
        return { valid: false, message: 'Max plating thickness must be a number' };
    }

    const minPlating = parseFloat(data.minPlating);
    const maxPlating = parseFloat(data.maxPlating);

    if (minPlating < 0 || maxPlating < 0) {
        return { valid: false, message: 'Plating thickness cannot be negative' };
    }

    if (maxPlating < minPlating) {
        return { valid: false, message: 'Max plating must be greater than or equal to min plating' };
    }

    return { valid: true };
}

function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    const formData = getCurrentFormData();
    
    // ASME B1.1 Results
    document.getElementById('asme-maj-max').textContent = formatValue(data.asme.majorMax);
    document.getElementById('asme-maj-min').textContent = formatValue(data.asme.majorMin);
    document.getElementById('asme-pitch-max').textContent = formatValue(data.asme.pitchMax);
    document.getElementById('asme-pitch-min').textContent = formatValue(data.asme.pitchMin);
    document.getElementById('asme-minor-max').textContent = formatValue(data.asme.minorMax);
    document.getElementById('asme-minor-min').textContent = formatValue(data.asme.minorMin);

    // Pre-Plate Results
    document.getElementById('plate-maj-max').textContent = formatValue(data.prePlate.majorMax);
    document.getElementById('plate-maj-min').textContent = formatValue(data.prePlate.majorMin);
    document.getElementById('plate-pitch-max').textContent = formatValue(data.prePlate.pitchMax);
    document.getElementById('plate-pitch-min').textContent = formatValue(data.prePlate.pitchMin);
    document.getElementById('plate-minor-max').textContent = formatValue(data.prePlate.minorMax);
    document.getElementById('plate-minor-min').textContent = formatValue(data.prePlate.minorMin);
    document.getElementById('asmeDrawingCallout').value = buildAsmeDrawingCallout(formData, data.asme);
    document.getElementById('prePlateDrawingCallout').value = buildPrePlateDrawingCallout(formData, data.prePlate);
    setCalloutStatus('asmeCalloutCopyStatus', '');
    setCalloutStatus('prePlateCalloutCopyStatus', '');

    resultsDiv.style.display = 'block';
    
    // Hide form for mobile view
    if (window.innerWidth < 768) {
        document.querySelector('.form-section').style.display = 'none';
    }
}

function formatValue(value) {
    if (value === null || value === undefined) {
        return 'N/A';
    }
    return parseFloat(value).toFixed(4);
}

function getCurrentFormData() {
    return {
        majorDiameter: document.getElementById('majorDiameter').value.trim(),
        tpi: document.getElementById('tpi').value,
        series: document.getElementById('series').value.toUpperCase(),
        threadType: document.getElementById('threadType').value,
        minPlating: document.getElementById('minPlating').value,
        maxPlating: document.getElementById('maxPlating').value
    };
}

function formatTpiValue(tpi) {
    const parsed = parseFloat(tpi);
    if (Number.isNaN(parsed)) {
        return tpi;
    }
    return Number.isInteger(parsed) ? String(parsed) : String(parsed);
}

function formatDimensionLine(label, maxValue, minValue, appendRefToMin = false) {
    const maxText = formatValue(maxValue);
    const minText = appendRefToMin ? `${formatValue(minValue)} REF` : formatValue(minValue);
    return `${label}: ${maxText} / ${minText}`;
}

function buildAsmeDrawingCallout(formData, asme) {
    const classSuffix = formData.threadType === 'I' ? 'B' : 'A';
    const header = `${formData.majorDiameter}-${formatTpiValue(formData.tpi)} ${formData.series}-2${classSuffix}`;
    const useMajorRef = formData.threadType === 'I';
    const useMinorRef = formData.threadType === 'E';

    return [
        header,
        formatDimensionLine('MAJOR Ø', asme.majorMax, asme.majorMin, useMajorRef),
        formatDimensionLine('PITCH Ø', asme.pitchMax, asme.pitchMin),
        formatDimensionLine('MINOR Ø', asme.minorMax, asme.minorMin, useMinorRef)
    ].join('\n');
}

function buildPrePlateDrawingCallout(formData, prePlate) {
    const classSuffix = formData.threadType === 'I' ? 'B' : 'A';
    const header = `${formData.majorDiameter}-${formatTpiValue(formData.tpi)} ${formData.series}-2${classSuffix}`;
    const useMajorRef = formData.threadType === 'I';
    const useMinorRef = formData.threadType === 'E';

    return [
        `${header} (ADJUSTED FOR PLATING)`,
        `Adjusted for plating thickness range: ${formatValue(formData.minPlating)} to ${formatValue(formData.maxPlating)} per side`,
        formatDimensionLine('MAJOR Ø', prePlate.majorMax, prePlate.majorMin, useMajorRef),
        formatDimensionLine('PITCH Ø', prePlate.pitchMax, prePlate.pitchMin),
        formatDimensionLine('MINOR Ø', prePlate.minorMax, prePlate.minorMin, useMinorRef)
    ].join('\n');
}

async function copyDrawingCallout(button) {
    const targetId = button?.dataset?.copyTarget;
    const statusId = button?.dataset?.statusTarget;
    const callout = targetId ? document.getElementById(targetId) : null;
    if (!callout || !callout.value.trim()) {
        setCalloutStatus(statusId, 'Run a calculation first.', true);
        return;
    }

    try {
        await navigator.clipboard.writeText(callout.value);
        setCalloutStatus(statusId, 'Callout copied to clipboard.');
    } catch (_error) {
        callout.select();
        document.execCommand('copy');
        setCalloutStatus(statusId, 'Callout copied to clipboard.');
    }
}

function setCalloutStatus(statusId, message, isError = false) {
    const statusEl = document.getElementById(statusId);
    if (!statusEl) {
        return;
    }
    statusEl.textContent = message;
    statusEl.classList.toggle('error', isError);
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    if (errorText) {
        errorText.textContent = message;
    } else {
        errorDiv.textContent = message;
    }
    errorDiv.style.display = 'flex';
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    errorDiv.style.display = 'none';
}

function resetForm() {
    document.getElementById('calculatorForm').reset();
    document.getElementById('results').style.display = 'none';
    document.getElementById('asmeDrawingCallout').value = '';
    document.getElementById('prePlateDrawingCallout').value = '';
    setCalloutStatus('asmeCalloutCopyStatus', '');
    setCalloutStatus('prePlateCalloutCopyStatus', '');
    hideError();
}

// Add some keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Enter to calculate
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        const form = document.getElementById('calculatorForm');
        if (document.activeElement.closest('form')) {
            form.dispatchEvent(new Event('submit'));
        }
    }
});
