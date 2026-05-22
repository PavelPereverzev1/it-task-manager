document.addEventListener('DOMContentLoaded', function () {
    const isManagerSwitch = document.querySelector('input[name="is_manager"]');
    const positionDiv = document.getElementById('div_position');

    if (isManagerSwitch && positionDiv) {
        function togglePosition() {
            if (isManagerSwitch.checked) {
                positionDiv.style.display = 'none';
            } else {
                positionDiv.style.display = 'block';
            }
        }

        isManagerSwitch.addEventListener('change', togglePosition);

        togglePosition();
    }
});