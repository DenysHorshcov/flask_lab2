let movies = window.movies;
let isAuthenticated = window.isAuthenticated;

let filteredMovies = [...movies];
let currentIndex = 0;
const moviesPerPage = 8;

// Функція для рендеру фільмів
function renderMovies(reset = false) {
    const movieList = document.getElementById('movie-list');
    if (reset) {
        movieList.innerHTML = '';
        currentIndex = 0;
    }
    for (let i = currentIndex; i < currentIndex + moviesPerPage && i < filteredMovies.length; i++) {
        const movie = filteredMovies[i];

        const div = document.createElement('div');
        div.className = 'list-group-item';

        div.innerHTML = `
            <h5 class="mb-1">
                <a href="/movie/${movie.id}" class="text-decoration-none">${movie.title}</a>
            </h5>
            <small>Release: ${movie.release || "Unknown"}, IMDb Score: ${movie.imdb_score || "N/A"}</small>
            ${isAuthenticated ? `
            <form action="/rate-movie/${movie.id}" method="POST" class="mt-2 d-flex align-items-center" style="max-width: 300px;">
                <input type="number" name="rating" class="form-control me-2" step="0.5" min="0" max="10" placeholder="Your score" required>
                <button type="submit" class="btn btn-sm btn-success">Rate</button>
            </form>
            ` : ''}
        `;

        movieList.appendChild(div);
    }
    currentIndex += moviesPerPage;
    toggleLoadMoreButton();
}

// Показати або сховати кнопку "Load More"
function toggleLoadMoreButton() {
    const button = document.getElementById('load-more');
    button.style.display = currentIndex >= filteredMovies.length ? 'none' : 'block';
}

// Отримати напрямок сортування
function getSortOrder() {
    return document.querySelector('input[name="sort-order"]:checked').value;
}

// Сортувати фільми
function sortMovies() {
    const sortBy = document.getElementById('sort-select').value;
    const order = getSortOrder();

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
    const query = document.getElementById('search-input').value.trim().toLowerCase();
    filteredMovies = movies.filter(movie => movie.title.toLowerCase().includes(query));
    sortMovies();
}

// Обробники подій
document.addEventListener('DOMContentLoaded', function() {
    renderMovies(false);

    document.getElementById('load-more').addEventListener('click', () => renderMovies(false));
    document.getElementById('sort-select').addEventListener('change', sortMovies);
    document.querySelectorAll('input[name="sort-order"]').forEach(radio => radio.addEventListener('change', sortMovies));
    document.getElementById('search-button').addEventListener('click', searchMovies);
    document.getElementById('search-input').addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            searchMovies();
        }
    });
});
