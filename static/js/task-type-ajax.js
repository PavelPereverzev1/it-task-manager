document.addEventListener('DOMContentLoaded', function () {
    const saveBtn = document.getElementById('save-task-type-btn');
    const modalEl = document.getElementById('addTaskTypeModal');

    if (!saveBtn) return;

    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', function () {
            const typeNameInput = document.getElementById('modal_task_type_name');
            const errorBlock = document.getElementById('modal-error-block');

            if (typeNameInput) {
                typeNameInput.value = '';
            }

            if (errorBlock) {
                errorBlock.textContent = '';
                errorBlock.classList.add('d-none');
            }
        });
    }
    
    saveBtn.addEventListener('click', function () {
        const typeNameInput = document.getElementById('modal_task_type_name');
        const typeName = typeNameInput.value.trim();
        const errorBlock = document.getElementById('modal-error-block');

        const csrfEl = document.querySelector('#ajax-task-type-form [name=csrfmiddlewaretoken]');
        const csrfToken = csrfEl ? csrfEl.value : '';

        errorBlock.classList.add('d-none');
        errorBlock.textContent = '';

        if (!typeName) {
            errorBlock.textContent = "Please, enter a type name.";
            errorBlock.classList.remove('d-none');
            return;
        }

        const formData = new FormData();
        formData.append('name', typeName);
        formData.append('csrfmiddlewaretoken', csrfToken);

        const url = saveBtn.getAttribute('data-url');

        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                return response.json().then(data => {
                    return {status: response.status, body: data};
                });
            })
            .then(res => {
                if (res.status === 201) {
                    const selectTaskType = document.getElementById('id_task_type');
                    const newOption = new Option(res.body.name, res.body.id, true, true);
                    selectTaskType.add(newOption);

                    typeNameInput.value = '';
                    const modal = bootstrap.Modal.getInstance(modalEl);
                    modal.hide();
                } else {
                    let textError = "Task type with this Name already exists.";
                    if (res.body && res.body.error) {
                        textError = res.body.error;
                    }

                    errorBlock.textContent = textError;
                    errorBlock.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Критическая ошибка JS:', error);
                errorBlock.textContent = "Something went wrong. Try again.";
                errorBlock.classList.remove('d-none');
            });
    });
});