document.addEventListener("DOMContentLoaded", () => {
    // ── Elements Binding ──────────────────────────────────────────────────────
    const screen = document.getElementById("terminal-screen");
    const cartList = document.getElementById("cart-list");
    const itemCountBadge = document.getElementById("item-count");
    const cartSubtotal = document.getElementById("cart-subtotal");
    const cartTaxes = document.getElementById("cart-taxes");
    const cartTotal = document.getElementById("cart-total");
    const payBtn = document.getElementById("pay-btn");
    
    // Tabs switcher
    const tabCatalogBtn = document.getElementById("tab-catalog-btn");
    const tabKeypadBtn = document.getElementById("tab-keypad-btn");
    const panelCatalog = document.getElementById("panel-catalog");
    const panelKeypad = document.getElementById("panel-keypad");
    
    // Catalog searching and filtering
    const searchInput = document.getElementById("catalog-search");
    const categoryPills = document.querySelectorAll(".category-pill");
    const catalogGrid = document.getElementById("catalog-grid");
    
    let currentInput = "";
    let cachedProducts = [];
    let activeCategory = "Todos";
    let searchQuery = "";
    
    // ── Tab Navigation Controller ─────────────────────────────────────────────
    if (tabCatalogBtn && tabKeypadBtn) {
        tabCatalogBtn.addEventListener("click", () => {
            tabCatalogBtn.classList.add("active");
            tabKeypadBtn.classList.remove("active");
            panelCatalog.classList.add("active");
            panelKeypad.classList.remove("active");
            triggerTabAnimation(panelCatalog);
        });
        
        tabKeypadBtn.addEventListener("click", () => {
            tabKeypadBtn.classList.add("active");
            tabCatalogBtn.classList.remove("active");
            panelKeypad.classList.add("active");
            panelCatalog.classList.remove("active");
            triggerTabAnimation(panelKeypad);
        });
    }
    
    function triggerTabAnimation(element) {
        element.style.opacity = "0.2";
        element.style.transform = "translateY(5px)";
        setTimeout(() => {
            element.style.opacity = "1";
            element.style.transform = "translateY(0)";
            element.style.transition = "all 0.3s ease";
        }, 50);
    }
    
    // ── Classic Keypad Code-Typing Handler ────────────────────────────────────
    document.querySelectorAll(".num-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            if (currentInput.length < 8) {
                currentInput += btn.value;
                screen.textContent = currentInput;
                triggerHapticFeedback();
            }
        });
    });
    
    const delBtn = document.getElementById("del-btn");
    if (delBtn) {
        delBtn.addEventListener("click", () => {
            if (currentInput.length > 0) {
                currentInput = currentInput.slice(0, -1);
                screen.textContent = currentInput;
                triggerHapticFeedback();
            }
        });
    }
    
    const confirmBtn = document.getElementById("confirm-btn");
    if (confirmBtn) {
        confirmBtn.addEventListener("click", () => {
            if (currentInput) {
                addProductToCart(currentInput);
                currentInput = "";
                screen.textContent = "";
                triggerHapticFeedback();
            }
        });
    }
    
    function triggerHapticFeedback() {
        if (screen) {
            screen.style.transform = "scale(1.02)";
            setTimeout(() => screen.style.transform = "scale(1)", 80);
        }
    }
    
    // ── Visual Catalog Grid Renderers ──────────────────────────────────────────
    
    // Fetch products catalog
    async function loadCatalog() {
        if (!catalogGrid) return;
        
        try {
            const res = await fetch("/api/admin/products");
            if (!res.ok) throw new Error("Falha ao buscar catálogo");
            
            cachedProducts = await res.json();
            renderCatalog();
        } catch (error) {
            console.error("Erro ao carregar catálogo:", error);
            catalogGrid.innerHTML = `<p style="padding: 20px; color: var(--danger);">Erro ao carregar catálogo de produtos.</p>`;
        }
    }
    
    // Render product items in grid
    function renderCatalog() {
        if (!catalogGrid) return;
        
        catalogGrid.innerHTML = "";
        
        // Filter catalog by active category and search text
        const filtered = cachedProducts.filter(p => {
            const matchesCategory = activeCategory === "Todos" || p.category === activeCategory;
            const matchesSearch = p.name.toLowerCase().includes(searchQuery) || p.code.includes(searchQuery);
            return matchesCategory && matchesSearch;
        });
        
        if (filtered.length === 0) {
            catalogGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 40px; color: var(--text-muted);">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 10px; opacity: 0.5;">
                        <circle cx="11" cy="11" r="8"></circle>
                        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                    <p>Nenhum produto correspondente encontrado.</p>
                </div>
            `;
            return;
        }
        
        filtered.forEach(p => {
            const card = document.createElement("div");
            card.className = "product-card";
            card.setAttribute("data-code", p.code);
            card.innerHTML = `
                <div class="product-card-badge">Cód: ${p.code}</div>
                <div class="product-image-container">
                    <img src="/images/${p.image}" alt="${p.name}" onerror="this.src='/images/1zYZMU.png';">
                </div>
                <div class="product-card-info">
                    <span class="product-card-name">${p.name}</span>
                    <span class="product-card-desc">${p.description || "Nenhuma descrição disponível."}</span>
                </div>
                <div class="product-card-footer">
                    <span class="product-card-price">R$ ${p.price.toFixed(2).replace('.', ',')}</span>
                    <div class="product-card-add-btn">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </div>
                </div>
            `;
            
            // Add click listener
            card.addEventListener("click", () => {
                addProductToCart(p.code);
                animateCardAddition(card);
            });
            
            catalogGrid.appendChild(card);
        });
    }
    
    // Elegant fly animation feedback upon clicking a card
    function animateCardAddition(card) {
        card.style.transform = "scale(0.97)";
        card.style.borderColor = "var(--success)";
        setTimeout(() => {
            card.style.transform = "translateY(-4px)";
            card.style.borderColor = "var(--border-glass)";
        }, 150);
    }
    
    // Category pill listeners
    categoryPills.forEach(pill => {
        pill.addEventListener("click", () => {
            categoryPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            activeCategory = pill.getAttribute("data-category");
            renderCatalog();
        });
    });
    
    // Search input listener
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            renderCatalog();
        });
    }
    
    // ── Cart API Sync Layer ──────────────────────────────────────────────────
    
    // Load and render cart
    async function loadCart() {
        if (!cartList) return;
        
        try {
            const res = await fetch("/api/cart");
            if (!res.ok) throw new Error("Erro ao carregar o carrinho");
            
            const data = await res.json();
            renderCart(data);
        } catch (error) {
            console.error("Erro no sincronismo do carrinho:", error);
        }
    }
    
    // Render Cart DOM Rows
    function renderCart(data) {
        cartList.innerHTML = "";
        
        if (!data.items || data.items.length === 0) {
            cartList.innerHTML = `
                <div class="cart-empty">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="9" cy="21" r="1"></circle>
                        <circle cx="20" cy="21" r="1"></circle>
                        <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"></path>
                    </svg>
                    <p>Terminal Pronto.<br>Selecione produtos na grade ou digite o código ao lado.</p>
                </div>
            `;
            itemCountBadge.textContent = "0 itens";
            cartSubtotal.textContent = "R$ 0,00";
            cartTaxes.textContent = "R$ 0,00";
            cartTotal.textContent = "R$ 0,00";
            payBtn.disabled = true;
            return;
        }
        
        let totalItems = 0;
        data.items.forEach(item => {
            totalItems += item.quantity;
            const itemRow = document.createElement("div");
            itemRow.className = "cart-item";
            itemRow.innerHTML = `
                <div class="item-img">
                    <img src="/images/${item.image}" alt="${item.name}" onerror="this.style.display='none';">
                </div>
                <div class="item-info">
                    <span class="item-name">${item.name}</span>
                    <span class="item-details">Cód: ${item.code} | R$ ${item.price.toFixed(2).replace('.', ',')} un</span>
                </div>
                <div class="item-actions">
                    <button class="qty-btn dec-qty" data-code="${item.code}" data-qty="${item.quantity}">-</button>
                    <span class="item-qty">${item.quantity}</span>
                    <button class="qty-btn inc-qty" data-code="${item.code}" data-qty="${item.quantity}">+</button>
                    <span class="item-price">R$ ${item.subtotal.toFixed(2).replace('.', ',')}</span>
                    <button class="item-remove" data-code="${item.code}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            `;
            cartList.appendChild(itemRow);
        });
        
        // Add events to dynamically loaded buttons
        document.querySelectorAll(".dec-qty").forEach(btn => {
            btn.addEventListener("click", () => {
                const code = btn.getAttribute("data-code");
                const currentQty = parseInt(btn.getAttribute("data-qty"));
                updateQuantity(code, currentQty - 1);
            });
        });
        
        document.querySelectorAll(".inc-qty").forEach(btn => {
            btn.addEventListener("click", () => {
                const code = btn.getAttribute("data-code");
                const currentQty = parseInt(btn.getAttribute("data-qty"));
                updateQuantity(code, currentQty + 1);
            });
        });
        
        document.querySelectorAll(".item-remove").forEach(btn => {
            btn.addEventListener("click", () => {
                const code = btn.getAttribute("data-code");
                removeItem(code);
            });
        });
        
        // Calculate taxes & totals
        const sub = data.total;
        const tax = Math.round(sub * 0.0825 * 100) / 100;
        const tot = Math.round((sub + tax) * 100) / 100;
        
        itemCountBadge.textContent = `${totalItems} ${totalItems === 1 ? 'item' : 'itens'}`;
        cartSubtotal.textContent = `R$ ${sub.toFixed(2).replace('.', ',')}`;
        cartTaxes.textContent = `R$ ${tax.toFixed(2).replace('.', ',')}`;
        cartTotal.textContent = `R$ ${tot.toFixed(2).replace('.', ',')}`;
        payBtn.disabled = false;
    }
    
    // Add product to cart via API
    async function addProductToCart(code) {
        try {
            const res = await fetch("/api/cart/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code })
            });
            
            if (res.status === 404) {
                alert("Produto não cadastrado! Digite um código válido do catálogo.");
                return;
            }
            if (!res.ok) throw new Error("Erro ao adicionar produto");
            
            await loadCart();
        } catch (error) {
            console.error("Erro na requisição add:", error);
        }
    }
    
    // Update product quantity via API
    async function updateQuantity(code, newQty) {
        try {
            const res = await fetch("/api/cart/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code, quantity: newQty })
            });
            if (!res.ok) throw new Error("Erro ao atualizar quantidade");
            await loadCart();
        } catch (error) {
            console.error("Erro na requisição update:", error);
        }
    }
    
    // Remove item from cart via API
    async function removeItem(code) {
        try {
            const res = await fetch("/api/cart/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code })
            });
            if (!res.ok) throw new Error("Erro ao remover item");
            await loadCart();
        } catch (error) {
            console.error("Erro na requisição delete:", error);
        }
    }
    
    // Checkout action redirection
    if (payBtn) {
        payBtn.addEventListener("click", () => {
            window.location.href = "/SelectPayment";
        });
    }
    
    // ── Initializer Call ──────────────────────────────────────────────────────
    loadCatalog();
    loadCart();
});
