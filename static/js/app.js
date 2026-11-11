/**
 * Jahon Kinolari — Frontend Application Script
 */

const TMDB_IMAGE_BASE_W500 = "https://image.tmdb.org/t/p/w500";
const TMDB_IMAGE_BASE_ORIGINAL = "https://image.tmdb.org/t/p/original";
const FALLBACK_POSTER = "data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22300%22%20height%3D%22450%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20300%20450%22%3E%3Crect%20fill%3D%22%231a2236%22%20width%3D%22300%22%20height%3D%22450%22%2F%3E%3Ctext%20fill%3D%22%236b7280%22%20font-family%3D%22sans-serif%22%20font-size%3D%2248%22%20dy%3D%2210.5%22%20font-weight%3D%22bold%22%20x%3D%2250%25%22%20y%3D%2250%25%22%20text-anchor%3D%22middle%22%3E%F0%9F%8E%AC%3C%2Ftext%3E%3Ctext%20fill%3D%22%239ca3af%22%20font-family%3D%22sans-serif%22%20font-size%3D%2216%22%20dy%3D%2240%22%20x%3D%2250%25%22%20y%3D%2250%25%22%20text-anchor%3D%22middle%22%3EPoster%20mavjud%20emas%3C%2Ftext%3E%3C%2Fsvg%3E";

const state = {
    page: 1,
    genre: "all",
    year: "all",
    sortBy: "trending",
    search: "",
    totalPages: 1,
    totalMovies: 0,
    heroMovies: [],
    heroCurrentIndex: 0,
    heroInterval: null,
    currentModalMovie: null,
    favorites: JSON.parse(localStorage.getItem("jahon_kinolari_favs") || "[]")
};

// ============================================================
// Initialization
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    updateFavBadge();
    setupSearchListener();
    setupKeyboardListeners();

    await Promise.all([
        loadStats(),
        loadGenres(),
        loadFeatured()
    ]);

    await loadMovies(1);
}

// ============================================================
// Hero Featured Slider
// ============================================================
async function loadFeatured() {
    try {
        const res = await fetch("/api/featured");
        const data = await res.json();
        state.heroMovies = data.featured || [];

        if (state.heroMovies.length === 0) return;

        renderHeroSlider();
        startHeroAutoplay();
    } catch (err) {
        console.error("Featured filmlarni yuklashda xatolik:", err);
    }
}

function renderHeroSlider() {
    const slider = document.getElementById("heroSlider");
    const dotsContainer = document.getElementById("heroDots");

    slider.innerHTML = "";
    dotsContainer.innerHTML = "";

    state.heroMovies.forEach((movie, index) => {
        const slide = document.createElement("div");
        slide.className = `hero-slide ${index === 0 ? "active" : ""}`;
        slide.id = `heroSlide_${index}`;

        const backdropUrl = movie.backdrop_path ? `${TMDB_IMAGE_BASE_ORIGINAL}${movie.backdrop_path}` : "";
        const genres = movie.genres ? movie.genres.split(",").slice(0, 3).join(" • ") : "";

        slide.innerHTML = `
            <img src="${backdropUrl}" alt="${escapeHtml(movie.title)}" class="hero-backdrop" onerror="this.style.display='none'">
            <div class="hero-gradient-overlay"></div>
            <div class="hero-content">
                <div class="hero-badge-row">
                    <span class="hero-badge-trend">🔥 Trend Film</span>
                    <span class="hero-badge-rating">★ ${movie.vote_average.toFixed(1)}</span>
                    <span class="hero-year">${movie.release_year || ''}</span>
                    <span class="hero-year">• ${escapeHtml(genres)}</span>
                </div>
                <h1 class="hero-title">${escapeHtml(movie.title)}</h1>
                ${movie.tagline ? `<p class="hero-tagline">"${escapeHtml(movie.tagline)}"</p>` : ''}
                <p class="hero-overview">${escapeHtml(movie.overview || '')}</p>
                <div class="hero-actions">
                    <button class="btn btn-trailer" onclick="openTrailer('${escapeHtml(movie.title)}', ${movie.release_year || 2024})">
                        ▶ Treylerni ko'rish
                    </button>
                    <button class="btn btn-secondary" onclick="openMovieDetail(${movie.id})">
                        ℹ Batafsil ma'lumot
                    </button>
                    <button class="btn btn-fav" onclick="toggleHeroFav(${movie.id})">
                        ${isFavorite(movie.id) ? '❤️ Saqlangan' : '🤍 Sevimlilarga'}
                    </button>
                </div>
            </div>
        `;
        slider.appendChild(slide);

        // Dot
        const dot = document.createElement("div");
        dot.className = `hero-dot ${index === 0 ? "active" : ""}`;
        dot.onclick = () => setHeroSlide(index);
        dotsContainer.appendChild(dot);
    });
}

function startHeroAutoplay() {
    if (state.heroInterval) clearInterval(state.heroInterval);
    state.heroInterval = setInterval(() => {
        changeHeroSlide(1);
    }, 6500);
}

function setHeroSlide(index) {
    if (state.heroMovies.length === 0) return;
    const slides = document.querySelectorAll(".hero-slide");
    const dots = document.querySelectorAll(".hero-dot");

    slides.forEach(s => s.classList.remove("active"));
    dots.forEach(d => d.classList.remove("active"));

    state.heroCurrentIndex = (index + state.heroMovies.length) % state.heroMovies.length;

    if (slides[state.heroCurrentIndex]) slides[state.heroCurrentIndex].classList.add("active");
    if (dots[state.heroCurrentIndex]) dots[state.heroCurrentIndex].classList.add("active");
}

function changeHeroSlide(direction) {
    setHeroSlide(state.heroCurrentIndex + direction);
}

function toggleHeroFav(movieId) {
    const movie = state.heroMovies.find(m => m.id === movieId);
    if (movie) {
        toggleFavorite(movie);
        renderHeroSlider(); // Re-render to update button text
    }
}

// ============================================================
// Genres & Stats
// ============================================================
async function loadGenres() {
    try {
        const res = await fetch("/api/genres");
        const data = await res.json();
        const chipsContainer = document.getElementById("genreChips");

        (data.genres || []).forEach(g => {
            const btn = document.createElement("button");
            btn.className = "genre-chip";
            btn.dataset.genre = g.id;
            btn.innerHTML = `${g.icon} ${g.name}`;
            btn.onclick = () => selectGenre(g.id, btn);
            chipsContainer.appendChild(btn);
        });
    } catch (err) {
        console.error("Janrlarni yuklashda xatolik:", err);
    }
}

async function loadStats() {
    try {
        const res = await fetch("/api/stats");
        const data = await res.json();
        const footerStats = document.getElementById("footerStats");
        footerStats.innerHTML = `
            <span>Ma'lumotlar bazasi: Kaggle TMDB Dataset</span>
            <span>Jami filmlar: ${data.total_movies.toLocaleString()} ta (${data.year_range})</span>
            <span>Yangi va kutilayotgan: ${data.new_and_upcoming} ta</span>
        `;
    } catch (err) {
        console.error("Statistikani yuklashda xatolik:", err);
    }
}

// ============================================================
// Movies Grid & Pagination
// ============================================================
async function loadMovies(page = 1) {
    state.page = page;
    const grid = document.getElementById("moviesGrid");
    const loading = document.getElementById("gridLoading");
    const emptyState = document.getElementById("emptyState");
    const paginationBar = document.getElementById("paginationBar");
    const statsEl = document.getElementById("resultsStats");

    grid.innerHTML = "";
    emptyState.style.display = "none";
    loading.style.display = "flex";
    statsEl.textContent = "Qidirilmoqda...";

    try {
        const params = new URLSearchParams({
            page: state.page,
            per_page: 24,
            genre: state.genre,
            year: state.year,
            sort_by: state.sortBy,
            search: state.search
        });

        const res = await fetch(`/api/movies?${params.toString()}`);
        const data = await res.json();

        loading.style.display = "none";

        state.totalMovies = data.total;
        state.totalPages = data.total_pages;

        statsEl.textContent = `Natija: ${data.total.toLocaleString()} ta kino`;

        if (!data.movies || data.movies.length === 0) {
            emptyState.style.display = "block";
            paginationBar.style.display = "none";
            return;
        }

        renderMovieCards(data.movies);
        renderPagination();
        paginationBar.style.display = "flex";

    } catch (err) {
        loading.style.display = "none";
        emptyState.style.display = "block";
        statsEl.textContent = "Xatolik yuz berdi";
        console.error("Filmlarni yuklashda xatolik:", err);
    }
}

function renderMovieCards(movies) {
    const grid = document.getElementById("moviesGrid");
    grid.innerHTML = "";

    movies.forEach(movie => {
        const card = document.createElement("div");
        card.className = "movie-card";
        card.onclick = (e) => {
            // Prevent opening modal when clicking favorite heart
            if (e.target.closest(".card-fav-btn")) return;
            openMovieDetail(movie.id);
        };

        const posterSrc = movie.poster_path ? `${TMDB_IMAGE_BASE_W500}${movie.poster_path}` : FALLBACK_POSTER;
        const genres = movie.genres ? movie.genres.split(",").slice(0, 2).join(", ") : "";
        const fav = isFavorite(movie.id);

        card.innerHTML = `
            <div class="card-poster-wrap">
                <img src="${posterSrc}" alt="${escapeHtml(movie.title)}" class="card-poster" loading="lazy" onerror="this.src='${FALLBACK_POSTER}'">
                <div class="card-badge-rating">
                    ★ ${movie.vote_average ? movie.vote_average.toFixed(1) : '—'}
                </div>
                <button class="card-fav-btn ${fav ? 'is-fav' : ''}" title="Sevimlilarga qo'shish" onclick="handleCardFavClick(event, ${movie.id})">
                    ${fav ? '❤️' : '🤍'}
                </button>
            </div>
            <div class="card-info">
                <h4 class="card-title" title="${escapeHtml(movie.title)}">${escapeHtml(movie.title)}</h4>
                <div class="card-meta">
                    <span class="card-year">${movie.release_year || 'Noma\'lum'}</span>
                    <span class="card-votes">👥 ${movie.vote_count ? movie.vote_count.toLocaleString() : 0}</span>
                </div>
                <div class="card-genres">${escapeHtml(genres)}</div>
            </div>
        `;

        grid.appendChild(card);
    });
}

function handleCardFavClick(event, movieId) {
    event.stopPropagation();
    // Find movie in existing DOM or fetch
    fetch(`/api/movie/${movieId}`)
        .then(r => r.json())
        .then(movie => {
            toggleFavorite(movie);
            // Update the clicked button
            const btn = event.currentTarget;
            const fav = isFavorite(movieId);
            btn.className = `card-fav-btn ${fav ? 'is-fav' : ''}`;
            btn.innerHTML = fav ? '❤️' : '🤍';
        });
}

// ============================================================
// Pagination
// ============================================================
function renderPagination() {
    const pageNumbers = document.getElementById("pageNumbers");
    const prevBtn = document.getElementById("prevPageBtn");
    const nextBtn = document.getElementById("nextPageBtn");

    pageNumbers.innerHTML = "";

    prevBtn.disabled = state.page <= 1;
    nextBtn.disabled = state.page >= state.totalPages;

    const current = state.page;
    const total = state.totalPages;

    // Window of pages around current
    let pages = [];
    pages.push(1);
    for (let i = Math.max(2, current - 2); i <= Math.min(total - 1, current + 2); i++) {
        pages.push(i);
    }
    if (total > 1 && !pages.includes(total)) {
        pages.push(total);
    }

    let lastP = 0;
    pages.forEach(p => {
        if (lastP && p - lastP > 1) {
            const dots = document.createElement("span");
            dots.textContent = "...";
            dots.style.padding = "0 6px";
            dots.style.color = "var(--text-muted)";
            pageNumbers.appendChild(dots);
        }

        const btn = document.createElement("button");
        btn.className = `page-num ${p === current ? "active" : ""}`;
        btn.textContent = p;
        btn.onclick = () => {
            window.scrollTo({ top: 400, behavior: "smooth" });
            loadMovies(p);
        };
        pageNumbers.appendChild(btn);
        lastP = p;
    });
}

function changePage(direction) {
    const newPage = state.page + direction;
    if (newPage >= 1 && newPage <= state.totalPages) {
        window.scrollTo({ top: 400, behavior: "smooth" });
        loadMovies(newPage);
    }
}

// ============================================================
// Filters, Sorting & Search
// ============================================================
function selectGenre(genreId, btn) {
    state.genre = genreId;
    document.querySelectorAll(".genre-chip").forEach(c => c.classList.remove("active"));
    if (btn) btn.classList.add("active");
    loadMovies(1);
}

function applyFilters() {
    state.year = document.getElementById("yearSelect").value;
    state.sortBy = document.getElementById("sortSelect").value;
    loadMovies(1);
}

function setQuickTab(tab) {
    document.querySelectorAll(".nav-btn[data-filter]").forEach(b => b.classList.remove("active"));
    const activeBtn = document.querySelector(`.nav-btn[data-filter="${tab}"]`);
    if (activeBtn) activeBtn.classList.add("active");

    const yearSelect = document.getElementById("yearSelect");
    const sortSelect = document.getElementById("sortSelect");

    if (tab === "trending") {
        state.genre = "all";
        state.year = "all";
        state.sortBy = "trending";
        state.search = "";
        yearSelect.value = "all";
        sortSelect.value = "trending";
    } else if (tab === "rating") {
        state.genre = "all";
        state.year = "all";
        state.sortBy = "rating";
        sortSelect.value = "rating";
    } else if (tab === "upcoming") {
        state.genre = "all";
        state.year = "2020s";
        state.sortBy = "newest";
        yearSelect.value = "2020s";
        sortSelect.value = "newest";
    }

    // Reset genre chips
    document.querySelectorAll(".genre-chip").forEach(c => c.classList.remove("active"));
    const allChip = document.querySelector('.genre-chip[data-genre="all"]');
    if (allChip) allChip.classList.add("active");

    document.getElementById("searchInput").value = "";
    document.getElementById("clearSearchBtn").style.display = "none";

    loadMovies(1);
}

function resetFilters() {
    setQuickTab("trending");
}

let searchDebounceTimer = null;
function setupSearchListener() {
    const input = document.getElementById("searchInput");
    const clearBtn = document.getElementById("clearSearchBtn");

    input.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        clearBtn.style.display = val.length > 0 ? "block" : "none";

        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            state.search = val;
            loadMovies(1);
        }, 400);
    });

    clearBtn.addEventListener("click", () => {
        input.value = "";
        state.search = "";
        clearBtn.style.display = "none";
        loadMovies(1);
    });
}

// ============================================================
// Movie Details Modal
// ============================================================
async function openMovieDetail(movieId) {
    try {
        const res = await fetch(`/api/movie/${movieId}`);
        if (!res.ok) throw new Error("Film topilmadi");
        const movie = await res.json();
        state.currentModalMovie = movie;

        // Populate elements
        const backdropEl = document.getElementById("modalBackdrop");
        if (movie.backdrop_path) {
            backdropEl.src = `${TMDB_IMAGE_BASE_ORIGINAL}${movie.backdrop_path}`;
            backdropEl.style.display = "block";
        } else {
            backdropEl.style.display = "none";
        }

        const posterEl = document.getElementById("modalPoster");
        posterEl.src = movie.poster_path ? `${TMDB_IMAGE_BASE_W500}${movie.poster_path}` : FALLBACK_POSTER;

        document.getElementById("modalTitle").textContent = movie.title;
        document.getElementById("modalOriginalTitle").textContent = movie.original_title ? `Asl nomi: ${movie.original_title}` : "";
        document.getElementById("modalTagline").textContent = movie.tagline ? `"${movie.tagline}"` : "";

        // Meta chips
        const metaChips = document.getElementById("modalMetaChips");
        metaChips.innerHTML = `
            <span class="meta-chip gold">★ ${movie.vote_average ? movie.vote_average.toFixed(1) : '—'} / 10</span>
            <span class="meta-chip">👥 ${movie.vote_count ? movie.vote_count.toLocaleString() : 0} ovoz</span>
            <span class="meta-chip">📅 ${movie.release_year || 'Noma\'lum'}</span>
            <span class="meta-chip">⏱ ${movie.formatted_runtime || 'Noma\'lum'}</span>
            <span class="meta-chip">🔥 Trend: ${movie.popularity || 0}</span>
        `;

        // Genres
        const genresEl = document.getElementById("modalGenres");
        genresEl.innerHTML = "";
        if (movie.genres) {
            movie.genres.split(",").forEach(g => {
                const tag = document.createElement("span");
                tag.className = "modal-genre-tag";
                tag.textContent = g.trim();
                genresEl.appendChild(tag);
            });
        }

        // Overview
        document.getElementById("modalOverview").textContent = movie.overview || "Ushbu film haqida qisqacha tavsif mavjud emas.";

        // Details
        document.getElementById("modalLang").textContent = (movie.original_language || 'en').toUpperCase();
        document.getElementById("modalCountries").textContent = movie.production_countries || "Noma'lum";
        document.getElementById("modalBudget").textContent = movie.formatted_budget;
        document.getElementById("modalRevenue").textContent = movie.formatted_revenue;

        // Action Buttons
        document.getElementById("modalTrailerBtn").href = movie.trailer_url;
        const imdbBtn = document.getElementById("modalImdbBtn");
        if (movie.imdb_url) {
            imdbBtn.href = movie.imdb_url;
            imdbBtn.style.display = "inline-flex";
        } else {
            imdbBtn.style.display = "none";
        }

        // Favorite button
        updateModalFavButton();

        // Show modal
        const modal = document.getElementById("movieModal");
        modal.classList.add("open");
        document.body.style.overflow = "hidden";

    } catch (err) {
        showToast("Film ma'lumotlarini yuklab bo'lmadi");
        console.error(err);
    }
}

function closeMovieModal() {
    const modal = document.getElementById("movieModal");
    modal.classList.remove("open");
    document.body.style.overflow = "";
    state.currentModalMovie = null;
}

function closeModalOnOverlay(e) {
    if (e.target.id === "movieModal") {
        closeMovieModal();
    }
}

function updateModalFavButton() {
    const favBtn = document.getElementById("modalFavBtn");
    if (!state.currentModalMovie) return;
    const fav = isFavorite(state.currentModalMovie.id);
    favBtn.innerHTML = fav ? "❤️ Sevimlilardan o'chirish" : "🤍 Sevimlilarga qo'shish";
}

function toggleModalFavorite() {
    if (!state.currentModalMovie) return;
    toggleFavorite(state.currentModalMovie);
    updateModalFavButton();
    // Also re-render current grid cards
    const cardFavBtn = document.querySelector(`.card-fav-btn[onclick*="${state.currentModalMovie.id}"]`);
    if (cardFavBtn) {
        const fav = isFavorite(state.currentModalMovie.id);
        cardFavBtn.className = `card-fav-btn ${fav ? 'is-fav' : ''}`;
        cardFavBtn.innerHTML = fav ? '❤️' : '🤍';
    }
}

// ============================================================
// Favorites (LocalStorage)
// ============================================================
function isFavorite(movieId) {
    return state.favorites.some(f => f.id === movieId);
}

function toggleFavorite(movie) {
    const index = state.favorites.findIndex(f => f.id === movie.id);
    if (index >= 0) {
        state.favorites.splice(index, 1);
        showToast(`"${movie.title}" sevimlilardan olib tashlandi`);
    } else {
        state.favorites.push({
            id: movie.id,
            title: movie.title,
            release_year: movie.release_year,
            vote_average: movie.vote_average,
            poster_path: movie.poster_path,
            genres: movie.genres
        });
        showToast(`"${movie.title}" sevimlilarga qo'shildi! ❤️`);
    }
    localStorage.setItem("jahon_kinolari_favs", JSON.stringify(state.favorites));
    updateFavBadge();
}

function updateFavBadge() {
    const count = state.favorites.length;
    document.getElementById("favCountBadge").textContent = count;
    const drawerCount = document.getElementById("favDrawerCount");
    if (drawerCount) drawerCount.textContent = count;
}

function openFavoritesModal() {
    renderFavoritesList();
    const modal = document.getElementById("favoritesModal");
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
}

function closeFavoritesModal() {
    const modal = document.getElementById("favoritesModal");
    modal.classList.remove("open");
    document.body.style.overflow = "";
}

function closeFavOnOverlay(e) {
    if (e.target.id === "favoritesModal") {
        closeFavoritesModal();
    }
}

function renderFavoritesList() {
    const container = document.getElementById("favoritesList");
    container.innerHTML = "";

    updateFavBadge();

    if (state.favorites.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px 10px; color: var(--text-gray);">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">🤍</div>
                <p>Hozircha sevimlilar ro'yxati bo'sh.</p>
                <p style="font-size: 0.8rem; margin-top: 6px;">Filmlardagi yurakcha belgisini bosib, bu yerga saqlashingiz mumkin.</p>
            </div>
        `;
        return;
    }

    state.favorites.forEach(m => {
        const item = document.createElement("div");
        item.className = "fav-item";
        item.onclick = (e) => {
            if (e.target.closest(".fav-remove-btn")) return;
            closeFavoritesModal();
            openMovieDetail(m.id);
        };

        const posterSrc = m.poster_path ? `${TMDB_IMAGE_BASE_W500}${m.poster_path}` : FALLBACK_POSTER;

        item.innerHTML = `
            <img src="${posterSrc}" alt="${escapeHtml(m.title)}" class="fav-item-poster" onerror="this.src='${FALLBACK_POSTER}'">
            <div class="fav-item-info">
                <div class="fav-item-title">${escapeHtml(m.title)}</div>
                <div class="fav-item-meta">★ ${m.vote_average ? m.vote_average.toFixed(1) : '-'} • ${m.release_year || ''}</div>
            </div>
            <button class="fav-remove-btn" title="O'chirish" onclick="removeFavorite(${m.id}, event)">✕</button>
        `;
        container.appendChild(item);
    });
}

function removeFavorite(movieId, e) {
    if (e) e.stopPropagation();
    const movie = state.favorites.find(f => f.id === movieId);
    if (movie) {
        toggleFavorite(movie);
        renderFavoritesList();
        // Update cards on page
        const cardBtn = document.querySelector(`.card-fav-btn[onclick*="${movieId}"]`);
        if (cardBtn) {
            cardBtn.className = "card-fav-btn";
            cardBtn.innerHTML = "🤍";
        }
    }
}

function clearAllFavorites() {
    if (confirm("Rostdan ham barcha sevimlilarni tozalaysizmi?")) {
        state.favorites = [];
        localStorage.setItem("jahon_kinolari_favs", JSON.stringify([]));
        updateFavBadge();
        renderFavoritesList();
        document.querySelectorAll(".card-fav-btn").forEach(b => {
            b.className = "card-fav-btn";
            b.innerHTML = "🤍";
        });
        showToast("Sevimlilar ro'yxati tozalandi");
    }
}

// ============================================================
// Utilities
// ============================================================
function openTrailer(title, year) {
    const q = encodeURIComponent(`${title} ${year} official trailer`);
    window.open(`https://www.youtube.com/results?search_query=${q}`, "_blank");
}

let toastTimer = null;
function showToast(msg) {
    const toast = document.getElementById("toast");
    toast.textContent = msg;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2500);
}

function setupKeyboardListeners() {
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            closeMovieModal();
            closeFavoritesModal();
        }
    });
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

