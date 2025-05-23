const originalMovies = window.originalMovies || [];
const userRatings = window.userRatings || [];
const isAuthenticated = window.isAuthenticated || false;

let movies = [...originalMovies];
let filteredMovies = [...originalMovies];
let currentIndex = 0;
const moviesPerPage = 8;

// Отримати оцінку користувача для певного фільму
function getUserRating(movieId) {
    const rating = userRatings.find(r => r.movie_id === movieId);
    return rating ? rating.rating : null;
}

// Функція для оновлення списку фільмів
function renderMovies(reset = false) {
    const movieList = document.getElementById('movie-list');
    if (reset) {
        movieList.innerHTML = '';
        currentIndex = 0;
    }

    for (let i = currentIndex; i < currentIndex + moviesPerPage && i < filteredMovies.length; i++) {
        const movie = filteredMovies[i];
        const userRating = getUserRating(movie.id);

        const div = document.createElement('div');
        div.className = 'list-group-item';

        div.innerHTML = `
            <h5 class="mb-1">
                <a href="/movie/${movie.id}" class="text-decoration-none">${movie.title}</a>
            </h5>
            <div class="d-flex align-items-center flex-wrap">
                <small class="me-3">Release: ${movie.release || "Unknown"}</small>
                <small class="me-3">IMDb Score: ${movie.imdb_score || "N/A"}</small>
                ${
                    isAuthenticated
                    ? userRating !== null
                        ? `
                            <small class="me-2">Your Score: ${userRating}</small>
                            <select onchange="editRating(${movie.id}, this)" class="form-select form-select-sm d-inline-block w-auto me-2">
                                ${generateRatingOptions(userRating)}
                            </select>
                            <button onclick="deleteRating(${movie.id})" class="btn btn-sm btn-outline-danger">✕</button>
                        `
                        : `
                            <select class="form-select form-select-sm w-auto" onchange="rateMovie(${movie.id}, this.value)">
                                <option value="">Rate</option>
                                ${generateRatingOptions()}
                            </select>
                        `
                    : ''
                }
            </div>
        `;

        movieList.appendChild(div);
    }

    currentIndex += moviesPerPage;

    const loadMoreButton = document.getElementById('load-more');
    if (currentIndex >= filteredMovies.length) {
        loadMoreButton.style.display = 'none';
    } else {
        loadMoreButton.style.display = 'block';
    }
}


// Створити варіанти оцінок
function generateRatingOptions(selected = null) {
    let options = '';
    for (let i = 0; i <= 10; i += 0.5) {
        options += `<option value="${i}" ${selected == i ? 'selected' : ''}>${i}</option>`;
    }
    return options;
}


// При оцінці
function rateMovie(movieId, rating) {
    if (!rating) return;

    fetch(`/rate-movie/${movieId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: parseFloat(rating) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.userRatings.push({ movie_id: movieId, rating: parseFloat(rating) });
            renderMovies(true);
        } else {
            alert('Failed to save rating.');
        }
    });
}

// При редагуванні
function editRating(movieId, selectElement) {
    const rating = selectElement.value;
    if (!rating) return;

    fetch(`/rate-movie/${movieId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: parseFloat(rating) })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const ratingObj = window.userRatings.find(r => r.movie_id === movieId);
            if (ratingObj) {
                ratingObj.rating = parseFloat(rating);
            }
            renderMovies(true);
        } else {
            alert('Failed to update rating.');
        }
    });
}

// При видаленні
function deleteRating(movieId) {
    fetch(`/delete-rating/${movieId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Видаляємо з локального масиву
            window.userRatings = window.userRatings.filter(r => r.movie_id !== movieId);
            // Одразу оновлюємо весь список
            renderMovies(true);
        } else {
            alert('Failed to delete rating.');
        }
    });
}

function toggleEditForm() {
    const form = document.getElementById("edit-form");
    form.classList.toggle("d-none");
}



// Сортування фільмів
function sortMovies() {
    const sortBy = document.getElementById('sort-select')?.value;
    const order = document.querySelector('input[name="sort-order"]:checked')?.value;

    filteredMovies.sort((a, b) => {
        let aVal = a[sortBy] || '';
        let bVal = b[sortBy] || '';

        if (sortBy === 'release') {
            return order === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        } else {
            aVal = parseFloat(aVal) || 0;
            bVal = parseFloat(bVal) || 0;
            return order === 'asc' ? aVal - bVal : bVal - aVal;
        }
    });
    renderMovies(true);
}

// Пошук фільмів
function searchMovies() {
    const query = document.getElementById('search-input')?.value.trim().toLowerCase();
    filteredMovies = movies.filter(movie => movie.title.toLowerCase().includes(query));
    sortMovies();
}

// Завантажити ще фільми
function loadMore() {
    renderMovies(false);
}

// Підписка на події
document.getElementById('sort-select')?.addEventListener('change', sortMovies);
document.querySelectorAll('input[name="sort-order"]').forEach(radio => {
    radio.addEventListener('change', sortMovies);
});
document.getElementById('search-button')?.addEventListener('click', searchMovies);
document.getElementById('search-input')?.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        searchMovies();
    }
});
document.getElementById('load-more')?.addEventListener('click', loadMore);

// Початкове завантаження
document.addEventListener('DOMContentLoaded', function() {
    renderMovies(false);
});
