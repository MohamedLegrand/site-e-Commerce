document.addEventListener('DOMContentLoaded', () => {
    const addToCartButtons = document.querySelectorAll('.btn-add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', () => {
            const productId = button.getAttribute('data-product-id');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (!csrfToken) {
                showNotification('Erreur : Jeton CSRF manquant.', 'bg-red-500');
                return;
            }
            console.log(`Ajout au panier : Envoi pour produit ID ${productId}`);
            fetch(urls.addToCart.replace('0', productId), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ quantity: 1, action: 'add' })
            })
            .then(response => {
                console.log(`Réponse reçue pour ajout : Statut ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    showNotification(data.message, 'bg-green-500');
                    updateCartDisplay(data.cart_items, data.total, data.cart_item_count);
                } else {
                    showNotification('Erreur : ' + data.message, 'bg-red-500');
                }
            })
            .catch(error => {
                console.error('Erreur lors de l\'ajout au panier:', error);
                showNotification('Une erreur est survenue lors de l\'ajout au panier.', 'bg-red-500');
            });
        });
    });

    // Ajout des boutons de modification dans le détail du panier
    document.querySelectorAll('.cart-item').forEach(item => {
        const productId = item.getAttribute('data-product-id');
        const quantityInput = item.querySelector('.quantity-input');
        const updateBtn = item.querySelector('.update-btn');
        const removeBtn = item.querySelector('.remove-btn');

        if (updateBtn) {
            updateBtn.addEventListener('click', () => {
                const quantity = parseInt(quantityInput.value) || 1;
                updateCartItem(productId, quantity);
            });
        }
        if (removeBtn) {
            removeBtn.addEventListener('click', () => {
                updateCartItem(productId, 0, 'remove');
            });
        }
    });

    // Bouton pour vider le panier
    const clearCartBtn = document.querySelector('.clear-cart-btn');
    if (clearCartBtn) {
        clearCartBtn.addEventListener('click', () => {
            clearCart();
        });
    }

    function updateCartItem(productId, quantity, action = 'update') {
    console.log(`Modification : Envoi pour produit ID ${productId}, quantité ${quantity}, action ${action}, URL ${urls.addToCart.replace(/0$/, productId)}`);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    fetch(urls.addToCart.replace(/0$/, productId), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ quantity: quantity, action: action })
    })
    .then(response => {
        console.log(`Réponse reçue pour modification : Statut ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showNotification(data.message, 'bg-green-500');
            updateCartDisplay(data.cart_items, data.total, data.cart_item_count);
        } else {
            showNotification('Erreur : ' + data.message, 'bg-red-500');
        }
    })
    .catch(error => {
        console.error('Erreur lors de la modification:', error);
        showNotification('Une erreur est survenue lors de la modification.', 'bg-red-500');
    });
}
    function clearCart() {
        console.log('Vidage : Envoi de la requête pour vider le panier');
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        fetch(urls.clearCart, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({})
        })
        .then(response => {
            console.log(`Réponse reçue pour vidage : Statut ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                showNotification(data.message, 'bg-green-500');
                updateCartDisplay(data.cart_items, data.total, data.cart_item_count);
            } else {
                showNotification('Erreur : ' + data.message, 'bg-red-500');
            }
        })
        .catch(error => {
            console.error('Erreur lors du vidage du panier:', error);
            showNotification('Une erreur est survenue lors du vidage du panier.', 'bg-red-500');
        });
    }

    function showNotification(message, bgClass) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 ${bgClass} text-white px-4 py-2 rounded shadow-lg`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    function updateCartDisplay(cartItems, total, cartItemCount) {
        const cartItemsDiv = document.querySelector('.cart-items');
        if (cartItemsDiv) {
            cartItemsDiv.innerHTML = cartItems.map(item => `
                <div class="cart-item flex justify-between items-center p-4 mb-4 bg-white rounded-lg shadow" data-product-id="${item.product__name.split(' ').join('_')}">
                    <span>${item.product__name} - <input type="number" class="quantity-input w-16 p-1 border rounded" value="${item.quantity}" min="0"></span>
                    <div>
                        <button class="update-btn bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600">Mettre à jour</button>
                        <button class="remove-btn bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 ml-2">Retirer</button>
                        <span>${item.product__price * item.quantity} FCFA</span>
                    </div>
                </div>
            `).join('');
            const totalElement = document.querySelector('.cart-total h3');
            if (totalElement) {
                totalElement.textContent = `Total : ${total || 0} FCFA`;
            }
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) {
                cartCount.textContent = cartItemCount || 0;
            }
        }
    }

    function scrollCarousel(sectionId, direction) {
        const container = document.getElementById(sectionId);
        const scrollAmount = 300;
        container.scrollLeft += direction * scrollAmount;
    }
});