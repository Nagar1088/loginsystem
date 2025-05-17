document.addEventListener('DOMContentLoaded', () => {
    const successMsg = document.querySelector('.msg.success');
    const errorMsg = document.querySelector('.msg.error');

    if (successMsg) {
        console.log('Success:', successMsg.textContent);
    }
    if (errorMsg) {
        console.error('Error:', errorMsg.textContent);
    }
});
