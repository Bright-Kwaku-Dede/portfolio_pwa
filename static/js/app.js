// DOM Elements
const cityInput = document.getElementById('city-input');
const searchBtn = document.getElementById('search-btn');
const errorMessage = document.getElementById('error-message');
const loading = document.getElementById('loading');
const currentWeather = document.getElementById('current-weather');
const forecastSection = document.getElementById('forecast-section');
const historyContainer = document.getElementById('history-container');

// Event Listeners
searchBtn.addEventListener('click', searchWeather);
cityInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchWeather();
    }
});

// Load search history on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSearchHistory();
});

// Search Weather Function
async function searchWeather() {
    const city = cityInput.value.trim();
    
    if (!city) {
        showError('Please enter a city name');
        return;
    }
    
    hideError();
    showLoading();
    hideWeatherSections();
    
    try {
        // Fetch current weather
        const currentData = await fetchCurrentWeather(city);
        
        if (currentData.success) {
            displayCurrentWeather(currentData);
            
            // Fetch forecast
            const forecastData = await fetchForecast(city);
            if (forecastData.success) {
                displayForecast(forecastData);
            }
            
            // Reload search history
            loadSearchHistory();
        } else {
            showError(currentData.error || 'Failed to fetch weather data');
        }
    } catch (error) {
        showError('An error occurred. Please try again.');
        console.error('Error:', error);
    } finally {
        hideLoading();
    }
}

// Fetch Current Weather
async function fetchCurrentWeather(city) {
    const response = await fetch(`/api/weather/current?city=${encodeURIComponent(city)}`);
    return await response.json();
}

// Fetch Forecast
async function fetchForecast(city) {
    const response = await fetch(`/api/weather/forecast?city=${encodeURIComponent(city)}`);
    return await response.json();
}

// Display Current Weather
function displayCurrentWeather(data) {
    document.getElementById('city-name').textContent = `${data.city}, ${data.country}`;
    document.getElementById('weather-description').textContent = data.description;
    document.getElementById('temp-value').textContent = data.temperature;
    document.getElementById('feels-like').textContent = `${data.feels_like}°C`;
    document.getElementById('humidity').textContent = `${data.humidity}%`;
    document.getElementById('wind-speed').textContent = `${data.wind_speed} m/s`;
    document.getElementById('pressure').textContent = `${data.pressure} hPa`;
    
    // Weather icon
    const iconUrl = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
    document.getElementById('weather-icon').src = iconUrl;
    
    currentWeather.style.display = 'block';
}

// Display Forecast
function displayForecast(data) {
    const forecastContainer = document.getElementById('forecast-container');
    forecastContainer.innerHTML = '';
    
    data.forecasts.forEach(forecast => {
        const card = document.createElement('div');
        card.className = 'forecast-card';
        
        // Format date
        const date = new Date(forecast.date);
        const dateStr = date.toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
        });
        
        const iconUrl = `https://openweathermap.org/img/wn/${forecast.icon}@2x.png`;
        
        card.innerHTML = `
            <div class="forecast-date">${dateStr}</div>
            <img class="forecast-icon" src="${iconUrl}" alt="${forecast.description}">
            <div class="forecast-temp">${forecast.temperature}°C</div>
            <div class="forecast-desc">${forecast.description}</div>
            <div style="font-size: 0.8rem; color: #718096; margin-top: 0.5rem;">
                H: ${forecast.temp_max}° L: ${forecast.temp_min}°
            </div>
        `;
        
        forecastContainer.appendChild(card);
    });
    
    forecastSection.style.display = 'block';
}

// Load Search History
async function loadSearchHistory() {
    try {
        const response = await fetch('/api/weather/history');
        const data = await response.json();
        
        if (data.success && data.history.length > 0) {
            displaySearchHistory(data.history);
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Display Search History
function displaySearchHistory(history) {
    historyContainer.innerHTML = '';
    
    history.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        // Format date
        const date = new Date(item.searched_at);
        const timeStr = date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        historyItem.innerHTML = `
            <div>
                <div class="history-city">${item.city}, ${item.country}</div>
                <div style="font-size: 0.85rem; color: #718096;">${timeStr}</div>
            </div>
            <div>
                <div class="history-temp">${item.temperature}°C</div>
                <div style="font-size: 0.85rem; color: #718096; text-transform: capitalize;">
                    ${item.weather_description}
                </div>
            </div>
        `;
        
        // Click to search again
        historyItem.addEventListener('click', () => {
            cityInput.value = item.city;
            searchWeather();
        });
        
        historyContainer.appendChild(historyItem);
    });
}

// Show/Hide Functions
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

function hideError() {
    errorMessage.classList.remove('show');
}

function showLoading() {
    loading.style.display = 'block';
}

function hideLoading() {
    loading.style.display = 'none';
}

function hideWeatherSections() {
    currentWeather.style.display = 'none';
    forecastSection.style.display = 'none';
}