/**
 * Custom Multi-Select Component
 * Converts regular select elements with data-select2="true" to custom multi-select dropdowns
 */

function initializeCustomMultiSelect() {
    $('select[data-select2="true"]:not(.custom-multiselect-initialized)').each(function () {
        const $select = $(this);
        const placeholder = $select.attr('data-placeholder') || 'Select options...';
        const originalClasses = $select.attr('class') || '';

        // Mark as initialized
        $select.addClass('custom-multiselect-initialized');

        // Hide original select
        $select.hide();

        // Create custom multi-select container
        const $container = $(`
            <div class="custom-multiselect">
                <div class="multiselect-input ${originalClasses}">
                    <input type="text" class="multiselect-search" placeholder="${placeholder}">
                </div>
                <div class="multiselect-dropdown">
                </div>
            </div>
        `);

        // Insert after original select
        $select.after($container);

        const $input = $container.find('.multiselect-search');
        const $dropdown = $container.find('.multiselect-dropdown');
        const $inputContainer = $container.find('.multiselect-input');

        // Populate dropdown with options
        $select.find('option').each(function () {
            const $option = $(this);
            const value = $option.val();
            const text = $option.text();

            if (value) {
                $dropdown.append(`
                    <div class="multiselect-option" data-value="${value}">
                        ${text}
                    </div>
                `);
            }
        });

        // Handle pre-selected values from form data
        const fieldName = $select.attr('name');
        let selectedValues = [];

        // Try to get selected values from the select element's data attribute
        const dataSelected = $select.data('selected');

        if (dataSelected) {
            if (typeof dataSelected === 'string' && dataSelected !== '') {
                selectedValues = dataSelected.split(',').filter(val => val !== '');
            } else if (Array.isArray(dataSelected)) {
                selectedValues = dataSelected;
            } else if (dataSelected !== '') {
                selectedValues = [dataSelected.toString()];
            }
        }

        // Apply the selected values
        selectedValues.forEach(function (value) {
            const $option = $select.find(`option[value="${value}"]`);
            if ($option.length > 0) {
                const text = $option.text();

                // Mark option as selected
                $option.prop('selected', true);
                $dropdown.find(`[data-value="${value}"]`).addClass('selected');

                // Add tag
                const $tag = $(`
                    <span class="multiselect-tag">
                        ${text}
                        <button type="button" data-value="${value}">×</button>
                    </span>
                `);
                $input.before($tag);
            }
        });

        // Show/hide dropdown
        $input.on('focus', function () {
            $dropdown.addClass('show');
        });

        $(document).on('click', function (e) {
            if (!$container[0].contains(e.target)) {
                $dropdown.removeClass('show');
            }
        });

        // Handle option selection
        $dropdown.on('click', '.multiselect-option', function () {
            const $option = $(this);
            const value = $option.data('value');
            const text = $option.text();

            if (!$option.hasClass('selected')) {
                // Add selection
                $option.addClass('selected');

                // Add tag
                const $tag = $(`
                    <span class="multiselect-tag">
                        ${text}
                        <button type="button" data-value="${value}">×</button>
                    </span>
                `);

                $input.before($tag);

                // Update original select
                $select.find(`option[value="${value}"]`).prop('selected', true);
                $select.trigger('change');

                // Manually trigger HTMX request
                triggerHTMXFilter();
            }

            $input.val('').focus();
        });

        // Handle tag removal
        $inputContainer.on('click', '.multiselect-tag button', function (e) {
            e.preventDefault();
            const value = $(this).data('value');

            // Remove tag
            $(this).parent().remove();

            // Update dropdown
            $dropdown.find(`[data-value="${value}"]`).removeClass('selected');

            // Update original select
            $select.find(`option[value="${value}"]`).prop('selected', false);
            $select.trigger('change');

            // Manually trigger HTMX request
            triggerHTMXFilter();
        });

        // Search functionality
        $input.on('input', function () {
            const search = $(this).val().toLowerCase();

            $dropdown.find('.multiselect-option').each(function () {
                const text = $(this).text().toLowerCase();
                $(this).toggle(text.includes(search));
            });
        });
    });
}

// Initialize when document is ready
$(document).ready(function () {
    initializeCustomMultiSelect();

    // Re-initialize after HTMX swaps
    document.body.addEventListener('htmx:afterSwap', function () {
        setTimeout(initializeCustomMultiSelect, 50);
    });
});

// Function to manually trigger HTMX filter request
function triggerHTMXFilter() {
    // Find the filter row and get its HTMX attributes
    const $filterRow = $('tr[hx-post]');
    if ($filterRow.length > 0) {
        // Use setTimeout to debounce the request
        clearTimeout(window.htmxFilterTimeout);
        window.htmxFilterTimeout = setTimeout(function () {
            // Collect form data from all filter inputs
            const formData = {};

            // Add text filter values
            $('[name="code"]').each(function () {
                if (this.value) formData.code = this.value;
            });
            $('[name="name"]').each(function () {
                if (this.value) formData.name = this.value;
            });

            // Add multi-select values
            formData.categories = [];
            $('[name="categories"]').each(function () {
                $(this).find('option:selected').each(function () {
                    if (this.value) formData.categories.push(this.value);
                });
            });

            formData.suppliers = [];
            $('[name="suppliers"]').each(function () {
                $(this).find('option:selected').each(function () {
                    if (this.value) formData.suppliers.push(this.value);
                });
            });

            // Make the HTMX request
            htmx.ajax('POST', $filterRow.attr('hx-post'), {
                values: formData,
                target: '#product-list',
                swap: 'outerHTML'
            });
        }, 250);
    }
}
