import streamlit as st
import sqlite3
import pandas as pd
import datetime
import altair as alt
import os

# ------------------------------
# DATABASE CONNECTION
# ------------------------------
DB_PATH = "car_rental.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def create_user(username, password, role="user"):
    try:
        c.execute("INSERT INTO users(username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()

def add_car(name, model, ctype, price, img):
    c.execute("INSERT INTO cars(car_name, car_model, car_type, price_per_day, available, image_path) VALUES (?, ?, ?, ?, ?, ?)",
              (name, model, ctype, price, "Yes", img))
    conn.commit()

def view_cars():
    return pd.read_sql_query("SELECT * FROM cars", conn)

def search_cars(query):
    q = f"%{query}%"
    return pd.read_sql_query("SELECT * FROM cars WHERE car_name LIKE ? OR car_model LIKE ? OR car_type LIKE ?", conn, params=(q, q, q))

def book_car(user_id, car_id, start, end):
    days = (end - start).days
    if days <= 0:
        return None
    c.execute("SELECT price_per_day FROM cars WHERE car_id=?", (car_id,))
    price = c.fetchone()[0]
    total = price * days
    c.execute("INSERT INTO bookings(user_id, car_id, start_date, end_date, total_amount) VALUES (?, ?, ?, ?, ?)",
              (user_id, car_id, str(start), str(end), total))
    c.execute("UPDATE cars SET available='No' WHERE car_id=?", (car_id,))
    conn.commit()
    return total

def view_user_bookings(user_id):
    return pd.read_sql_query("SELECT * FROM bookings WHERE user_id=?", conn, params=(user_id,))

def return_car(booking_id, car_id):
    c.execute("UPDATE bookings SET returned='Yes' WHERE booking_id=?", (booking_id,))
    c.execute("UPDATE cars SET available='Yes' WHERE car_id=?", (car_id,))
    conn.commit()

def add_rating(car_id, rating):
    c.execute("SELECT rating, total_ratings FROM cars WHERE car_id=?", (car_id,))
    res = c.fetchone()
    if not res:
        return
    old_rating, total = res
    new_total = total + 1
    new_rating = ((old_rating * total) + rating) / new_total if total > 0 else rating
    c.execute("UPDATE cars SET rating=?, total_ratings=? WHERE car_id=?", (new_rating, new_total, car_id))
    conn.commit()

def view_all_bookings():
    return pd.read_sql_query("SELECT * FROM bookings", conn)

# ------------------------------
# STYLING
# ------------------------------
st.set_page_config(page_title="🚘 Car Rental Dashboard", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #E3FDFD, #FFFFFF);
    font-family: 'Segoe UI';
}
.sidebar .sidebar-content {
    background: linear-gradient(to bottom, #74ebd5, #ACB6E5);
}
div[data-testid="stMetricValue"] {
    color: #0072B2;
}
</style>
""", unsafe_allow_html=True)

st.title("🚗 Car Rental Management System")

# ------------------------------
# MAIN MENU
# ------------------------------
menu = ["Login", "Sign Up"]
choice = st.sidebar.selectbox("Menu", menu)

# ------------------------------
# SIGN UP PAGE
# ------------------------------
if choice == "Sign Up":
    st.subheader("📝 Create Account")
    username = st.text_input("Username", key="signup_user")
    password = st.text_input("Password", type="password", key="signup_pass")
    if st.button("Register"):
        ok = create_user(username, password)
        if ok:
            st.success("✅ Account created successfully! You can now log in.")
        else:
            st.error("⚠️ Username already exists or invalid input!")

# ------------------------------
# LOGIN PAGE
# ------------------------------
elif choice == "Login":
    st.subheader("🔐 Login to your Account")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.success(f"Welcome, {user[1]} ({user[3].capitalize()})")
            role = user[3]

            # ------------------------------
            # ADMIN DASHBOARD
            # ------------------------------
            if role == "admin":
                admin_menu = ["📊 Dashboard", "🚘 Add Car", "📋 View Cars", "📦 View All Bookings"]
                admin_choice = st.sidebar.radio("Admin Panel", admin_menu)

                # ---------------- Dashboard ----------------
                if admin_choice == "📊 Dashboard":
                    st.subheader("📈 Admin Analytics Dashboard")
                    bookings_df = view_all_bookings()
                    cars_df = view_cars()
                    total_cars = len(cars_df)
                    total_bookings = len(bookings_df)
                    revenue = bookings_df["total_amount"].sum() if not bookings_df.empty else 0

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Cars", total_cars)
                    col2.metric("Total Bookings", total_bookings)
                    col3.metric("Revenue (₹)", f"{revenue:.2f}")

                    if not bookings_df.empty:
                        st.write("### 📆 Revenue Over Time")
                        chart = alt.Chart(bookings_df).mark_bar().encode(
                            x="start_date:T",
                            y="total_amount:Q",
                            color="total_amount:Q"
                        ).properties(width=700)
                        st.altair_chart(chart, use_container_width=True)

                        st.write("### 🚘 Car Type Distribution")
                        type_chart = alt.Chart(cars_df).mark_arc(innerRadius=50).encode(
                            theta="count():Q",
                            color="car_type:N",
                            tooltip=["car_type"]
                        )
                        st.altair_chart(type_chart, use_container_width=True)

                        st.write("### ⭐ Top Rated Cars")
                        top_rated = cars_df.sort_values("rating", ascending=False).head(5)
                        st.dataframe(top_rated[["car_name", "car_model", "rating", "total_ratings"]])
                    else:
                        st.info("No bookings available.")

                # ---------------- Add Car ----------------
                elif admin_choice == "🚘 Add Car":
                    st.subheader("Add a New Car")
                    name = st.text_input("Car Name")
                    model = st.text_input("Model")
                    ctype = st.selectbox("Car Type", ["Sedan", "SUV", "Hatchback", "Convertible", "Luxury", "Electric"])
                    price = st.number_input("Price per Day (₹)", min_value=100.0)
                    img = st.text_input("Image Path (e.g. car_images/car1.jpg)")
                    if st.button("Add Car"):
                        add_car(name, model, ctype, price, img)
                        st.success("✅ Car added successfully!")

                # ---------------- View Cars ----------------
                elif admin_choice == "📋 View Cars":
                    st.subheader("All Cars")
                    st.dataframe(view_cars())

                # ---------------- View All Bookings ----------------
                elif admin_choice == "📦 View All Bookings":
                    st.subheader("All Bookings")
                    st.dataframe(view_all_bookings())

            # ------------------------------
            # USER DASHBOARD
            # ------------------------------
            else:
                user_menu = ["🚗 Browse Cars", "📚 My Bookings"]
                user_choice = st.sidebar.radio("User Panel", user_menu)

                # ---------------- Browse Cars ----------------
                if user_choice == "🚗 Browse Cars":
                    st.subheader("Available Cars for Rent")
                    search_query = st.text_input("🔍 Search by name, model, or type")
                    if search_query:
                        df = search_cars(search_query)
                    else:
                        df = view_cars()
                    available_cars = df[df["available"] == "Yes"]

                    if available_cars.empty:
                        st.info("No cars available currently.")
                    else:
                        for _, row in available_cars.iterrows():
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                if row["image_path"] and os.path.exists(row["image_path"]):
                                    st.image(row["image_path"], width=160)
                                else:
                                    st.image("https://via.placeholder.com/160", width=160)
                            with col2:
                                st.markdown(f"### {row['car_name']} ({row['car_model']})")
                                st.write(f"Type: {row['car_type']}")
                                st.write(f"💰 ₹{row['price_per_day']} per day")
                                st.write(f"⭐ Rating: {round(row['rating'], 1)} ({row['total_ratings']} ratings)")
                                start_date = st.date_input(f"Start Date ({row['car_id']})", datetime.date.today())
                                end_date = st.date_input(f"End Date ({row['car_id']})", datetime.date.today() + datetime.timedelta(days=1))
                                if st.button(f"Book {row['car_name']}", key=row["car_id"]):
                                    total = book_car(user[0], row["car_id"], start_date, end_date)
                                    if total:
                                        st.success(f"✅ Car booked successfully! Total = ₹{total}")
                                    else:
                                        st.warning("⚠️ Invalid date range.")

                # ---------------- My Bookings ----------------
                elif user_choice == "📚 My Bookings":
                    st.subheader("Your Bookings")
                    bookings = view_user_bookings(user[0])
                    if bookings.empty:
                        st.info("No bookings yet.")
                    else:
                        for _, row in bookings.iterrows():
                            st.markdown(f"### Booking ID: {row['booking_id']}")
                            st.write(f"Car ID: {row['car_id']}, From {row['start_date']} to {row['end_date']}")
                            st.write(f"Total: ₹{row['total_amount']}")
                            st.write(f"Returned: {row['returned']}")
                            if row["returned"] == "No":
                                if st.button(f"Return Car #{row['car_id']}", key=f"ret_{row['booking_id']}"):
                                    return_car(row["booking_id"], row["car_id"])
                                    st.success("✅ Car returned successfully!")
                            else:
                                rating = st.slider(f"Rate Car #{row['car_id']}", 1, 5, key=f"rate_{row['car_id']}")
                                if st.button(f"Submit Rating #{row['car_id']}", key=f"btn_{row['car_id']}"):
                                    add_rating(row["car_id"], rating)
                                    st.success("⭐ Rating submitted successfully!")
        else:
            st.error("❌ Invalid username or password")
