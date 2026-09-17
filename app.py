import streamlit as st
import binascii
import pandas as pd
from datetime import datetime

# --- CORE CRC-32 ENGINE ---
def calculate_crc32(data: bytes) -> str:
    """Computes standard 32-bit CRC checksum in hexadecimal format."""
    crc = binascii.crc32(data) & 0xFFFFFFFF
    return f"0x{crc:08X}"

def inject_bit_error(data: bytes) -> bytes:
    """Simulates noise/corruption by flipping the first bit of the payload."""
    if not data:
        return data
    byte_arr = bytearray(data)
    byte_arr[0] ^= 0x01  # Bitwise XOR flip
    return bytes(byte_arr)

# --- SESSION STATE INITIALIZATION ---
if "reference_crc" not in st.session_state:
    st.session_state.reference_crc = None
if "verification_logs" not in st.session_state:
    st.session_state.verification_logs = []

# --- PAGE CONFIG & HEADER ---
st.set_page_config(page_title="CRC-32 Dashboard", layout="wide")
st.title("🛡️ CRC-32 Dashboard & Module Integration")
st.caption("Week 4: Prototype Integration, Error Simulation & CSV Reporting")

# --- STEP 1 & 2: INPUT SELECTION & CRC GENERATION ---
st.header("1. Input Selection & Reference CRC Generation")
input_type = st.radio("Select Input Data Type:", ["File", "Message (Text)", "Packet / Record"], horizontal=True)

raw_bytes = None
input_name = ""

if input_type == "File":
    uploaded_file = st.file_uploader("Upload Assignment / Document File", type=None)
    if uploaded_file:
        raw_bytes = uploaded_file.read()
        input_name = uploaded_file.name
elif input_type == "Message (Text)":
    text_input = st.text_input("Enter String Message:", "ASSIGNMENT_SUBMISSION_V1")
    if text_input:
        raw_bytes = text_input.encode("utf-8")
        input_name = f"Text: {text_input[:15]}..."
else:
    packet_hex = st.text_input("Enter Packet / Record (Hex or Binary string):", "1011010011")
    if packet_hex:
        raw_bytes = packet_hex.encode("utf-8")
        input_name = f"Packet: {packet_hex}"

if raw_bytes is not None:
    ref_crc = calculate_crc32(raw_bytes)
    col1, col2 = st.columns(2)
    col1.metric("Input Byte Size", f"{len(raw_bytes)} bytes")
    col2.metric("Generated CRC-32", ref_crc)
    
    if st.button("Save as Stored Reference CRC"):
        st.session_state.reference_crc = ref_crc
        st.success(f"Reference CRC `{ref_crc}` stored successfully!")

st.divider()

# --- STEP 3 & 4: VERIFICATION & STATUS DISPLAY ---
st.header("2. Verification & Status Display")

if st.session_state.reference_crc:
    st.info(f"Active Stored Reference CRC: **{st.session_state.reference_crc}**")
    
    eval_bytes = None
    eval_name = ""

    if input_type == "File":
        eval_file = st.file_uploader("Upload File/Data to Verify Integrity", key="eval_uploader")
        if eval_file:
            eval_bytes = eval_file.read()
            eval_name = eval_file.name
    elif input_type == "Message (Text)":
        eval_text = st.text_input("Enter String Message to Verify:", "ASSIGNMENT_SUBMISSION_V1", key="eval_text")
        if eval_text:
            eval_bytes = eval_text.encode("utf-8")
            eval_name = f"Text: {eval_text[:15]}..."
    else:
        eval_packet = st.text_input("Enter Packet / Record to Verify:", "1011010011", key="eval_packet")
        if eval_packet:
            eval_bytes = eval_packet.encode("utf-8")
            eval_name = f"Packet: {eval_packet}"
    
    if eval_bytes is not None:
        current_crc = calculate_crc32(eval_bytes)
        
        # Decision Tree Logic
        is_match = (current_crc == st.session_state.reference_crc)
        status = "VALID" if is_match else "CORRUPTED"
        
        col_a, col_b = st.columns(2)
        col_a.metric("Current CRC-32", current_crc)
        
        if is_match:
            col_b.success("STATUS: VALID (No Error Detected)")
        else:
            col_b.error("STATUS: CORRUPTED (Mismatch Detected)")
            
        # Log Result for CSV Deliverable
        if st.button("Log Result to Verification Audit"):
            st.session_state.verification_logs.append({
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Input Name": eval_name,
                "Reference CRC": st.session_state.reference_crc,
                "Current CRC": current_crc,
                "Status": status
            })
            st.toast("Result logged to report summary!")
else:
    st.warning("Please generate and save a Reference CRC above before running verification.")

st.divider()

# --- STEP 5: ERROR SIMULATION CONTROLS ---
st.header("3. Error-Simulation Controls")
st.write("Inject single-bit transmission noise into data to test corrupted status detection.")

sim_bytes = None
sim_name = ""

if input_type == "File":
    sim_file = st.file_uploader("Upload Test Payload for Noise Injection", key="sim_uploader")
    if sim_file:
        sim_bytes = sim_file.read()
        sim_name = sim_file.name
elif input_type == "Message (Text)":
    sim_text = st.text_input("Enter Payload for Noise Injection:", "ASSIGNMENT_SUBMISSION_V1", key="sim_text")
    if sim_text:
        sim_bytes = sim_text.encode("utf-8")
        sim_name = f"Text: {sim_text[:15]}..."
else:
    sim_packet = st.text_input("Enter Packet for Noise Injection:", "1011010011", key="sim_packet")
    if sim_packet:
        sim_bytes = sim_packet.encode("utf-8")
        sim_name = f"Packet: {sim_packet}"

if sim_bytes is not None:
    orig_crc = calculate_crc32(sim_bytes)
    st.write(f"Original Checksum: `{orig_crc}`")
    
    if st.button("⚡ Inject Bit-Flip Error"):
        corrupted_bytes = inject_bit_error(sim_bytes)
        corrupted_crc = calculate_crc32(corrupted_bytes)
        
        st.error("🚨 Noise Injected: Bit 0 inverted!")
        c1, c2 = st.columns(2)
        c1.metric("Original CRC", orig_crc)
        c2.metric("Corrupted CRC", corrupted_crc, delta="Mismatch", delta_color="inverse")
        
        # Log Simulation
        st.session_state.verification_logs.append({
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Input Name": f"[SIMULATED NOISE] {sim_name}",
            "Reference CRC": orig_crc,
            "Current CRC": corrupted_crc,
            "Status": "CORRUPTED"
        })

st.divider()

# --- CSV REPORT GENERATION ---
st.header("4. CSV Verification Report Generation")

if st.session_state.verification_logs:
    df_logs = pd.DataFrame(st.session_state.verification_logs)
    st.markdown(df_logs.to_html(index=False), unsafe_allow_html=True)
    
    csv_data = df_logs.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Save & Download CSV Verification Report",
        data=csv_data,
        file_name="crc32_verification_report.csv",
        mime="text/csv"
    )
else:
    st.caption("No verification logs created yet. Perform checks above to generate report entries.")