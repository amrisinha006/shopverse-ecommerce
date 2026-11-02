import streamlit as st
import pandas as pd

from database import (
    init_db,
    get_products,
    get_categories,
    get_product,
    add_to_cart,
    get_cart,
    update_cart_quantity,
    checkout,
    get_user_orders,
    get_order_items,
    register_user,
    login_user,
    add_product,
    update_product,
    delete_product,
    get_all_orders,
    update_order_status,
    get_sales_summary
)

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------

st.set_page_config(
    page_title="ShopVerse | Online Store",
    page_icon="🛍️",
    layout="wide"
)

init_db()

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "selected_product" not in st.session_state:
    st.session_state.selected_product = None


# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def money(amount):
    return f"₹{amount:,.2f}"


def is_admin():
    if not st.session_state.user:
        return False

    try:
        return (
            st.session_state.user["email"]
            == st.secrets["ADMIN_EMAIL"]
        )
    except Exception:
        return False


def go_to(page):
    st.session_state.page = page
    st.rerun()


def logout():
    st.session_state.user = None
    st.session_state.page = "Home"
    st.rerun()


# -------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------

with st.sidebar:
    st.title("🛍️ ShopVerse")

    st.caption("Your everyday shopping destination")

    st.divider()

    if st.button("🏠 Home", use_container_width=True):
        go_to("Home")

    if st.button("🛒 Products", use_container_width=True):
        go_to("Products")

    if st.button("🛍️ My Cart", use_container_width=True):
        go_to("Cart")

    if st.button("📦 My Orders", use_container_width=True):
        go_to("Orders")

    if is_admin():
        if st.button("⚙️ Admin Dashboard",
                     use_container_width=True):
            go_to("Admin")

    st.divider()

    if st.session_state.user:
        st.write(
            f"Welcome, {st.session_state.user['name']}"
        )

        if st.button("Logout", use_container_width=True):
            logout()

    else:
        if st.button("Login / Register",
                     use_container_width=True):
            go_to("Account")


# -------------------------------------------------
# HOME PAGE
# -------------------------------------------------

def home_page():
    st.title("Welcome to ShopVerse 🛍️")

    st.subheader(
        "Discover products you'll love."
    )

    st.markdown("""
    Find electronics, fashion, accessories, and more.

    Shop conveniently from one place.
    """)

    st.divider()

    st.subheader("Featured Products")

    products = get_products()[:4]

    if not products:
        st.info("No products available.")

    cols = st.columns(4)

    for col, product in zip(cols, products):
        with col:
            if product["image_url"]:
                st.image(
                    product["image_url"],
                    use_container_width=True
                )

            st.markdown(f"**{product['name']}**")

            st.write(money(product["price"]))

            if st.button(
                "View Product",
                key=f"home_view_{product['id']}",
                use_container_width=True
            ):
                st.session_state.selected_product = (
                    product["id"]
                )

                go_to("Product Details")

    st.divider()

    if st.button(
        "Explore All Products",
        use_container_width=True
    ):
        go_to("Products")


# -------------------------------------------------
# ACCOUNT PAGE
# -------------------------------------------------

def account_page():
    st.title("Account")

    login_tab, register_tab = st.tabs([
        "Login",
        "Create Account"
    ])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("Email")

            password = st.text_input(
                "Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if submitted:
            user = login_user(email, password)

            if user:
                st.session_state.user = dict(user)

                st.success("Login successful!")

                go_to("Home")

            else:
                st.error("Invalid email or password.")

    with register_tab:
        with st.form("register_form"):
            name = st.text_input("Full Name")

            email = st.text_input(
                "Email Address",
                key="register_email"
            )

            password = st.text_input(
                "Create Password",
                type="password",
                key="register_password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

        if submitted:
            if not name.strip():
                st.error("Enter your name.")

            elif "@" not in email:
                st.error("Enter a valid email.")

            elif len(password) < 8:
                st.error(
                    "Password must contain at least 8 characters."
                )

            elif password != confirm_password:
                st.error("Passwords do not match.")

            else:
                success = register_user(
                    name.strip(),
                    email.strip(),
                    password
                )

                if success:
                    st.success(
                        "Account created. Please login."
                    )

                else:
                    st.error(
                        "An account with this email already exists."
                    )


# -------------------------------------------------
# PRODUCTS PAGE
# -------------------------------------------------

def products_page():
    st.title("Explore Products")

    search = st.text_input(
        "🔍 Search products",
        placeholder="Search for headphones, shoes..."
    )

    categories = get_categories()

    category = st.selectbox(
        "Category",
        categories
    )

    products = get_products(
        search=search,
        category=category
    )

    if not products:
        st.info("No products found.")

        return

    cols = st.columns(3)

    for index, product in enumerate(products):
        with cols[index % 3]:
            with st.container(border=True):
                if product["image_url"]:
                    st.image(
                        product["image_url"],
                        use_container_width=True
                    )

                st.markdown(
                    f"### {product['name']}"
                )

                st.caption(
                    product["category"]
                )

                st.write(
                    money(product["price"])
                )

                st.caption(
                    f"Available stock: {product['stock']}"
                )

                if st.button(
                    "View Details",
                    key=f"details_{product['id']}",
                    use_container_width=True
                ):
                    st.session_state.selected_product = (
                        product["id"]
                    )

                    go_to("Product Details")


# -------------------------------------------------
# PRODUCT DETAILS PAGE
# -------------------------------------------------

def product_details_page():
    product_id = st.session_state.selected_product

    if not product_id:
        st.warning("Select a product first.")

        return

    product = get_product(product_id)

    if not product:
        st.error("Product not found.")

        return

    left, right = st.columns([1, 1])

    with left:
        if product["image_url"]:
            st.image(
                product["image_url"],
                use_container_width=True
            )

    with right:
        st.title(product["name"])

        st.subheader(money(product["price"]))

        st.write(product["description"])

        st.write(
            f"Category: {product['category']}"
        )

        st.write(
            f"Available: {product['stock']}"
        )

        quantity = st.number_input(
            "Quantity",
            min_value=1,
            max_value=max(1, product["stock"]),
            value=1
        )

        if product["stock"] == 0:
            st.error("Out of stock.")

        elif st.button(
            "Add to Cart 🛒",
            use_container_width=True
        ):
            if not st.session_state.user:
                st.warning(
                    "Please login before adding products to your cart."
                )

                go_to("Account")

            else:
                success = add_to_cart(
                    st.session_state.user["id"],
                    product["id"],
                    int(quantity)
                )

                if success:
                    st.success("Added to cart!")

                else:
                    st.error("Insufficient stock.")

        if st.button("Back to Products"):
            go_to("Products")


# -------------------------------------------------
# CART PAGE
# -------------------------------------------------

def cart_page():
    st.title("🛒 Shopping Cart")

    if not st.session_state.user:
        st.warning("Please login to view your cart.")

        return

    user_id = st.session_state.user["id"]

    items = get_cart(user_id)

    if not items:
        st.info("Your cart is empty.")

        return

    total = 0

    for item in items:
        col1, col2, col3, col4 = st.columns(
            [3, 2, 2, 1]
        )

        with col1:
            st.write(f"**{item['name']}**")

            st.caption(
                money(item["price"])
            )

        with col2:
            quantity = st.number_input(
                "Quantity",
                min_value=0,
                max_value=max(1, item["stock"]),
                value=item["quantity"],
                key=f"cart_qty_{item['id']}"
            )

            if quantity != item["quantity"]:
                update_cart_quantity(
                    user_id,
                    item["id"],
                    int(quantity)
                )

                st.rerun()

        with col3:
            st.write(
                money(item["subtotal"])
            )

        with col4:
            if st.button(
                "Remove",
                key=f"remove_{item['id']}"
            ):
                update_cart_quantity(
                    user_id,
                    item["id"],
                    0
                )

                st.rerun()

        total += item["subtotal"]

        st.divider()

    st.subheader(
        f"Total: {money(total)}"
    )

    st.session_state.cart_total = total

    if st.button(
        "Proceed to Checkout",
        use_container_width=True
    ):
        go_to("Checkout")


# -------------------------------------------------
# CHECKOUT PAGE
# -------------------------------------------------

def checkout_page():
    st.title("Checkout")

    if not st.session_state.user:
        st.warning("Login to continue.")

        return

    items = get_cart(
        st.session_state.user["id"]
    )

    if not items:
        st.info("Your cart is empty.")

        return

    total = sum(
        item["subtotal"]
        for item in items
    )

    st.subheader("Order Summary")

    for item in items:
        st.write(
            f"{item['name']} × {item['quantity']} "
            f"— {money(item['subtotal'])}"
        )

    st.markdown(
        f"### Total: {money(total)}"
    )

    with st.form("checkout_form"):
        customer_name = st.text_input(
            "Full Name",
            value=st.session_state.user["name"]
        )

        address = st.text_area(
            "Delivery Address"
        )

        phone = st.text_input(
            "Phone Number"
        )

        payment_method = st.selectbox(
            "Payment Method",
            ["Cash on Delivery"]
        )

        submitted = st.form_submit_button(
            "Place Order",
            use_container_width=True
        )

    if submitted:
        if not customer_name.strip():
            st.error("Enter your full name.")

        elif not address.strip():
            st.error("Enter your delivery address.")

        elif not phone.strip():
            st.error("Enter your phone number.")

        else:
            order_id = checkout(
                st.session_state.user["id"],
                customer_name.strip(),
                address.strip(),
                phone.strip(),
                payment_method
            )

            if order_id:
                st.success(
                    f"Order #{order_id} placed successfully!"
                )

                go_to("Orders")

            else:
                st.error(
                    "Unable to place order. Check your cart and stock."
                )


# -------------------------------------------------
# MY ORDERS PAGE
# -------------------------------------------------

def orders_page():
    st.title("📦 My Orders")

    if not st.session_state.user:
        st.warning("Login to see your orders.")

        return

    orders = get_user_orders(
        st.session_state.user["id"]
    )

    if not orders:
        st.info("You haven't placed any orders.")

        return

    for order in orders:
        with st.expander(
            f"Order #{order['id']} — "
            f"{money(order['total'])}"
        ):
            st.write(
                f"Date: {order['created_at']}"
            )

            st.write(
                f"Status: {order['status']}"
            )

            st.write(
                f"Payment: {order['payment_method']}"
            )

            items = get_order_items(order["id"])

            for item in items:
                st.write(
                    f"{item['product_name']} × "
                    f"{item['quantity']} — "
                    f"{money(item['price'] * item['quantity'])}"
                )


# -------------------------------------------------
# ADMIN PAGE
# -------------------------------------------------

def admin_page():
    st.title("⚙️ Admin Dashboard")

    if not is_admin():
        st.error("Admin access required.")

        return

    summary = get_sales_summary()

    col1, col2 = st.columns(2)

    col1.metric(
        "Total Orders",
        summary["total_orders"]
    )

    col2.metric(
        "Total Revenue",
        money(summary["revenue"])
    )

    st.divider()

    add_tab, manage_tab, orders_tab = st.tabs([
        "Add Product",
        "Manage Products",
        "Manage Orders"
    ])

    with add_tab:
        with st.form("add_product_form"):
            name = st.text_input("Product Name")

            description = st.text_area(
                "Description"
            )

            category = st.text_input(
                "Category"
            )

            price = st.number_input(
                "Price",
                min_value=0.0,
                step=100.0
            )

            stock = st.number_input(
                "Stock",
                min_value=0,
                step=1
            )

            image_url = st.text_input(
                "Product Image URL"
            )

            submitted = st.form_submit_button(
                "Add Product"
            )

        if submitted:
            if name.strip() and category.strip():
                add_product(
                    name.strip(),
                    description,
                    category.strip(),
                    price,
                    int(stock),
                    image_url
                )

                st.success("Product added!")

                st.rerun()

            else:
                st.error(
                    "Product name and category are required."
                )

    with manage_tab:
        products = get_products()

        if products:
            df = pd.DataFrame(
                [dict(p) for p in products]
            )

            st.dataframe(
                df,
                use_container_width=True
            )

            product_ids = [
                p["id"]
                for p in products
            ]

            selected_id = st.selectbox(
                "Select Product",
                product_ids
            )

            selected = get_product(selected_id)

            with st.form("edit_product_form"):
                name = st.text_input(
                    "Name",
                    value=selected["name"]
                )

                description = st.text_area(
                    "Description",
                    value=selected["description"] or ""
                )

                category = st.text_input(
                    "Category",
                    value=selected["category"] or ""
                )

                price = st.number_input(
                    "Price",
                    min_value=0.0,
                    value=float(selected["price"])
                )

                stock = st.number_input(
                    "Stock",
                    min_value=0,
                    value=int(selected["stock"])
                )

                image_url = st.text_input(
                    "Image URL",
                    value=selected["image_url"] or ""
                )

                submitted = st.form_submit_button(
                    "Save Changes"
                )

            if submitted:
                update_product(
                    selected_id,
                    name,
                    description,
                    category,
                    price,
                    int(stock),
                    image_url
                )

                st.success("Product updated!")

                st.rerun()

            if st.button(
                "Delete Selected Product",
                type="primary"
            ):
                delete_product(selected_id)

                st.success("Product removed.")

                st.rerun()

    with orders_tab:
        orders = get_all_orders()

        if orders:
            st.dataframe(
                pd.DataFrame(
                    [dict(o) for o in orders]
                ),
                use_container_width=True
            )

            order_ids = [
                order["id"]
                for order in orders
            ]

            selected_order = st.selectbox(
                "Select Order",
                order_ids
            )

            status = st.selectbox(
                "Update Order Status",
                [
                    "Pending",
                    "Confirmed",
                    "Shipped",
                    "Delivered",
                    "Cancelled"
                ]
            )

            if st.button("Update Status"):
                update_order_status(
                    selected_order,
                    status
                )

                st.success("Order status updated!")

                st.rerun()


# -------------------------------------------------
# PAGE ROUTER
# -------------------------------------------------

page = st.session_state.page

if page == "Home":
    home_page()

elif page == "Account":
    account_page()

elif page == "Products":
    products_page()

elif page == "Product Details":
    product_details_page()

elif page == "Cart":
    cart_page()

elif page == "Checkout":
    checkout_page()

elif page == "Orders":
    orders_page()

elif page == "Admin":
    admin_page()