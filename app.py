import streamlit as st
import random

# Set the page title and layout
st.set_page_config(page_title="Interactive QKD Prototype", layout="centered")

# Page Header
st.title("⚛️ QKD Prototyping Playground")
st.write("This is a sample interactive web app built with Streamlit.")

st.divider()

# --- INTERACTIVE COMPONENT 1: Slider ---
st.subheader("Step 1: Alice's Bit Generation")
st.write("Choose how many random bits Alice should generate.")

# A slider that lets the user choose a number between 1 and 20 (defaults to 8)
num_bits = st.slider("Number of bits to generate:", min_value=1, max_value=20, value=8)

# --- INTERACTIVE COMPONENT 2: Button ---
# The code indented under the 'if' statement only runs when the button is clicked
if st.button("Generate Alice's Bits"):
    
    # Generate a list of random 0s and 1s based on the slider value
    alice_bits = [random.choice([0, 1]) for _ in range(num_bits)]
    
    # Display a success message
    st.success(f"Successfully generated {num_bits} random bits!")
    
    # Display the raw list as code
    st.code(str(alice_bits), language="python")
    
    # --- INTERACTIVE COMPONENT 3: Data Table ---
    # Streamlit automatically turns Python dictionaries into clean tables
    st.write("Visualized in a table:")
    
    # We can also generate random bases (+ or x) to show how you might build up the QKD table
    alice_bases = [random.choice(["+", "x"]) for _ in range(num_bits)]
    
    table_data = {
        "Photon Index": list(range(1, num_bits + 1)),
        "Alice's Bit": alice_bits,
        "Alice's Base": alice_bases
    }
    
    st.table(table_data)

st.divider()

# A helpful info box
st.info("💡 **Next Steps for your QKD App:** You could add more interactive elements below this to simulate Bob guessing bases, or Eve intercepting the transmission!")