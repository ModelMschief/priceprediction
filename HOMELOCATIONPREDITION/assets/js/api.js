const API_BASE_URL = "http://127.0.0.1:8000"; // Your Flask backend

document.addEventListener("DOMContentLoaded", () => {

    // 1. REGISTER LOGIC
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const username = document.getElementById("regName").value; // Mapping Name to username
            const email = document.getElementById("regEmail").value;
            const password = document.getElementById("regPassword").value;
            const confirmPassword = document.getElementById("regConfirmPassword").value;

            if (password !== confirmPassword) {
                alert("Passwords do not match!");
                return;
            }

            try {
                const response = await fetch(`${API_BASE_URL}/api/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, email, password })
                });
                
                const result = await response.json();
                if (response.ok) {
                    alert("Registration Successful! Please login.");
                    window.location.href = "login.html";
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert("Failed to connect to the server.");
            }
        });
    }

    // 2. LOGIN LOGIC
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const email = document.getElementById("loginEmail").value;
            const password = document.getElementById("loginPassword").value;

            try {
                const response = await fetch(`${API_BASE_URL}/api/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
                
                const result = await response.json();
                if (response.ok) {
                    localStorage.setItem("user", JSON.stringify(result.user));
                    alert(`Welcome back!`);
                    window.location.href = "Home.html"; // Redirect after login
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert("Failed to connect to the server.");
            }
        });
    }

    // 3. RESET PASSWORD LOGIC
    const resetForm = document.getElementById("resetForm");
    if (resetForm) {
        resetForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const email = document.getElementById("resetEmail").value;
            const new_password = document.getElementById("resetNewPassword").value;

            try {
                const response = await fetch(`${API_BASE_URL}/api/reset-password`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, new_password })
                });
                
                const result = await response.json();
                if (response.ok) {
                    alert("Password updated successfully! Please login.");
                    window.location.href = "login.html";
                } else {
                    alert(`Error: ${result.error}`);
                }
            } catch (error) {
                alert("Failed to connect to the server.");
            }
        });
    }

    // ==========================================
    // 4. ML PREDICTION LOGIC (Updated for full fields)
    // ==========================================
    const predictForm = document.getElementById("predictForm");
    const getLocationBtn = document.getElementById("getLocationBtn");

    if (getLocationBtn) {
        getLocationBtn.addEventListener("click", () => {
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        document.getElementById("predLat").value = position.coords.latitude;
                        document.getElementById("predLong").value = position.coords.longitude;
                        alert("Location successfully fetched!");
                    },
                    (error) => {
                        console.error("Error getting location: ", error);
                        alert("Unable to fetch location. The system will use your IP address instead.");
                    }
                );
            } else {
                alert("Geolocation is not supported by your browser.");
            }
        });
    }
    
    if (predictForm) {
        predictForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            
            const resultBox = document.getElementById("predictionResult");
            const priceDisplay = document.getElementById("priceDisplay");
            const locInfo = document.getElementById("locationUsedInfo");
            
            priceDisplay.innerText = "Calculating...";
            locInfo.innerText = "Please wait.";
            resultBox.style.display = "block";

            // Gathering exactly what your ML model needs from the new form
            const sqft_lot_val = document.getElementById("predSqftLot").value;
            const lat_val = document.getElementById("predLat").value;
            const long_val = document.getElementById("predLong").value;

            const payload = {
                bedrooms: parseInt(document.getElementById("predBedrooms").value),
                bathrooms: parseFloat(document.getElementById("predBathrooms").value),
                sqft_living: parseInt(document.getElementById("predSqftLiving").value),
                sqft_lot: sqft_lot_val ? parseInt(sqft_lot_val) : null,
                yr_built: parseInt(document.getElementById("predYrBuilt").value),
                floors: parseFloat(document.getElementById("predFloors").value || 1),
                condition: parseInt(document.getElementById("predCondition").value || 3),
                grade: parseInt(document.getElementById("predGrade").value || 7),
                view: parseInt(document.getElementById("predView").value || 0),
                waterfront: document.getElementById("predWaterfront").checked ? 1 : 0,
                lat: lat_val ? parseFloat(lat_val) : null,
                long: long_val ? parseFloat(long_val) : null,
                yr_renovated: parseInt(document.getElementById("predYrRenovated").value || 0)
            };

            try {
                const response = await fetch(`${API_BASE_URL}/predict`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                if (response.ok) {
                    const formattedPrice = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(result.predicted_price);
                    priceDisplay.innerText = formattedPrice;
                    
                    // Show which location method was used
                    locInfo.innerText = lat_val 
                        ? "Calculated using your precise GPS coordinates." 
                        : "Calculated using your network IP approximate location.";
                } else {
                    priceDisplay.innerText = "Error";
                    locInfo.innerText = result.error;
                }
            } catch (error) {
                priceDisplay.innerText = "Connection Failed";
                locInfo.innerText = "Make sure the Flask server is running.";
            }
        });
    });