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
            fetch(`/accounts/add_to_cart/${productId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ quantity: 1 })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showNotification('Produit ajouté au panier !', 'bg-green-500');
                    // Mettre à jour le compteur dans la barre de navigation
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount && data.cart_item_count !== undefined) {
                        cartCount.textContent = data.cart_item_count;
                    }
                    // Mettre à jour la page du panier si applicable
                    if (document.querySelector('.cart-items')) {
                        updateCartDisplay(data.cart_items, data.total);
                    }
                } else {
                    showNotification('Erreur : ' + data.message, 'bg-red-500');
                }
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification('Une erreur est survenue lors de l\'ajout au panier.', 'bg-red-500');
            });
        });
    });

    function showNotification(message, bgClass) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 ${bgClass} text-white px-4 py-2 rounded shadow-lg`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    function updateCartDisplay(cartItems, total) {
        const cartItemsDiv = document.querySelector('.cart-items');
        if (cartItemsDiv) {
            cartItemsDiv.innerHTML = cartItems.map(item => `
                <div class="cart-item flex justify-between items-center p-4 mb-4 bg-white rounded-lg shadow">
                    <span>${item.product__name} - ${item.quantity} x ${item.product__price} FCFA</span>
                    <span>${item.product__price * item.quantity} FCFA</span>
                </div>
            `).join('');
            const totalElement = document.querySelector('.cart-total h3');
            if (totalElement) {
                totalElement.textContent = `Total : ${total} FCFA`;
            }
        }
    }
});