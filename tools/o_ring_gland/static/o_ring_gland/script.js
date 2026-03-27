let crossSections = {};
let latestResult = null;
let latestSuggestions = [];

const DECIMALS = {
    in: 3,
    mm: 2,
};

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('oringForm');
    const sealType = document.getElementById('sealType');
    const unit = document.getElementById('unit');
    const crossSectionFamily = document.getElementById('crossSectionFamily');
    const suggestButton = document.getElementById('suggestButton');
    const reportButton = document.getElementById('reportButton');
    const sampleButton = document.getElementById('sampleButton');
    const resetButton = document.getElementById('resetButton');

    sealType.addEventListener('change', toggleReferenceFields);
    unit.addEventListener('change', handleUnitChange);
    crossSectionFamily.addEventListener('change', syncCrossSectionFromFamily);
    suggestButton.addEventListener('click', handleSuggestSizes);
    reportButton.addEventListener('click', handleGenerateReport);
    sampleButton.addEventListener('click', loadSample);
    resetButton.addEventListener('click', resetUI);
    form.addEventListener('submit', handleCalculate);

    initCrossSections();
    toggleReferenceFields();
    document.getElementById('reportDate').value = new Date().toISOString().slice(0, 10);
});

function currentUnit() {
    return document.getElementById('unit').value;
}

function unitSymbol() {
    return currentUnit() === 'mm' ? 'mm' : 'in';
}

function handleUnitChange() {
    renderCrossSectionOptions();
    document.getElementById('suggestionsPanel').style.display = 'none';
    document.getElementById('resultsPanel').style.display = 'none';
}

async function initCrossSections() {
    try {
        const response = await fetch('/api/tools/o-ring-gland-calculator/cross-sections');
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load cross-section families');
        }

        crossSections = data;
        renderCrossSectionOptions();
        syncCrossSectionFromFamily();
    } catch (error) {
        showError(error.message || 'Failed to load cross-section list.');
    }
}

function renderCrossSectionOptions() {
    const select = document.getElementById('crossSectionFamily');
    const selected = select.value;

    select.innerHTML = '<option value="">Select</option>';

    const entries = Object.entries(crossSections).sort((a, b) => a[0].localeCompare(b[0]));
    entries.forEach(([key, value]) => {
        const csValue = currentUnit() === 'mm' ? value.cross_section_mm : value.cross_section_in;
        const option = document.createElement('option');
        option.value = key;
        option.textContent = `${key.toUpperCase()} (${toFixed(csValue, DECIMALS[currentUnit()])} ${unitSymbol()})`;
        select.appendChild(option);
    });

    if (selected) {
        select.value = selected;
    }
}

function toggleReferenceFields() {
    const sealTypeValue = document.getElementById('sealType').value;
    const boreField = document.getElementById('boreField');
    const rodField = document.getElementById('rodField');
    const boreInput = document.getElementById('boreDiameter');
    const boreTolInput = document.getElementById('boreDiameterTol');
    const rodInput = document.getElementById('rodDiameter');
    const rodTolInput = document.getElementById('rodDiameterTol');

    if (sealTypeValue === 'piston') {
        boreField.style.display = 'block';
        rodField.style.display = 'none';
        boreInput.required = true;
        boreTolInput.required = true;
        rodInput.required = false;
        rodTolInput.required = false;
    } else if (sealTypeValue === 'rod') {
        boreField.style.display = 'none';
        rodField.style.display = 'block';
        boreInput.required = false;
        boreTolInput.required = false;
        rodInput.required = true;
        rodTolInput.required = true;
    } else {
        boreField.style.display = 'none';
        rodField.style.display = 'none';
        boreInput.required = false;
        boreTolInput.required = false;
        rodInput.required = false;
        rodTolInput.required = false;
    }
}

function syncCrossSectionFromFamily() {
    const family = document.getElementById('crossSectionFamily').value;
    if (!family || !crossSections[family]) {
        return;
    }
    const cs = currentUnit() === 'mm' ? crossSections[family].cross_section_mm : crossSections[family].cross_section_in;
    document.getElementById('selectedOringCs').value = toFixed(cs, DECIMALS[currentUnit()]);
}

function validateSetupInputs() {
    const sealType = document.getElementById('sealType').value;
    const serviceType = document.getElementById('serviceType').value;
    const crossSectionFamily = document.getElementById('crossSectionFamily').value;
    const boreDiameter = parseFloat(document.getElementById('boreDiameter').value);
    const boreDiameterTol = parseFloat(document.getElementById('boreDiameterTol').value);
    const rodDiameter = parseFloat(document.getElementById('rodDiameter').value);
    const rodDiameterTol = parseFloat(document.getElementById('rodDiameterTol').value);

    if (!sealType) {
        return 'Select a seal type.';
    }
    if (!serviceType) {
        return 'Select a service type.';
    }
    if (!crossSectionFamily) {
        return 'Select a cross-section family.';
    }

    if (sealType === 'piston' && (!Number.isFinite(boreDiameter) || boreDiameter <= 0)) {
        return `Bore ID must be greater than zero (${unitSymbol()}).`;
    }
    if (sealType === 'piston' && (!Number.isFinite(boreDiameterTol) || boreDiameterTol < 0)) {
        return `Bore ID tolerance must be zero or positive (${unitSymbol()}).`;
    }

    if (sealType === 'rod' && (!Number.isFinite(rodDiameter) || rodDiameter <= 0)) {
        return `Shaft OD must be greater than zero (${unitSymbol()}).`;
    }
    if (sealType === 'rod' && (!Number.isFinite(rodDiameterTol) || rodDiameterTol < 0)) {
        return `Shaft OD tolerance must be zero or positive (${unitSymbol()}).`;
    }

    return null;
}

function setupPayload() {
    return {
        unit: currentUnit(),
        sealType: document.getElementById('sealType').value,
        serviceType: document.getElementById('serviceType').value,
        crossSectionFamily: document.getElementById('crossSectionFamily').value,
        boreDiameter: parseFloat(document.getElementById('boreDiameter').value),
        boreDiameterTol: parseFloat(document.getElementById('boreDiameterTol').value),
        rodDiameter: parseFloat(document.getElementById('rodDiameter').value),
        rodDiameterTol: parseFloat(document.getElementById('rodDiameterTol').value),
    };
}

async function handleSuggestSizes() {
    const validationError = validateSetupInputs();
    if (validationError) {
        showError(validationError);
        return;
    }

    hideError();
    setSuggestBusy(true);

    try {
        const response = await fetch('/api/tools/o-ring-gland-calculator/suggest-sizes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(setupPayload()),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to suggest sizes');
        }

        renderSuggestions(data.result);
    } catch (error) {
        showError(error.message || 'Failed to suggest sizes');
    } finally {
        setSuggestBusy(false);
    }
}

function renderSuggestions(result) {
    const panel = document.getElementById('suggestionsPanel');
    const list = document.getElementById('suggestionsList');
    const note = document.getElementById('suggestionNote');

    list.innerHTML = '';

    note.textContent = `Recommended groove dia: ${toDim(result.recommended_geometry.recommended_groove_diameter)} | Suggested groove width: ${toDim(result.recommended_geometry.suggested_groove_width)}`;
    latestSuggestions = Array.isArray(result.suggestions) ? result.suggestions : [];

    result.suggestions.forEach((item, index) => {
        const card = document.createElement('button');
        card.type = 'button';
        card.className = 'suggestion-item';

        card.innerHTML = `
            <span class="suggestion-main">AS568 ${item.dash_size} | ID ${toDim(item.nominal_id)} | CS ${toDim(item.cross_section)}</span>
            <span class="suggestion-sub">Predicted stretch: ${toFixed(item.predicted_stretch_percent, 2)}%</span>
        `;

        card.addEventListener('click', () => {
            applySuggestion(item, result);
            highlightSelectedSuggestion(card);
        });

        if (index === 1 || (index === 0 && result.suggestions.length === 1)) {
            card.classList.add('top-pick');
        }

        list.appendChild(card);
    });

    panel.style.display = 'block';
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    if (result.suggestions.length > 0) {
        const centerIndex = result.suggestions.length === 3 ? 1 : 0;
        applySuggestion(result.suggestions[centerIndex], result);
        const defaultCard = list.children[centerIndex];
        if (defaultCard) {
            highlightSelectedSuggestion(defaultCard);
        }
    }
}

function highlightSelectedSuggestion(selectedCard) {
    document.querySelectorAll('#suggestionsList .suggestion-item').forEach((card) => {
        card.classList.remove('selected');
    });
    selectedCard.classList.add('selected');
}

function applySuggestion(item, result) {
    document.getElementById('selectedDash').value = item.dash_size;
    document.getElementById('selectedOringId').value = toFixed(item.nominal_id, DECIMALS[currentUnit()]);
    document.getElementById('selectedOringCs').value = toFixed(item.cross_section, DECIMALS[currentUnit()]);

    document.getElementById('grooveDiameter').value = toFixed(result.recommended_geometry.recommended_groove_diameter, currentUnit() === 'in' ? 3 : 2);
    document.getElementById('grooveWidth').value = toFixed(result.recommended_geometry.suggested_groove_width, DECIMALS[currentUnit()]);

    document.getElementById('grooveDiameterTol').value = toFixed(result.suggested_tolerances.groove_diameter_tol, DECIMALS[currentUnit()]);
    document.getElementById('grooveWidthTol').value = toFixed(result.suggested_tolerances.groove_width_tol, DECIMALS[currentUnit()]);
    document.getElementById('oRingCsTol').value = toFixed(result.suggested_tolerances.o_ring_cs_tol, DECIMALS[currentUnit()]);
    const refTol = toFixed(result.suggested_tolerances.reference_diameter_tol, DECIMALS[currentUnit()]);
    if (document.getElementById('sealType').value === 'piston') {
        document.getElementById('boreDiameterTol').value = refTol;
    } else if (document.getElementById('sealType').value === 'rod') {
        document.getElementById('rodDiameterTol').value = refTol;
    }
}

function analysisPayload() {
    return {
        unit: currentUnit(),
        sealType: document.getElementById('sealType').value,
        serviceType: document.getElementById('serviceType').value,
        crossSectionFamily: document.getElementById('crossSectionFamily').value,
        oRingId: parseFloat(document.getElementById('selectedOringId').value),
        oRingCs: parseFloat(document.getElementById('selectedOringCs').value),
        oRingCsTol: parseFloat(document.getElementById('oRingCsTol').value),
        grooveWidth: parseFloat(document.getElementById('grooveWidth').value),
        grooveWidthTol: parseFloat(document.getElementById('grooveWidthTol').value),
        grooveDiameter: parseFloat(document.getElementById('grooveDiameter').value),
        grooveDiameterTol: parseFloat(document.getElementById('grooveDiameterTol').value),
        boreDiameter: parseFloat(document.getElementById('boreDiameter').value),
        boreDiameterTol: parseFloat(document.getElementById('boreDiameterTol').value),
        rodDiameter: parseFloat(document.getElementById('rodDiameter').value),
        rodDiameterTol: parseFloat(document.getElementById('rodDiameterTol').value),
        referenceDiameterTol: document.getElementById('sealType').value === 'piston'
            ? parseFloat(document.getElementById('boreDiameterTol').value)
            : parseFloat(document.getElementById('rodDiameterTol').value),
    };
}

function validateAnalysisPayload(payload) {
    const numericChecks = [
        ['Selected O-ring ID', payload.oRingId],
        ['Selected O-ring cross-section', payload.oRingCs],
        ['O-ring CS tolerance', payload.oRingCsTol],
        ['Groove width', payload.grooveWidth],
        ['Groove width tolerance', payload.grooveWidthTol],
        ['Groove diameter', payload.grooveDiameter],
        ['Groove diameter tolerance', payload.grooveDiameterTol],
    ];

    if (payload.sealType === 'piston') {
        numericChecks.push(['Bore ID', payload.boreDiameter]);
        numericChecks.push(['Bore ID tolerance', payload.boreDiameterTol]);
    }
    if (payload.sealType === 'rod') {
        numericChecks.push(['Shaft OD', payload.rodDiameter]);
        numericChecks.push(['Shaft OD tolerance', payload.rodDiameterTol]);
    }

    for (const [label, value] of numericChecks) {
        if (!Number.isFinite(value) || value < 0 || (label.indexOf('tolerance') < 0 && value <= 0)) {
            return `${label} is invalid.`;
        }
    }

    return null;
}

async function handleCalculate(event) {
    event.preventDefault();

    const setupError = validateSetupInputs();
    if (setupError) {
        showError(setupError);
        return;
    }

    const payload = analysisPayload();
    const validationError = validateAnalysisPayload(payload);
    if (validationError) {
        showError(validationError);
        return;
    }

    hideError();
    setCalcBusy(true);

    try {
        const response = await fetch('/api/tools/o-ring-gland-calculator/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Calculation failed');
        }

        renderResults(data.result);
    } catch (error) {
        showError(error.message || 'Calculation failed');
    } finally {
        setCalcBusy(false);
    }
}

function renderResults(result) {
    latestResult = result;
    document.getElementById('radialDepth').textContent = toDim(result.radial_gland_depth);
    document.getElementById('squeeze').textContent = `${toFixed(result.squeeze_percent, 2)} %`;
    document.getElementById('stretch').textContent = `${toFixed(result.stretch_percent, 2)} %`;
    document.getElementById('fill').textContent = `${toFixed(result.fill_percent, 2)} %`;

    document.getElementById('squeezeRange').textContent = `${toFixed(result.squeeze_min_percent, 2)}% to ${toFixed(result.squeeze_max_percent, 2)}%`;
    document.getElementById('stretchRange').textContent = `${toFixed(result.stretch_min_percent, 2)}% to ${toFixed(result.stretch_max_percent, 2)}%`;
    document.getElementById('fillRange').textContent = `${toFixed(result.fill_min_percent, 2)}% to ${toFixed(result.fill_max_percent, 2)}%`;

    document.getElementById('targetSqueeze').textContent = `${toFixed(result.target_squeeze_percent, 2)} %`;
    document.getElementById('targetFill').textContent = `${toFixed(result.target_fill_percent, 2)} %`;
    document.getElementById('recDepth').textContent = toDim(result.recommended_gland_depth);
    document.getElementById('recWidth').textContent = toDim(result.recommended_groove_width_min);
    document.getElementById('recGrooveDia').textContent = toDim(result.recommended_groove_diameter);

    const warningCard = document.getElementById('warningCard');
    const warningList = document.getElementById('warningList');
    warningList.innerHTML = '';

    if (Array.isArray(result.warnings) && result.warnings.length) {
        result.warnings.forEach((warning) => {
            const li = document.createElement('li');
            li.textContent = warning;
            warningList.appendChild(li);
        });
        warningCard.style.display = 'block';
    } else {
        warningCard.style.display = 'none';
    }

    document.getElementById('resultsPanel').style.display = 'block';
    document.getElementById('resultsPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function handleGenerateReport() {
    if (!latestResult) {
        showError('Run a calculation before generating a report.');
        return;
    }

    const payload = analysisPayload();
    const validationError = validateAnalysisPayload(payload);
    if (validationError) {
        showError(validationError);
        return;
    }

    hideError();
    const reportButton = document.getElementById('reportButton');
    reportButton.disabled = true;
    const originalText = reportButton.innerHTML;
    reportButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Building Report...';

    try {
        const formData = new FormData();
        formData.append('reportId', document.getElementById('reportId').value || '');
        formData.append('analyst', document.getElementById('analyst').value || '');
        formData.append('reportDate', document.getElementById('reportDate').value || '');
        formData.append('unit', currentUnit());
        formData.append('inputsJson', JSON.stringify(payload));
        formData.append('resultsJson', JSON.stringify(latestResult));
        formData.append('suggestionsJson', JSON.stringify(latestSuggestions));

        const fileInput = document.getElementById('reportImage');
        if (fileInput.files && fileInput.files[0]) {
            formData.append('reportImage', fileInput.files[0]);
        }

        const response = await fetch('/api/tools/o-ring-gland-calculator/report', {
            method: 'POST',
            body: formData,
        });

        const html = await response.text();
        if (!response.ok) {
            throw new Error('Failed to generate report.');
        }

        const reportWindow = window.open('', '_blank');
        if (!reportWindow) {
            throw new Error('Popup blocked. Allow popups to open report.');
        }
        reportWindow.document.open();
        reportWindow.document.write(html);
        reportWindow.document.close();
    } catch (error) {
        showError(error.message || 'Failed to generate report.');
    } finally {
        reportButton.disabled = false;
        reportButton.innerHTML = originalText;
    }
}

function setSuggestBusy(isBusy) {
    const btn = document.getElementById('suggestButton');
    if (isBusy) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Suggesting...';
    } else {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-lightbulb"></i> Suggest Standard Sizes';
    }
}

function setCalcBusy(isBusy) {
    const btn = document.getElementById('calcButton');
    if (isBusy) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
    } else {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-calculator"></i> Analyze Gland';
    }
}

function toFixed(value, decimals) {
    const n = Number(value);
    return Number.isFinite(n) ? n.toFixed(decimals) : '-';
}

function toDim(value) {
    return `${toFixed(value, DECIMALS[currentUnit()])} ${unitSymbol()}`;
}

function showError(message) {
    const banner = document.getElementById('errorBanner');
    banner.textContent = message;
    banner.style.display = 'block';
}

function hideError() {
    const banner = document.getElementById('errorBanner');
    banner.style.display = 'none';
    banner.textContent = '';
}

function resetUI() {
    document.getElementById('oringForm').reset();
    document.getElementById('resultsPanel').style.display = 'none';
    document.getElementById('suggestionsPanel').style.display = 'none';
    document.getElementById('suggestionsList').innerHTML = '';
    document.getElementById('selectedDash').value = '';
    latestResult = null;
    latestSuggestions = [];
    hideError();
    toggleReferenceFields();
    renderCrossSectionOptions();
    document.getElementById('reportDate').value = new Date().toISOString().slice(0, 10);
}

function loadSample() {
    resetUI();
    document.getElementById('unit').value = 'in';
    renderCrossSectionOptions();
    document.getElementById('sealType').value = 'piston';
    document.getElementById('serviceType').value = 'dynamic';
    document.getElementById('crossSectionFamily').value = '2xx';
    document.getElementById('boreDiameter').value = '2.000';
    document.getElementById('boreDiameterTol').value = '0.003';
    toggleReferenceFields();
    syncCrossSectionFromFamily();
}
