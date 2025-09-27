const API_BASE = 'http://localhost:5001/api';
let currentUser = null;

// Utility functions
function showFlashMessage(message, type = 'info') {
    const flashDiv = document.getElementById('flashMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flash-message';
    messageDiv.textContent = message;
    flashDiv.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
}

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.style.display = 'none');
    document.getElementById(pageId).style.display = 'block';
}

function updateNavigation() {
    const navLinks = document.getElementById('navLinks');
    if (currentUser) {
        navLinks.innerHTML = `
            <a href="#" onclick="showProfile()">Profile</a>
            <a href="#" onclick="logout()">Logout</a>
            <span class="user-email">${currentUser.email}</span>
        `;
    } else {
        navLinks.innerHTML = `
            <a href="#" onclick="showLogin()">Login</a>
            <a href="#" onclick="showRegister()">Register</a>
        `;
    }
}

function renderStars(rating) {
    if (!rating) return '<span class="no-rating">No reviews yet</span>';
    const stars = '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
    return `<span class="stars">${stars}</span> <span class="rating-text">${rating.toFixed(1)}</span>`;
}

// API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        showFlashMessage('Network error occurred', 'error');
        return null;
    }
}

// Authentication
async function login(event) {
    event.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    const result = await apiCall('/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
    
    if (result && result.success) {
        currentUser = result.user;
        updateNavigation();
        showFlashMessage('Login successful!');
        showHome();
    } else {
        showFlashMessage(result?.message || 'Login failed', 'error');
    }
}

async function register(event) {
    event.preventDefault();
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    const result = await apiCall('/register', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
    
    if (result && result.success) {
        showFlashMessage('Registration successful! Please login.');
        showLogin();
    } else {
        showFlashMessage(result?.message || 'Registration failed', 'error');
    }
}

async function logout() {
    await apiCall('/logout', { method: 'POST' });
    currentUser = null;
    updateNavigation();
    showFlashMessage('Logged out successfully');
    showHome();
}

// Page navigation
function showHome() {
    showPage('homePage');
    loadRecommendations();
    loadCourses();
}

function showLogin() {
    showPage('loginPage');
}

function showRegister() {
    showPage('registerPage');
}

async function showProfile() {
    if (!currentUser) {
        showLogin();
        return;
    }
    
    showPage('profilePage');
    document.getElementById('profileEmail').textContent = currentUser.email;
    
    const reviews = await apiCall('/user/reviews');
    const reviewsDiv = document.getElementById('userReviews');
    
    if (reviews && reviews.length > 0) {
        reviewsDiv.innerHTML = reviews.map(review => `
            <div class="user-review">
                <h4>${review.course_name}</h4>
                <div class="review-rating">${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}</div>
                <p class="review-text">${review.review_text}</p>
                <span class="review-date">${review.created_at.substring(0, 10)}</span>
            </div>
        `).join('');
    } else {
        reviewsDiv.innerHTML = '<p class="no-reviews">You haven\'t written any reviews yet.</p>';
    }
}

// Course functions
async function loadRecommendations() {
    const recommendations = await apiCall('/recommendations');
    if (!recommendations) return;
    
    const topRatedDiv = document.getElementById('topRated');
    const mostReviewedDiv = document.getElementById('mostReviewed');
    
    topRatedDiv.innerHTML = recommendations.top_rated.map(course => `
        <div class="course-card">
            <h3><a href="#" onclick="showCourseDetail(${course.id})">${course.course_name}</a></h3>
            <p class="provider">${course.provider}</p>
            <div class="rating">${renderStars(course.avg_rating)} (${course.review_count} reviews)</div>
        </div>
    `).join('');
    
    mostReviewedDiv.innerHTML = recommendations.most_reviewed.map(course => `
        <div class="course-card">
            <h3><a href="#" onclick="showCourseDetail(${course.id})">${course.course_name}</a></h3>
            <p class="provider">${course.provider}</p>
            <div class="rating">${renderStars(course.avg_rating)} (${course.review_count} reviews)</div>
        </div>
    `).join('');
}

async function loadCourses(search = '') {
    const courses = await apiCall(`/courses${search ? `?search=${encodeURIComponent(search)}` : ''}`);
    if (!courses) return;
    
    const coursesDiv = document.getElementById('coursesList');
    const titleDiv = document.getElementById('coursesTitle');
    
    titleDiv.textContent = search ? `Search Results for "${search}"` : 'All Courses';
    
    coursesDiv.innerHTML = courses.map(course => `
        <div class="course-item">
            <h3><a href="#" onclick="showCourseDetail(${course.id})">${course.course_name}</a></h3>
            <p class="provider">${course.provider}</p>
            <div class="rating">${renderStars(course.avg_rating)} (${course.review_count} reviews)</div>
        </div>
    `).join('');
}

async function searchCourses(event) {
    event.preventDefault();
    const search = document.getElementById('searchInput').value;
    await loadCourses(search);
}

async function showCourseDetail(courseId) {
    const courseData = await apiCall(`/courses/${courseId}`);
    if (!courseData) return;
    
    const { course, avg_rating, review_count, reviews } = courseData;
    
    const courseDetailDiv = document.getElementById('courseDetail');
    courseDetailDiv.innerHTML = `
        <div class="course-header">
            <h1>${course.course_name}</h1>
            <p class="provider">Provider: ${course.provider}</p>
            <div class="course-rating">${renderStars(avg_rating)} (${review_count} reviews)</div>
            <p class="description">${course.description}</p>
            <a href="${course.course_url}" target="_blank" class="course-link">Visit Course</a>
        </div>

        ${currentUser ? `
        <div class="review-form">
            <h3>Write a Review</h3>
            <form onsubmit="submitReview(event, ${course.id})">
                <div class="rating-input">
                    <label>Rating:</label>
                    <div class="star-rating">
                        <input type="radio" name="rating" value="5" id="star5">
                        <label for="star5">★</label>
                        <input type="radio" name="rating" value="4" id="star4">
                        <label for="star4">★</label>
                        <input type="radio" name="rating" value="3" id="star3">
                        <label for="star3">★</label>
                        <input type="radio" name="rating" value="2" id="star2">
                        <label for="star2">★</label>
                        <input type="radio" name="rating" value="1" id="star1">
                        <label for="star1">★</label>
                    </div>
                </div>
                <textarea name="review_text" placeholder="Write your review here..." required></textarea>
                <button type="submit">Submit Review</button>
            </form>
        </div>
        ` : `
        <div class="login-prompt">
            <p><a href="#" onclick="showLogin()">Login</a> to write a review</p>
        </div>
        `}

        <div class="reviews-section">
            <h3>Reviews</h3>
            ${reviews.length > 0 ? reviews.map(review => `
                <div class="review">
                    <div class="review-header">
                        <span class="reviewer">${review.email}</span>
                        <span class="review-rating">${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}</span>
                        <span class="review-date">${review.created_at.substring(0, 10)}</span>
                    </div>
                    <p class="review-text">${review.review_text}</p>
                </div>
            `).join('') : '<p class="no-reviews">No reviews yet. Be the first to review this course!</p>'}
        </div>
    `;
    
    showPage('courseDetailPage');
}

async function submitReview(event, courseId) {
    event.preventDefault();
    
    const rating = document.querySelector('input[name="rating"]:checked')?.value;
    const reviewText = document.querySelector('textarea[name="review_text"]').value;
    
    if (!rating) {
        showFlashMessage('Please select a rating', 'error');
        return;
    }
    
    const result = await apiCall('/reviews', {
        method: 'POST',
        body: JSON.stringify({
            course_id: courseId,
            rating: parseInt(rating),
            review_text: reviewText
        })
    });
    
    if (result && result.success) {
        showFlashMessage('Review submitted successfully!');
        showCourseDetail(courseId); // Refresh the page
    } else {
        showFlashMessage(result?.message || 'Failed to submit review', 'error');
    }
}

// Initialize app
async function init() {
    const user = await apiCall('/user');
    if (user && user.user) {
        currentUser = user.user;
    }
    updateNavigation();
    showHome();
}

// Start the app
document.addEventListener('DOMContentLoaded', init);