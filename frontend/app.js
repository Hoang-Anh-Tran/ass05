const API_URL = "http://localhost:4000";
const contentArea = document.getElementById("content-area");

const appState = {
    currentView: 'store',
    customerId: null,
    customerName: 'Guest',
    customerRole: 'customer'
};

// --- Admin Nav Visibility ---
function updateAdminNav() {
    const adminLabel = document.getElementById('admin-nav-label');
    const adminItems = document.querySelectorAll('.admin-nav-item');
    const isAdmin = appState.customerRole === 'admin';
    if (adminLabel) adminLabel.style.display = isAdmin ? '' : 'none';
    adminItems.forEach(el => el.style.display = isAdmin ? '' : 'none');
    // If non-admin is on admin page, redirect to store
    if (!isAdmin && ['dashboard', 'books', 'customers'].includes(appState.currentView)) {
        document.querySelector('.nav-item[data-target="store"]').click();
    }
}

// --- Toast System ---
function showToast(message, type = 'success') {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    let icon = "ri-information-line";
    if (type === 'success') icon = "ri-checkbox-circle-line";
    if (type === 'error') icon = "ri-error-warning-line";
    toast.innerHTML = `<i class="${icon}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = "slideOut 0.3s ease forwards";
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- API Helpers ---
async function apiCall(endpoint, method = 'GET', data = null) {
    try {
        const options = { method, headers: { 'Content-Type': 'application/json' } };
        if (data) options.body = JSON.stringify(data);
        const response = await fetch(`${API_URL}${endpoint}`, options);
        if (!response.ok) throw new Error("API Request failed");
        const text = await response.text();
        return text ? JSON.parse(text) : null;
    } catch (e) {
        showToast(e.message, 'error');
        console.error(e);
        return null;
    }
}

// --- Star Helpers ---
function renderStars(rating, size = 16) {
    let html = '';
    for (let i = 1; i <= 5; i++) {
        html += `<i class="ri-star-${i <= rating ? 'fill' : 'line'}" style="color:${i <= rating ? '#f5a623' : '#e0e0e0'};font-size:${size}px;"></i>`;
    }
    return html;
}

// --- Navigation ---
document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", (e) => {
        e.preventDefault();
        document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
        item.classList.add("active");
        loadView(item.getAttribute("data-target"));
    });
});

document.querySelector(".theme-toggle").addEventListener("click", () => {
    const isDark = document.body.getAttribute("data-theme") === "dark";
    document.body.setAttribute("data-theme", isDark ? "light" : "dark");
});

function loadView(viewName) {
    appState.currentView = viewName;
    contentArea.innerHTML = `<div class="view-section" style="display:flex;justify-content:center;padding:100px;"><i class="ri-loader-4-line ri-spin" style="font-size:40px;color:var(--accent);"></i></div>`;
    setTimeout(() => {
        switch (viewName) {
            case 'store': renderStore(); break;
            case 'dashboard': renderDashboard(); break;
            case 'books': renderBooks(); break;
            case 'customers': renderCustomers(); break;
            case 'cart': renderCart(); break;
            case 'orders': renderOrders(); break;
        }
    }, 200);
}

// ============= CUSTOMER-FACING VIEWS =============

async function renderStore() {
    const books = await apiCall("/books/") || [];
    const comments = await apiCall("/comments/") || [];

    // Calc avg ratings per book
    const ratingsMap = {};
    comments.forEach(c => {
        if (!ratingsMap[c.book_id]) ratingsMap[c.book_id] = { total: 0, count: 0 };
        ratingsMap[c.book_id].total += c.rating;
        ratingsMap[c.book_id].count++;
    });

    let html = `
        <div class="view-section">
            <div class="page-header">
                <div>
                    <h1><i class="ri-store-2-line" style="color:var(--accent);"></i> Book Store</h1>
                    <p>${books.length} books available${appState.customerId ? ` · Shopping as <b>${appState.customerName}</b>` : ' · <b style="color:var(--danger);">Select a customer first ↗</b>'}</p>
                </div>
            </div>
            <div class="grid-cards">
    `;

    books.forEach(b => {
        const rd = ratingsMap[b.id];
        const avg = rd ? (rd.total / rd.count).toFixed(1) : null;
        const stars = avg ? renderStars(Math.round(avg)) : '<span style="font-size:12px;color:var(--text-muted);">No ratings</span>';
        const ratingBadge = avg ? `<span class="rating-badge">${stars} <span>${avg}</span> <span style="font-size:11px;color:var(--text-muted);">(${rd.count})</span></span>` : stars;

        html += `
            <div class="data-card">
                <div class="card-icon"><i class="ri-book-2-line"></i></div>
                <h3>${b.title}</h3>
                <p style="margin-bottom:8px;">by ${b.author}</p>
                <div>${ratingBadge}</div>
                <div class="book-price-tag">$${b.price}</div>
                <div class="book-stock">${b.stock > 0 ? `${b.stock} in stock` : '<span style="color:var(--danger)">Out of stock</span>'}</div>
                <div class="card-actions">
                    <button class="card-btn" onclick="addToCart(${b.id})"><i class="ri-shopping-cart-line"></i> Add to Cart</button>
                    <button class="card-btn" onclick="openRateModal(${b.id}, '${b.title.replace(/'/g, "\\'")}')"><i class="ri-star-line"></i> Rate</button>
                </div>
            </div>
        `;
    });

    html += `</div></div>`;
    contentArea.innerHTML = html;
}

// ============= CART =============

let cachedCartTotal = 0;

async function renderCart() {
    if (!appState.customerId) {
        contentArea.innerHTML = `<div class="view-section"><div style="text-align:center;padding:80px;"><i class="ri-user-line" style="font-size:48px;color:var(--text-muted);"></i><h2 style="margin-top:16px;">Please select a customer first</h2><p style="color:var(--text-muted);margin-top:8px;">Click your name in the top-right to switch customer</p><button class="primary-btn" style="margin:24px auto 0;" onclick="openCustomerSelector()"><i class="ri-user-settings-line"></i> Select Customer</button></div></div>`;
        return;
    }

    contentArea.innerHTML = `
        <div class="view-section">
            <div class="page-header">
                <div>
                    <h1><i class="ri-shopping-cart-2-line" style="color:var(--accent);"></i> My Cart</h1>
                    <p>Shopping as <b>${appState.customerName}</b></p>
                </div>
                <button class="primary-btn" onclick="openCheckoutModal()"><i class="ri-secure-payment-line"></i> Checkout</button>
            </div>
            <div id="cart-container"><div style="display:flex;justify-content:center;padding:40px;"><i class="ri-loader-4-line ri-spin" style="font-size:30px;color:var(--accent);"></i></div></div>
        </div>
    `;

    const cartData = await apiCall(`/cart/${appState.customerId}/`);
    const container = document.getElementById("cart-container");

    if (!cartData || !cartData.items || cartData.items.length === 0) {
        cachedCartTotal = 0;
        container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted);"><i class="ri-shopping-bag-line" style="font-size:48px;display:block;margin-bottom:12px;"></i>Your cart is empty. Browse the <a href="#" onclick="document.querySelector('.nav-item[data-target=store]').click();return false;" style="color:var(--accent);">Book Store</a> to add items.</div>`;
        return;
    }

    const books = await apiCall("/books/") || [];
    const bookMap = {};
    books.forEach(b => { bookMap[b.id] = b; });

    let grandTotal = 0;
    let html = `<div class="grid-cards">`;
    cartData.items.forEach(item => {
        const book = bookMap[item.book_id];
        const bookTitle = book ? book.title : `Book #${item.book_id}`;
        const unitPrice = book ? parseFloat(book.price) : 0;
        const subtotal = unitPrice * item.quantity;
        grandTotal += subtotal;

        html += `
            <div class="data-card" style="display:flex;justify-content:space-between;align-items:center;">
                <div style="flex:1;">
                    <h3>${bookTitle}</h3>
                    <p style="margin-bottom:4px;color:var(--text-muted);font-size:13px;">Unit: $${unitPrice.toFixed(2)}</p>
                    <p style="margin-bottom:0;">Qty: ${item.quantity}</p>
                </div>
                <div style="display:flex;align-items:center;gap:16px;">
                    <div style="font-weight:600;font-size:18px;color:var(--accent);">$${subtotal.toFixed(2)}</div>
                    <button class="card-btn" style="flex:none;width:40px;color:var(--danger);" onclick="removeCartItem(${item.id})"><i class="ri-delete-bin-line"></i></button>
                </div>
            </div>
        `;
    });
    html += `</div>`;

    html += `
        <div style="display:flex;justify-content:flex-end;align-items:center;margin-top:24px;padding:20px 24px;background:var(--bg-card,var(--bg-secondary));border-radius:16px;border:1px solid var(--border-color);">
            <div style="margin-right:24px;font-size:14px;color:var(--text-muted);">${cartData.items.length} item(s)</div>
            <div style="font-size:14px;color:var(--text-muted);margin-right:8px;">Total:</div>
            <div style="font-weight:700;font-size:28px;color:var(--accent);">$${grandTotal.toFixed(2)}</div>
        </div>
    `;

    cachedCartTotal = grandTotal;
    container.innerHTML = html;
}

// ============= ORDERS =============

async function renderOrders() {
    const endpoint = appState.customerId ? `/orders/list/?customer_id=${appState.customerId}` : `/orders/list/`;
    const orders = await apiCall(endpoint) || [];

    let html = `
        <div class="view-section">
            <div class="page-header">
                <div>
                    <h1><i class="ri-truck-line" style="color:var(--accent);"></i> ${appState.customerId ? 'My Orders' : 'All Orders'}</h1>
                    <p>${orders.length} order(s)${appState.customerId ? ` for ${appState.customerName}` : ''}</p>
                </div>
            </div>
            <div class="grid-cards">
    `;

    if (orders.length === 0) {
        html += `<div style="text-align:center;padding:40px;color:var(--text-muted);grid-column:1/-1;"><i class="ri-inbox-line" style="font-size:48px;display:block;margin-bottom:12px;"></i>No orders yet.</div>`;
    }

    const payLabels = { credit_card: "Credit Card", paypal: "PayPal", cod: "COD" };
    const shipLabels = { standard: "Standard", express: "Express", overnight: "Overnight" };

    orders.forEach(o => {
        let statusColor = "var(--text-muted)";
        if (o.status === "SHIPPED") statusColor = "var(--success)";
        if (o.status && o.status.includes("FAILED")) statusColor = "var(--danger)";
        if (o.status === "PROCESSING" || o.status === "PAID") statusColor = "var(--accent)";

        html += `
            <div class="data-card">
                <div class="card-icon" style="color:${statusColor}"><i class="ri-box-3-line"></i></div>
                <h3>Order #${o.id}</h3>
                <p>Customer #${o.customer_id}</p>
                <div style="font-weight:600;font-size:24px;margin-bottom:8px;">$${o.total_amount}</div>
                <div style="font-size:12px;color:var(--text-muted);margin-bottom:12px;">
                    <i class="ri-bank-card-line"></i> ${payLabels[o.pay_method] || o.pay_method}
                    &nbsp;·&nbsp;
                    <i class="ri-truck-line"></i> ${shipLabels[o.ship_method] || o.ship_method}
                </div>
                <div style="display:inline-block;padding:4px 12px;background:rgba(0,0,0,0.05);border-radius:20px;font-size:12px;font-weight:600;color:${statusColor}">${o.status}</div>
            </div>
        `;
    });
    html += `</div></div>`;
    contentArea.innerHTML = html;
}

// ============= ADMIN VIEWS =============

function renderDashboard() {
    contentArea.innerHTML = `
        <div class="view-section">
            <div class="page-header"><div><h1>System Dashboard</h1><p>Overview of microservices health & counts</p></div></div>
            <div class="grid-cards">
                <div class="data-card"><div class="card-icon"><i class="ri-stack-line"></i></div><h3>Microservices</h3><h1 style="font-size:36px;">12</h1><p style="margin-top:10px;">All services active</p></div>
            </div>
        </div>
    `;
}

async function renderBooks() {
    const books = await apiCall("/books/") || [];
    let html = `
        <div class="view-section">
            <div class="page-header">
                <div><h1>Manage Books</h1><p>Total: ${books.length}</p></div>
                <button class="primary-btn" onclick="openBookModal()"><i class="ri-add-line"></i> Add New Book</button>
            </div>
            <div class="grid-cards">
    `;
    books.forEach(b => {
        html += `
            <div class="data-card">
                <div class="card-icon"><i class="ri-book-2-line"></i></div>
                <h3>${b.title}</h3>
                <p>by ${b.author}</p>
                <div style="font-weight:600;font-size:18px;margin-bottom:16px;color:var(--accent);">$${b.price} <span style="font-size:12px;font-weight:400;color:var(--text-muted)">| Stock: ${b.stock}</span></div>
            </div>
        `;
    });
    html += `</div></div>`;
    contentArea.innerHTML = html;
}

async function renderCustomers() {
    const customers = await apiCall("/customers/") || [];
    let html = `
        <div class="view-section">
            <div class="page-header">
                <div><h1>Customers</h1><p>Total: ${customers.length}</p></div>
                <button class="primary-btn" onclick="openCustomerModal()"><i class="ri-user-add-line"></i> Register</button>
            </div>
            <div class="grid-cards">
    `;
    customers.forEach(c => {
        html += `
            <div class="data-card">
                <div class="card-icon"><i class="ri-user-smile-line"></i></div>
                <h3>${c.name}</h3>
                <p><i class="ri-mail-line"></i> ${c.email}</p>
                <div class="card-actions">
                    <button class="card-btn" onclick="switchToCustomer(${c.id},'${c.name.replace(/'/g, "\\'")}')"><i class="ri-login-box-line"></i> Login as</button>
                </div>
            </div>
        `;
    });
    html += `</div></div>`;
    contentArea.innerHTML = html;
}

// ============= ACTIONS =============

function addToCart(bookId) {
    if (!appState.customerId) {
        showToast("Please select a customer first!", "error");
        openCustomerSelector();
        return;
    }
    apiCall('/cart/items/', 'POST', { cart: appState.customerId, book_id: bookId, quantity: 1 })
        .then(res => {
            if (res) {
                if (res.error) showToast(res.error, 'error');
                else showToast("Added to cart!");
            }
        });
}

async function removeCartItem(itemId) {
    await apiCall(`/cart/items/${itemId}/`, 'DELETE');
    showToast("Removed from cart");
    renderCart();
}

async function createBook(e) {
    e.preventDefault();
    const data = {
        title: document.getElementById('b-title').value,
        author: document.getElementById('b-author').value,
        price: parseFloat(document.getElementById('b-price').value),
        stock: parseInt(document.getElementById('b-stock').value)
    };
    const res = await apiCall('/staff/', 'POST', data);
    if (res) { showToast("Book added!"); closeModal(); renderBooks(); }
}

async function createCustomer(e) {
    e.preventDefault();
    const data = { name: document.getElementById('c-name').value, email: document.getElementById('c-email').value };
    const res = await apiCall('/customers/', 'POST', data);
    if (res) {
        showToast("Customer registered! Cart auto-created.");
        closeModal();
        switchToCustomer(res.id, res.name);
        renderCustomers();
    }
}

async function submitRating(bookId) {
    const rating = parseInt(document.getElementById('rate-value').value);
    const comment = document.getElementById('rate-comment').value;
    if (!rating || rating < 1 || rating > 5) { showToast("Please select a rating (1-5)", "error"); return; }

    const res = await apiCall('/comments/', 'POST', {
        book_id: bookId,
        customer_id: appState.customerId,
        rating: rating,
        comment: comment || ""
    });
    if (res) { showToast("Review submitted!"); closeModal(); renderStore(); }
}

function switchToCustomer(id, name, role) {
    appState.customerId = id;
    appState.customerName = name;
    appState.customerRole = role || 'customer';
    document.getElementById('user-avatar').src = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=${role === 'admin' ? 'e53e3e' : '4318ff'}&color=fff`;
    document.getElementById('user-name').textContent = role === 'admin' ? `${name} (Admin)` : name;
    updateAdminNav();
    showToast(`Logged in as ${name}${role === 'admin' ? ' (Admin)' : ''}`);
    if (appState.currentView === 'store') renderStore();
}

// ============= CHECKOUT =============

let selectedPayMethod = 'credit_card';
let selectedShipMethod = 'standard';

function openCheckoutModal() {
    if (cachedCartTotal <= 0) { showToast("Cart is empty!", "error"); return; }

    openModal(`
        <div class="modal-content" style="width:520px;">
            <div class="modal-head">
                <h2><i class="ri-secure-payment-line" style="color:var(--accent);"></i> Checkout</h2>
                <i class="ri-close-line close-modal" onclick="closeModal()"></i>
            </div>

            <div class="form-group">
                <label>Payment Method</label>
                <div class="method-grid" id="pay-methods">
                    <div class="method-card selected" onclick="selectMethod('pay','credit_card')">
                        <i class="ri-bank-card-line"></i>
                        <div class="method-name">Credit Card</div>
                    </div>
                    <div class="method-card" onclick="selectMethod('pay','paypal')">
                        <i class="ri-paypal-line"></i>
                        <div class="method-name">PayPal</div>
                    </div>
                    <div class="method-card" onclick="selectMethod('pay','cod')">
                        <i class="ri-money-dollar-circle-line"></i>
                        <div class="method-name">COD</div>
                        <div class="method-desc">Cash on Delivery</div>
                    </div>
                </div>
            </div>

            <div class="form-group">
                <label>Shipping Method</label>
                <div class="method-grid" id="ship-methods">
                    <div class="method-card selected" onclick="selectMethod('ship','standard')">
                        <i class="ri-truck-line"></i>
                        <div class="method-name">Standard</div>
                        <div class="method-desc">5-7 days</div>
                    </div>
                    <div class="method-card" onclick="selectMethod('ship','express')">
                        <i class="ri-rocket-2-line"></i>
                        <div class="method-name">Express</div>
                        <div class="method-desc">1-2 days</div>
                    </div>
                    <div class="method-card" onclick="selectMethod('ship','overnight')">
                        <i class="ri-flashlight-line"></i>
                        <div class="method-name">Overnight</div>
                        <div class="method-desc">Next day</div>
                    </div>
                </div>
            </div>

            <div class="checkout-summary">
                <div class="checkout-row"><span>Subtotal</span><span>$${cachedCartTotal.toFixed(2)}</span></div>
                <div class="checkout-row total"><span>Total</span><span>$${cachedCartTotal.toFixed(2)}</span></div>
            </div>

            <button class="primary-btn" style="width:100%;justify-content:center;margin-top:20px;" onclick="placeOrder()">
                <i class="ri-check-double-line"></i> Place Order — $${cachedCartTotal.toFixed(2)}
            </button>
        </div>
    `);
    selectedPayMethod = 'credit_card';
    selectedShipMethod = 'standard';
}

function selectMethod(type, value) {
    if (type === 'pay') selectedPayMethod = value;
    else selectedShipMethod = value;

    const container = document.getElementById(type === 'pay' ? 'pay-methods' : 'ship-methods');
    container.querySelectorAll('.method-card').forEach(c => c.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
}

async function placeOrder() {
    const data = {
        customer_id: appState.customerId,
        total_amount: cachedCartTotal,
        pay_method: selectedPayMethod,
        ship_method: selectedShipMethod
    };

    const res = await apiCall('/orders/', 'POST', data);
    if (res) {
        if (res.error) showToast(res.error, 'error');
        else {
            showToast(`Order placed! $${cachedCartTotal.toFixed(2)}`);
            closeModal();
            document.querySelector('.nav-item[data-target="orders"]').click();
        }
    }
}

// ============= RATING MODAL =============

function openRateModal(bookId, bookTitle) {
    if (!appState.customerId) { showToast("Please select a customer first!", "error"); openCustomerSelector(); return; }

    // Load existing reviews for this book
    apiCall(`/comments/?book_id=${bookId}`).then(reviews => {
        let reviewHtml = '';
        if (reviews && reviews.length > 0) {
            reviews.forEach(r => {
                reviewHtml += `
                    <div class="review-item">
                        <div class="review-header">
                            <span class="review-customer">Customer #${r.customer_id}</span>
                            <span>${renderStars(r.rating, 14)}</span>
                        </div>
                        <div class="review-text">${r.comment || '<em>No comment</em>'}</div>
                    </div>
                `;
            });
        } else {
            reviewHtml = '<p style="color:var(--text-muted);text-align:center;padding:16px;">No reviews yet. Be the first!</p>';
        }

        openModal(`
            <div class="modal-content" style="width:480px;">
                <div class="modal-head">
                    <h2>Rate "${bookTitle}"</h2>
                    <i class="ri-close-line close-modal" onclick="closeModal()"></i>
                </div>

                <div style="max-height:200px;overflow-y:auto;margin-bottom:20px;border:1px solid var(--border-color);border-radius:var(--radius-sm);padding:0 16px;">
                    ${reviewHtml}
                </div>

                <input type="hidden" id="rate-value" value="0">
                <div class="form-group">
                    <label>Your Rating</label>
                    <div class="star-input" id="star-input">
                        ${[1, 2, 3, 4, 5].map(i => `<i class="ri-star-line" data-val="${i}" onclick="setStarRating(${i})"></i>`).join('')}
                    </div>
                </div>
                <div class="form-group">
                    <label>Comment (optional)</label>
                    <textarea id="rate-comment" class="form-input" rows="3" placeholder="Share your thoughts..."></textarea>
                </div>
                <button class="primary-btn" style="width:100%;justify-content:center;" onclick="submitRating(${bookId})">
                    <i class="ri-send-plane-line"></i> Submit Review
                </button>
            </div>
        `);
    });
}

function setStarRating(val) {
    document.getElementById('rate-value').value = val;
    document.querySelectorAll('#star-input i').forEach((star, idx) => {
        star.className = idx < val ? 'ri-star-fill active' : 'ri-star-line';
    });
}

// ============= CUSTOMER SELECTOR =============

async function openCustomerSelector() {
    const customers = await apiCall("/customers/") || [];

    let list = '';
    customers.forEach(c => {
        const isActive = c.id === appState.customerId;
        const isAdmin = c.role === 'admin';
        const bgColor = isAdmin ? 'e53e3e' : '4318ff';
        list += `
            <div class="data-card" style="padding:16px;cursor:pointer;display:flex;align-items:center;gap:12px;${isActive ? 'border-color:var(--accent);background:rgba(67,24,255,0.05);' : ''}" onclick="switchToCustomer(${c.id},'${c.name.replace(/'/g, "\\'")}','${c.role || 'customer'}');closeModal();">
                <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(c.name)}&background=${bgColor}&color=fff" style="width:36px;height:36px;border-radius:50%;">
                <div>
                    <div style="font-weight:600;">${c.name} ${isAdmin ? '<span style="font-size:10px;padding:2px 8px;background:var(--danger);color:white;border-radius:10px;margin-left:6px;">ADMIN</span>' : ''}</div>
                    <div style="font-size:12px;color:var(--text-muted);">${c.email}</div>
                </div>
                ${isActive ? '<i class="ri-check-line" style="margin-left:auto;color:var(--accent);font-size:20px;"></i>' : ''}
            </div>
        `;
    });

    openModal(`
        <div class="modal-content" style="width:400px;">
            <div class="modal-head">
                <h2>Select Customer</h2>
                <i class="ri-close-line close-modal" onclick="closeModal()"></i>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;max-height:300px;overflow-y:auto;">
                ${list || '<p style="color:var(--text-muted);text-align:center;">No customers yet.</p>'}
            </div>
            <button class="primary-btn" style="width:100%;justify-content:center;margin-top:16px;" onclick="closeModal();openCustomerModal();">
                <i class="ri-user-add-line"></i> Register New Customer
            </button>
        </div>
    `);
}

// ============= MODALS =============

function openModal(html) {
    let overlay = document.querySelector('.modal-overlay');
    if (!overlay) { overlay = document.createElement('div'); overlay.className = 'modal-overlay'; document.body.appendChild(overlay); }
    overlay.innerHTML = html;
    setTimeout(() => overlay.classList.add('active'), 10);
}

function closeModal() {
    const overlay = document.querySelector('.modal-overlay');
    if (overlay) { overlay.classList.remove('active'); setTimeout(() => overlay.remove(), 300); }
}

function openBookModal() {
    openModal(`
        <div class="modal-content">
            <div class="modal-head"><h2>Add Book via Staff Service</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="createBook(event)">
                <div class="form-group"><label>Title</label><input type="text" id="b-title" class="form-input" required></div>
                <div class="form-group"><label>Author</label><input type="text" id="b-author" class="form-input" required></div>
                <div class="form-group"><label>Price ($)</label><input type="number" step="0.01" id="b-price" class="form-input" required></div>
                <div class="form-group"><label>Stock</label><input type="number" id="b-stock" class="form-input" required></div>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;margin-top:24px;">Confirm</button>
            </form>
        </div>
    `);
}

function openCustomerModal() {
    openModal(`
        <div class="modal-content">
            <div class="modal-head"><h2>Register Customer</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="createCustomer(event)">
                <div class="form-group"><label>Full Name</label><input type="text" id="c-name" class="form-input" required></div>
                <div class="form-group"><label>Email</label><input type="email" id="c-email" class="form-input" required></div>
                <p style="font-size:12px;color:var(--text-muted);margin:16px 0;">*Auto-creates a cart via cart-service</p>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;">Register</button>
            </form>
        </div>
    `);
}

// Initial Load — hide admin nav by default
loadView('store');
updateAdminNav();
