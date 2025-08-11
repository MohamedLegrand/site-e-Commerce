document.addEventListener('DOMContentLoaded', () => {
    console.log('Écouteur chargé');
    
    // Gestion des boutons "Ajouter au panier"
    const addToCartButtons = document.querySelectorAll('.btn-add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', () => {
            const productId = button.getAttribute('data-product-id');
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            if (!csrfToken) {
                showNotification('Erreur : Jeton CSRF manquant.', 'bg-red-500');
                return;
            }
            fetch(`${urls.addToCart.replace(/\/+$/, '')}/${productId}/`, {
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
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount && data.cart_item_count !== undefined) {
                        cartCount.textContent = data.cart_item_count;
                    }
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

    // Gestion des boutons "Mettre à jour"
    const updateButtons = document.querySelectorAll('.update-btn');
    updateButtons.forEach(button => {
        button.addEventListener('click', () => {
            console.log('Bouton Mettre à jour cliqué');
            const cartItem = button.closest('.cart-item');
            const productId = cartItem.getAttribute('data-product-id');
            console.log('Product ID:', productId);
            const quantityInput = cartItem.querySelector('.quantity-input');
            const quantity = parseInt(quantityInput.value) || 1;
            console.log('Quantity:', quantity);
            if (productId) {
                updateCartItem(productId, quantity);
            } else {
                console.error('Product ID non trouvé');
                showNotification('Erreur : ID du produit manquant.', 'bg-red-500');
            }
        });
    });

    // Gestion des boutons "Retirer"
    const removeButtons = document.querySelectorAll('.remove-btn');
    removeButtons.forEach(button => {
        button.addEventListener('click', () => {
            console.log('Bouton Retirer cliqué');
            const cartItem = button.closest('.cart-item');
            const productId = cartItem.getAttribute('data-product-id');
            console.log('Product ID:', productId);
            if (productId) {
                updateCartItem(productId, 0, 'remove');
            } else {
                console.error('Product ID non trouvé');
                showNotification('Erreur : ID du produit manquant.', 'bg-red-500');
            }
        });
    });

    // Gestion du bouton "Vider le Panier"
    const clearCartButton = document.querySelector('.clear-cart-btn');
    if (clearCartButton) {
        clearCartButton.addEventListener('click', () => {
            console.log('Bouton Vider le Panier cliqué');
            clearCart();
        });
    }

    function updateCartItem(productId, quantity, action = 'update') {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        fetch(`${urls.addToCart.replace(/\/+$/, '')}/${productId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ quantity: quantity, action: action })
        })
        .then(response => {
            console.log('Réponse reçue:', response);
            return response.json();
        })
        .then(data => {
            console.log('Données reçues:', data);
            if (data.status === 'success') {
                showNotification(data.message || 'Panier mis à jour !', 'bg-green-500');
                if (document.querySelector('.cart-items')) {
                    updateCartDisplay(data.cart_items, data.total);
                }
                const cartCount = document.querySelector('.cart-count');
                if (cartCount && data.cart_item_count !== undefined) {
                    cartCount.textContent = data.cart_item_count;
                }
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
            console.log('Réponse reçue:', response);
            return response.json();
        })
        .then(data => {
            console.log('Données reçues:', data);
            if (data.status === 'success') {
                showNotification(data.message || 'Panier vidé avec succès !', 'bg-green-500');
                if (document.querySelector('.cart-items')) {
                    updateCartDisplay(data.cart_items, data.total);
                }
                const cartCount = document.querySelector('.cart-count');
                if (cartCount) {
                    cartCount.textContent = data.cart_item_count || 0;
                }
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

    function updateCartDisplay(cartItems, total) {
        const cartItemsDiv = document.querySelector('.cart-items');
        if (cartItemsDiv) {
            cartItemsDiv.innerHTML = cartItems.map(item => `
                <div class="cart-item flex justify-between items-center p-4 mb-4 bg-white rounded-lg shadow" data-product-id="${item.product__id || item.product_id}">
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

// Ajout du code search.js sans modification des autres parties
// Début de search.js
$(document).ready(function() {
    $("#search-input").autocomplete({
        source: function(request, response) {
            $.ajax({
                url: "/product-autocomplete/",
                dataType: "json",
                data: {
                    term: request.term
                },
                success: function(data) {
                    response($.map(data, function(item) {
                        return {
                            label: item.label,
                            value: item.value,
                            price: item.price,
                            image: item.image
                        };
                    }));
                }
            });
        },
        minLength: 2,
        select: function(event, ui) {
            $("#search-input").val(ui.item.label);
            $("#product-price").text(ui.item.price + " FCFA");
            $("#product-image").attr("src", ui.item.image).attr("alt", ui.item.label);
            $("#add-to-cart-btn").data("product-id", ui.item.value).show();
            return false;
        }
    });

    // Gestion du bouton "Ajouter au panier"
    $("#add-to-cart-btn").on("click", function() {
        const productId = $(this).data("product-id");
        const csrfToken = $('[name=csrfmiddlewaretoken]').val();
        if (!csrfToken) {
            showNotification('Erreur : Jeton CSRF manquant.', 'bg-red-500');
            return;
        }
        fetch(`${urls.addToCart.replace(/\/+$/, '')}/${productId}/`, {
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
                const cartCount = $('.cart-count');
                if (cartCount.length && data.cart_item_count !== undefined) {
                    cartCount.text(data.cart_item_count); // Correction : utiliser .text() au lieu de .textContent
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

    function showNotification(message, bgClass) {
        const notification = $('<div>').addClass(`fixed top-4 right-4 ${bgClass} text-white px-4 py-2 rounded shadow-lg`).text(message);
        $('body').append(notification);
        setTimeout(() => notification.remove(), 3000);
    }
});
// Fin de search.js