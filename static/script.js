// Flash message auto-hide
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 3000);
    });

    // Star rating interaction
    const starInputs = document.querySelectorAll('.star-rating input');
    starInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const rating = this.value;
            console.log('Rating selected:', rating);
        });
    });

    // Search form enhancement
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchForm.submit();
            }
        });
    }
});