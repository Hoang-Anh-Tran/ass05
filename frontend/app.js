const API_URL = "http://localhost:4000";
const contentArea = document.getElementById("content-area");

const appState = {
    currentView: 'store',
    customerId: null,
    customerName: 'Guest',
    customerRole: 'customer'
};

// --- Nav Visibility by Role ---
function updateAdminNav() {
    const staffLabel = document.getElementById('staff-nav-label');
    const staffItems = document.querySelectorAll('.staff-nav-item');
    const adminLabel = document.getElementById('admin-nav-label');
    const adminItems = document.querySelectorAll('.admin-nav-item');
    const isAdmin = appState.customerRole === 'admin';
    const isStaff = appState.customerRole === 'staff';
    const canManageBooks = isAdmin || isStaff;

    // Staff section: visible for staff and admin
    if (staffLabel) staffLabel.style.display = canManageBooks ? '' : 'none';
    staffItems.forEach(el => el.style.display = canManageBooks ? '' : 'none');

    // Admin section: visible for admin only
    if (adminLabel) adminLabel.style.display = isAdmin ? '' : 'none';
    adminItems.forEach(el => el.style.display = isAdmin ? '' : 'none');

    // Redirect if on unauthorized page
    const adminOnlyViews = ['dashboard', 'customers'];
    const staffViews = ['books', 'vouchers'];
    if (!canManageBooks && staffViews.includes(appState.currentView)) {
        document.querySelector('.nav-item[data-target="store"]').click();
    }
    if (!isAdmin && adminOnlyViews.includes(appState.currentView)) {
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
            case 'vouchers': renderVouchers(); break;
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
                    <button class="card-btn" onclick="openReviewsModal(${b.id}, '${b.title.replace(/'/g, "\\'")}')" title="View Reviews"><i class="ri-chat-3-line"></i> Reviews</button>
                    <button class="card-btn" onclick="openRateModal(${b.id}, '${b.title.replace(/'/g, "\\'")}')" title="Write a Review"><i class="ri-star-line"></i> Rate</button>
                </div>
            </div>
        `;
    });

    html += `</div></div>`;
    contentArea.innerHTML = html;
}

// ============= FEATURE 1: VIEW REVIEWS MODAL =============

async function openReviewsModal(bookId, bookTitle) {
    const reviews = await apiCall(`/comments/?book_id=${bookId}`) || [];
    const customers = await apiCall("/customers/") || [];
    const customerMap = {};
    customers.forEach(c => { customerMap[c.id] = c.name; });

    let reviewHtml = '';
    if (reviews.length > 0) {
        reviews.forEach(r => {
            const customerName = customerMap[r.customer_id] || `Customer #${r.customer_id}`;
            reviewHtml += `
                <div class="review-item">
                    <div class="review-header">
                        <span class="review-customer"><i class="ri-user-line" style="margin-right:4px;"></i>${customerName}</span>
                        <span>${renderStars(r.rating, 14)}</span>
                    </div>
                    <div class="review-text">${r.comment || '<em>No comment</em>'}</div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">${r.created_at ? new Date(r.created_at).toLocaleDateString() : ''}</div>
                </div>
            `;
        });
    } else {
        reviewHtml = '<p style="color:var(--text-muted);text-align:center;padding:32px;">No reviews yet for this book.</p>';
    }

    // Calculate average
    let avgHtml = '';
    if (reviews.length > 0) {
        const avgRating = (reviews.reduce((s, r) => s + r.rating, 0) / reviews.length).toFixed(1);
        avgHtml = `
            <div style="text-align:center;padding:16px 0;border-bottom:1px solid var(--border-color);margin-bottom:8px;">
                <div style="font-size:32px;font-weight:700;color:var(--accent);">${avgRating}</div>
                <div style="margin:4px 0;">${renderStars(Math.round(avgRating), 20)}</div>
                <div style="font-size:13px;color:var(--text-muted);">${reviews.length} review(s)</div>
            </div>
        `;
    }

    openModal(`
        <div class="modal-content" style="width:500px;">
            <div class="modal-head">
                <h2><i class="ri-chat-3-line" style="color:var(--accent);"></i> Reviews for "${bookTitle}"</h2>
                <i class="ri-close-line close-modal" onclick="closeModal()"></i>
            </div>
            ${avgHtml}
            <div style="max-height:350px;overflow-y:auto;padding:0 4px;">
                ${reviewHtml}
            </div>
            <button class="primary-btn" style="width:100%;justify-content:center;margin-top:16px;" onclick="openRateModal(${bookId},'${bookTitle.replace(/'/g, "\\'")}')">
                <i class="ri-edit-line"></i> Write a Review
            </button>
        </div>
    `);
}

// ============= CART =============

let cachedCartTotal = 0;
let appliedVoucher = null; // { code, discount_percent }

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
        appliedVoucher = null;
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

    // Voucher input section
    html += `
        <div class="voucher-section" style="margin-top:24px;padding:20px 24px;background:var(--bg-card,var(--bg-secondary));border-radius:16px;border:1px solid var(--border-color);">
            <div style="display:flex;align-items:center;gap:12px;">
                <i class="ri-coupon-3-line" style="font-size:20px;color:var(--accent);"></i>
                <input type="text" id="voucher-input" class="form-input" placeholder="Enter voucher code..." style="flex:1;margin:0;">
                <button class="primary-btn" onclick="applyVoucher()" style="white-space:nowrap;"><i class="ri-check-line"></i> Apply</button>
                ${appliedVoucher ? `<button class="card-btn" style="flex:none;width:40px;color:var(--danger);" onclick="removeVoucher()"><i class="ri-close-line"></i></button>` : ''}
            </div>
            ${appliedVoucher ? `<div class="voucher-applied" style="margin-top:12px;padding:8px 16px;background:rgba(5,205,153,0.1);border-radius:8px;display:flex;align-items:center;gap:8px;"><i class="ri-checkbox-circle-fill" style="color:var(--success);"></i><span style="font-weight:600;color:var(--success);">Voucher "${appliedVoucher.code}" applied — ${appliedVoucher.discount_percent}% OFF</span></div>` : ''}
        </div>
    `;

    // Total section with discount
    const discountAmount = appliedVoucher ? grandTotal * (appliedVoucher.discount_percent / 100) : 0;
    const finalTotal = grandTotal - discountAmount;

    html += `
        <div style="display:flex;flex-direction:column;gap:8px;margin-top:24px;padding:20px 24px;background:var(--bg-card,var(--bg-secondary));border-radius:16px;border:1px solid var(--border-color);">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:14px;color:var(--text-muted);">${cartData.items.length} item(s) · Subtotal</div>
                <div style="font-size:18px;font-weight:600;color:var(--text-main);">$${grandTotal.toFixed(2)}</div>
            </div>
            ${appliedVoucher ? `
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div style="font-size:14px;color:var(--success);"><i class="ri-coupon-3-line"></i> Discount (${appliedVoucher.discount_percent}%)</div>
                <div style="font-size:18px;font-weight:600;color:var(--success);">-$${discountAmount.toFixed(2)}</div>
            </div>
            ` : ''}
            <div style="display:flex;justify-content:space-between;align-items:center;border-top:2px solid var(--border-color);padding-top:12px;margin-top:4px;">
                <div style="font-size:14px;color:var(--text-muted);">Total</div>
                <div style="font-weight:700;font-size:28px;color:var(--accent);">$${finalTotal.toFixed(2)}</div>
            </div>
        </div>
    `;

    cachedCartTotal = finalTotal;
    container.innerHTML = html;
}

// ============= FEATURE 3: VOUCHER APPLICATION =============

async function applyVoucher() {
    const codeInput = document.getElementById('voucher-input');
    const code = codeInput ? codeInput.value.trim() : '';
    if (!code) { showToast("Please enter a voucher code", "error"); return; }

    const res = await apiCall(`/catalog/vouchers/?code=${encodeURIComponent(code)}`);
    if (res && !res.error) {
        appliedVoucher = { code: res.code, discount_percent: res.discount_percent };
        showToast(`Voucher applied! ${res.discount_percent}% discount`);
        renderCart();
    } else {
        showToast("Invalid or inactive voucher code", "error");
    }
}

function removeVoucher() {
    appliedVoucher = null;
    showToast("Voucher removed");
    renderCart();
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

// ============= FEATURE 4: ADMIN MANAGE BOOKS (with EDIT) =============

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
        const stockColor = b.stock > 10 ? 'var(--success)' : b.stock > 0 ? '#f5a623' : 'var(--danger)';
        html += `
            <div class="data-card">
                <div class="card-icon"><i class="ri-book-2-line"></i></div>
                <h3>${b.title}</h3>
                <p>by ${b.author}</p>
                <div style="font-weight:600;font-size:18px;margin-bottom:16px;color:var(--accent);">$${b.price} <span style="font-size:12px;font-weight:400;color:${stockColor}">| Stock: ${b.stock}</span></div>
                <div class="card-actions">
                    <button class="card-btn" onclick="openRestockModal(${b.id}, '${b.title.replace(/'/g, "\\'")}')"><i class="ri-add-box-line"></i> Restock</button>
                    <button class="card-btn" onclick="openEditBookModal(${b.id}, '${b.title.replace(/'/g, "\\'")}'  , '${b.author.replace(/'/g, "\\'")}', ${b.price}, ${b.stock})"><i class="ri-edit-line"></i> Edit</button>
                </div>
            </div>
        `;
    });
    html += `</div></div>`;
    contentArea.innerHTML = html;
}

function openEditBookModal(bookId, title, author, price, stock) {
    openModal(`
        <div class="modal-content">
            <div class="modal-head"><h2><i class="ri-edit-line" style="color:var(--accent);"></i> Edit Book</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="updateBook(event, ${bookId})">
                <div class="form-group"><label>Title</label><input type="text" id="eb-title" class="form-input" value="${title}" required></div>
                <div class="form-group"><label>Author</label><input type="text" id="eb-author" class="form-input" value="${author}" required></div>
                <div class="form-group"><label>Price ($)</label><input type="number" step="0.01" id="eb-price" class="form-input" value="${price}" required></div>
                <div class="form-group"><label>Stock</label><input type="number" id="eb-stock" class="form-input" value="${stock}" required></div>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;margin-top:24px;"><i class="ri-save-line"></i> Save Changes</button>
            </form>
        </div>
    `);
}

async function updateBook(e, bookId) {
    e.preventDefault();
    const data = {
        title: document.getElementById('eb-title').value,
        author: document.getElementById('eb-author').value,
        price: parseFloat(document.getElementById('eb-price').value),
        stock: parseInt(document.getElementById('eb-stock').value)
    };
    const res = await apiCall(`/staff/${bookId}/`, 'PUT', data);
    if (res && !res.error) {
        showToast("Book updated!");
        closeModal();
        renderBooks();
    }
}

function openRestockModal(bookId, bookTitle) {
    openModal(`
        <div class="modal-content">
            <div class="modal-head"><h2><i class="ri-add-box-line" style="color:var(--accent);"></i> Restock "${bookTitle}"</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="restockBook(event, ${bookId})">
                <div class="form-group"><label>Quantity to Add</label><input type="number" id="rs-qty" class="form-input" min="1" placeholder="e.g. 50" required></div>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;margin-top:24px;"><i class="ri-add-box-line"></i> Add Stock</button>
            </form>
        </div>
    `);
}

async function restockBook(e, bookId) {
    e.preventDefault();
    const addQty = parseInt(document.getElementById('rs-qty').value);
    // Fetch current book to get current stock
    const books = await apiCall('/books/') || [];
    const book = books.find(b => b.id === bookId);
    if (!book) { showToast('Book not found', 'error'); return; }
    const newStock = book.stock + addQty;
    const res = await apiCall(`/staff/${bookId}/`, 'PUT', { stock: newStock });
    if (res && !res.error) {
        showToast(`Restocked! New stock: ${newStock}`);
        closeModal();
        renderBooks();
    }
}

// ============= FEATURE 2: ADMIN VOUCHER MANAGEMENT =============

async function renderVouchers() {
    const vouchers = await apiCall("/catalog/vouchers/") || [];
    let html = `
        <div class="view-section">
            <div class="page-header">
                <div><h1><i class="ri-coupon-3-line" style="color:var(--accent);"></i> Manage Vouchers</h1><p>Total: ${vouchers.length}</p></div>
                <button class="primary-btn" onclick="openVoucherModal()"><i class="ri-add-line"></i> Create Voucher</button>
            </div>
            <div class="grid-cards">
    `;

    if (vouchers.length === 0) {
        html += `<div style="text-align:center;padding:40px;color:var(--text-muted);grid-column:1/-1;"><i class="ri-coupon-3-line" style="font-size:48px;display:block;margin-bottom:12px;"></i>No vouchers yet. Create one!</div>`;
    }

    vouchers.forEach(v => {
        const statusColor = v.active ? 'var(--success)' : 'var(--danger)';
        const statusText = v.active ? 'Active' : 'Inactive';
        html += `
            <div class="data-card">
                <div class="card-icon" style="background:${v.active ? 'rgba(5,205,153,0.1)' : 'rgba(238,93,80,0.1)'};color:${statusColor};"><i class="ri-coupon-3-line"></i></div>
                <h3 style="font-family:monospace;letter-spacing:2px;">${v.code}</h3>
                <div style="font-weight:700;font-size:28px;color:var(--accent);margin:8px 0;">${v.discount_percent}% OFF</div>
                <div style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;color:${statusColor};background:${v.active ? 'rgba(5,205,153,0.1)' : 'rgba(238,93,80,0.1)'};">${statusText}</div>
                <div class="card-actions" style="margin-top:16px;">
                    <button class="card-btn" onclick="toggleVoucher(${v.id}, ${v.active})"><i class="ri-${v.active ? 'pause' : 'play'}-line"></i> ${v.active ? 'Deactivate' : 'Activate'}</button>
                    <button class="card-btn" onclick="openEditVoucherModal(${v.id}, '${v.code}', ${v.discount_percent}, ${v.active})"><i class="ri-edit-line"></i> Edit</button>
                    <button class="card-btn" style="color:var(--danger);" onclick="deleteVoucher(${v.id})"><i class="ri-delete-bin-line"></i></button>
                </div>
            </div>
        `;
    });

    html += `</div></div>`;
    contentArea.innerHTML = html;
}

function openVoucherModal() {
    openModal(`
        <div class="modal-content">
            <div class="modal-head"><h2><i class="ri-coupon-3-line" style="color:var(--accent);"></i> Create Voucher</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="createVoucher(event)">
                <div class="form-group"><label>Voucher Code</label><input type="text" id="v-code" class="form-input" placeholder="e.g. SAVE20" required></div>
                <div class="form-group"><label>Discount (%)</label><input type="number" id="v-discount" class="form-input" min="1" max="100" placeholder="1-100" required></div>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;margin-top:24px;"><i class="ri-add-line"></i> Create</button>
            </form>
        </div>
    `);
}

function openEditVoucherModal(id, code, discount, active) {
    openModal(`
        <div class="modal-content">
            <div class="modal-head"><h2><i class="ri-edit-line" style="color:var(--accent);"></i> Edit Voucher</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="updateVoucher(event, ${id})">
                <div class="form-group"><label>Voucher Code</label><input type="text" id="ev-code" class="form-input" value="${code}" required></div>
                <div class="form-group"><label>Discount (%)</label><input type="number" id="ev-discount" class="form-input" value="${discount}" min="1" max="100" required></div>
                <div class="form-group"><label style="display:flex;align-items:center;gap:8px;"><input type="checkbox" id="ev-active" ${active ? 'checked' : ''}> Active</label></div>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;margin-top:24px;"><i class="ri-save-line"></i> Save</button>
            </form>
        </div>
    `);
}

async function createVoucher(e) {
    e.preventDefault();
    const data = {
        code: document.getElementById('v-code').value.toUpperCase(),
        discount_percent: parseInt(document.getElementById('v-discount').value),
        active: true
    };
    const res = await apiCall('/catalog/vouchers/', 'POST', data);
    if (res && !res.error) { showToast("Voucher created!"); closeModal(); renderVouchers(); }
}

async function updateVoucher(e, id) {
    e.preventDefault();
    const data = {
        code: document.getElementById('ev-code').value.toUpperCase(),
        discount_percent: parseInt(document.getElementById('ev-discount').value),
        active: document.getElementById('ev-active').checked
    };
    const res = await apiCall(`/catalog/vouchers/${id}/`, 'PUT', data);
    if (res && !res.error) { showToast("Voucher updated!"); closeModal(); renderVouchers(); }
}

async function toggleVoucher(id, currentActive) {
    const res = await apiCall(`/catalog/vouchers/${id}/`, 'PUT', { active: !currentActive });
    if (res && !res.error) { showToast(currentActive ? "Voucher deactivated" : "Voucher activated"); renderVouchers(); }
}

async function deleteVoucher(id) {
    if (!confirm("Delete this voucher?")) return;
    await apiCall(`/catalog/vouchers/${id}/`, 'DELETE');
    showToast("Voucher deleted");
    renderVouchers();
}

// ============= CUSTOMERS =============

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
    apiCall('/cart/items/', 'POST', { customer_id: appState.customerId, book_id: bookId, quantity: 1 })
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
    const data = {
        name: document.getElementById('c-name').value,
        email: document.getElementById('c-email').value,
        password: document.getElementById('c-password').value
    };
    const res = await apiCall('/customers/', 'POST', data);
    if (res) {
        showToast("Customer registered! Cart auto-created.");
        closeModal();
        switchToCustomer(res.id, res.name, res.role);
        if (appState.currentView === 'customers') renderCustomers();
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
    appliedVoucher = null;
    const bgColor = role === 'admin' ? 'e53e3e' : role === 'staff' ? 'e88e0a' : '4318ff';
    document.getElementById('user-avatar').src = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=${bgColor}&color=fff`;
    const roleLabel = role === 'admin' ? ' (Admin)' : role === 'staff' ? ' (Staff)' : '';
    document.getElementById('user-name').textContent = `${name}${roleLabel}`;
    updateAdminNav();
    showToast(`Logged in as ${name}${roleLabel}`);
    if (appState.currentView === 'store') renderStore();
}

function logout() {
    appState.customerId = null;
    appState.customerName = 'Guest';
    appState.customerRole = 'customer';
    appliedVoucher = null;
    cachedCartTotal = 0;
    document.getElementById('user-avatar').src = 'https://ui-avatars.com/api/?name=Guest&background=4318ff&color=fff';
    document.getElementById('user-name').textContent = 'Guest';
    updateAdminNav();
    closeModal();
    showToast('Logged out successfully');
    document.querySelector('.nav-item[data-target="store"]').click();
}

// ============= CHECKOUT (FEATURE 5: CLEAR CART AFTER SUCCESS) =============

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
                ${appliedVoucher ? `<div class="checkout-row" style="color:var(--success);"><span>Voucher (${appliedVoucher.discount_percent}% OFF)</span><span>Applied</span></div>` : ''}
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
            // FEATURE 5: Clear cart after successful checkout
            await apiCall(`/cart/clear/${appState.customerId}/`, 'DELETE');
            appliedVoucher = null; // Reset voucher after checkout
            cachedCartTotal = 0;
            showToast(`Order placed! $${data.total_amount.toFixed(2)}`);
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
    if (appState.customerId) {
        // Logged in: show user info + logout
        const isAdmin = appState.customerRole === 'admin';
        const isStaff = appState.customerRole === 'staff';
        const bgColor = isAdmin ? 'e53e3e' : isStaff ? 'e88e0a' : '4318ff';
        const roleBadge = isAdmin ? '<span style="font-size:10px;padding:2px 8px;background:var(--danger);color:white;border-radius:10px;margin-left:6px;">ADMIN</span>' : isStaff ? '<span style="font-size:10px;padding:2px 8px;background:#e88e0a;color:white;border-radius:10px;margin-left:6px;">STAFF</span>' : '';
        openModal(`
            <div class="modal-content" style="width:400px;">
                <div class="modal-head">
                    <h2>Account</h2>
                    <i class="ri-close-line close-modal" onclick="closeModal()"></i>
                </div>
                <div style="display:flex;align-items:center;gap:16px;padding:20px;background:var(--bg-primary);border-radius:var(--radius-md);margin-bottom:20px;">
                    <img src="https://ui-avatars.com/api/?name=${encodeURIComponent(appState.customerName)}&background=${bgColor}&color=fff" style="width:48px;height:48px;border-radius:50%;">
                    <div>
                        <div style="font-weight:700;font-size:18px;">${appState.customerName} ${roleBadge}</div>
                        <div style="font-size:13px;color:var(--text-muted);margin-top:2px;">Logged in</div>
                    </div>
                </div>
                <button class="primary-btn" style="width:100%;justify-content:center;background:var(--danger);box-shadow:0 4px 12px rgba(238,93,80,0.2);" onclick="logout()">
                    <i class="ri-logout-box-line"></i> Logout
                </button>
            </div>
        `);
    } else {
        // Not logged in: show login/register
        openModal(`
            <div class="modal-content" style="width:400px;">
                <div class="modal-head">
                    <h2>Welcome</h2>
                    <i class="ri-close-line close-modal" onclick="closeModal()"></i>
                </div>
                <div style="text-align:center;padding:24px 0;">
                    <i class="ri-user-line" style="font-size:48px;color:var(--text-muted);"></i>
                    <p style="color:var(--text-muted);margin-top:12px;">Please login or register to continue</p>
                </div>
                <div style="display:flex;gap:12px;">
                    <button class="primary-btn" style="flex:1;justify-content:center;" onclick="openLoginModal()">
                        <i class="ri-login-box-line"></i> Login
                    </button>
                    <button class="primary-btn" style="flex:1;justify-content:center;background:var(--success);box-shadow:0 4px 12px rgba(5,205,153,0.2);" onclick="openCustomerModal()">
                        <i class="ri-user-add-line"></i> Register
                    </button>
                </div>
            </div>
        `);
    }
}

// ============= LOGIN MODAL =============

function openLoginModal() {
    openModal(`
        <div class="modal-content">
            <div class="modal-head"><h2><i class="ri-login-box-line" style="color:var(--accent);"></i> Login</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="loginCustomer(event)">
                <div class="form-group"><label>Email</label><input type="email" id="l-email" class="form-input" placeholder="Enter your email" required></div>
                <div class="form-group"><label>Password</label><input type="password" id="l-password" class="form-input" placeholder="Enter your password" required></div>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;margin-top:24px;"><i class="ri-login-box-line"></i> Login</button>
            </form>
            <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--text-muted);">Don't have an account? <a href="#" onclick="openCustomerModal();return false;" style="color:var(--accent);font-weight:600;">Register</a></p>
        </div>
    `);
}

async function loginCustomer(e) {
    e.preventDefault();
    const data = {
        email: document.getElementById('l-email').value,
        password: document.getElementById('l-password').value
    };
    const res = await apiCall('/customers/login/', 'POST', data);
    if (res && !res.error) {
        showToast(`Welcome back, ${res.name}!`);
        closeModal();
        switchToCustomer(res.id, res.name, res.role);
    }
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
            <div class="modal-head"><h2><i class="ri-user-add-line" style="color:var(--accent);"></i> Register</h2><i class="ri-close-line close-modal" onclick="closeModal()"></i></div>
            <form onsubmit="createCustomer(event)">
                <div class="form-group"><label>Full Name</label><input type="text" id="c-name" class="form-input" placeholder="Enter your full name" required></div>
                <div class="form-group"><label>Email</label><input type="email" id="c-email" class="form-input" placeholder="Enter your email" required></div>
                <div class="form-group"><label>Password</label><input type="password" id="c-password" class="form-input" placeholder="Create a password" required></div>
                <p style="font-size:12px;color:var(--text-muted);margin:16px 0;">*Auto-creates a cart via cart-service</p>
                <button type="submit" class="primary-btn" style="width:100%;justify-content:center;"><i class="ri-user-add-line"></i> Register</button>
            </form>
            <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--text-muted);">Already have an account? <a href="#" onclick="openLoginModal();return false;" style="color:var(--accent);font-weight:600;">Login</a></p>
        </div>
    `);
}

// Initial Load — hide admin nav by default
loadView('store');
updateAdminNav();
