import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="BB84 QKD Simulator", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# Physics helpers
# ─────────────────────────────────────────────────────────────────────────────

BASES = ["+", "×"]

# The four BB84 photon states
PHOTON_STATE = {
    (0, "+"): "|0⟩  (vertical)",
    (1, "+"): "|1⟩  (horizontal)",
    (0, "×"): "|+⟩  (diagonal 45°)",
    (1, "×"): "|−⟩  (anti-diagonal 135°)",
}


def measure(bit: int, sender_basis: str, receiver_basis: str) -> int:
    """
    Projective measurement of a photon prepared with `bit` in `sender_basis`,
    measured in `receiver_basis`.

    Same basis  → deterministic, correct result.
    Wrong basis → uniformly random (Born rule, maximally mixed state).
    """
    if receiver_basis == sender_basis:
        return bit
    return random.randint(0, 1)


def run_bb84(num_bits: int, eve_present: bool, sample_fraction: float) -> dict:
    """Run one complete BB84 exchange and return all intermediate data."""

    # Alice
    alice_bits  = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(BASES)  for _ in range(num_bits)]

    # Eve (optional intercept-resend attack)
    eve_bases: list[str] = []
    eve_bits:  list[int] = []
    channel_bits  = alice_bits[:]   # photon bit arriving at Bob
    channel_bases = alice_bases[:]  # photon basis arriving at Bob

    if eve_present:
        for i in range(num_bits):
            eb = random.choice(BASES)
            em = measure(alice_bits[i], alice_bases[i], eb)
            eve_bases.append(eb)
            eve_bits.append(em)
            # Eve resends a fresh photon prepared with her result in her chosen basis.
            # The no-cloning theorem prevents her from forwarding the original undisturbed.
            channel_bits[i]  = em
            channel_bases[i] = eb

    # Bob
    bob_bases = [random.choice(BASES) for _ in range(num_bits)]
    bob_bits  = [
        measure(channel_bits[i], channel_bases[i], bob_bases[i])
        for i in range(num_bits)
    ]

    # Sifting — keep photons where Alice's and Bob's bases agree
    sifted_mask  = [alice_bases[i] == bob_bases[i] for i in range(num_bits)]
    sifted_idx   = [i for i, m in enumerate(sifted_mask) if m]
    alice_sifted = [alice_bits[i] for i in sifted_idx]
    bob_sifted   = [bob_bits[i]   for i in sifted_idx]

    # QBER estimation — sacrifice a random sample
    n_sifted   = len(sifted_idx)
    n_sample   = max(1, round(n_sifted * sample_fraction))
    sample_pos = sorted(random.sample(range(n_sifted), min(n_sample, n_sifted)))

    sample_alice = [alice_sifted[i] for i in sample_pos]
    sample_bob   = [bob_sifted[i]   for i in sample_pos]
    errors       = sum(a != b for a, b in zip(sample_alice, sample_bob))
    qber         = errors / len(sample_pos) if sample_pos else 0.0

    # Final key — sifted bits not used in the QBER check
    key_pos   = [i for i in range(n_sifted) if i not in sample_pos]
    alice_key = [alice_sifted[i] for i in key_pos]
    bob_key   = [bob_sifted[i]   for i in key_pos]

    return dict(
        alice_bits=alice_bits, alice_bases=alice_bases,
        eve_present=eve_present, eve_bases=eve_bases, eve_bits=eve_bits,
        bob_bases=bob_bases, bob_bits=bob_bits,
        sifted_mask=sifted_mask, sifted_idx=sifted_idx,
        alice_sifted=alice_sifted, bob_sifted=bob_sifted,
        sample_pos=sample_pos, sample_alice=sample_alice, sample_bob=sample_bob,
        errors=errors, qber=qber,
        alice_key=alice_key, bob_key=bob_key,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Row-level highlighting helpers for styled DataFrames
# ─────────────────────────────────────────────────────────────────────────────

def _hl_yesno(row, col, yes_color="#d4edda", no_color="#f8d7da"):
    color = yes_color if row[col] == "Yes" else no_color
    return [f"background-color: {color}"] * len(row)


def hl_bob(row):
    return _hl_yesno(row, "Bases match")


def hl_eve(row):
    return _hl_yesno(row, "Bases match", yes_color="#d4edda", no_color="#fff3cd")


def hl_sifted(row):
    return _hl_yesno(row, "Agree")


def hl_sample(row):
    return _hl_yesno(row, "Match")


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────

st.title("BB84 Quantum Key Distribution Simulator")
st.write(
    "A step-by-step walkthrough of the BB84 protocol — the first practical scheme for distributing "
    "a cryptographic key whose security is guaranteed by physical law rather than computational "
    "hardness assumptions. Proposed by Charles Bennett and Gilles Brassard in 1984."
)

with st.expander("Background: how does BB84 work?"):
    st.markdown("""
**The problem.** Alice and Bob want to share a secret random key over a channel Eve can monitor.
Classical methods like Diffie-Hellman are secure only if certain maths problems are hard — a large
quantum computer breaks them. BB84 uses *quantum mechanics* instead.

**Why eavesdropping is detectable.**
The no-cloning theorem states that an arbitrary unknown quantum state cannot be copied perfectly.
If Eve intercepts a photon, she must measure it in *some* basis and then re-send a fresh photon
based on what she learned. Whenever she picks the wrong basis she disturbs the state irreversibly.
That disturbance shows up as errors in bits Alice and Bob would otherwise agree on.

**Encoding — the four BB84 states.**

| Bit | Rectilinear basis `+` | Diagonal basis `×` |
|-----|----------------------|--------------------|
| 0   | `\|0⟩` vertical          | `\|+⟩` diagonal 45°   |
| 1   | `\|1⟩` horizontal        | `\|−⟩` anti-diagonal 135°|

Measuring in the *same* basis as preparation always gives the correct bit.
Measuring in the *wrong* basis gives a uniformly random result — the quantum state
is projected onto an orthogonal basis, so both outcomes are equally probable.

**The five phases simulated here.**

1. **Preparation.** Alice generates a random bit string and a random basis string.
   Each (bit, basis) pair determines the polarisation state of one photon.
2. **Interception (optional).** Eve measures each photon in a random basis and re-sends
   a fresh photon. She has no way to avoid this; perfect cloning is forbidden.
3. **Measurement.** Bob picks an independent random basis per photon and records his result.
4. **Sifting.** Alice and Bob publicly compare *which bases* they used (not the bits).
   Photons where their bases differ are discarded — those results are meaningless.
   On average ~50% of photons survive sifting.
5. **QBER check.** A random sample of sifted bits is publicly compared to estimate the
   Quantum Bit Error Rate. No Eve → QBER ≈ 0%.
   Full intercept-resend attack → QBER ≈ 25% (Eve guesses wrong basis 50% of the time;
   when she does, Bob's measurement on the re-sent photon is random, giving an error
   half the time: 0.5 × 0.5 = 0.25).
   If QBER is below a chosen threshold the remaining sifted bits form the shared key.
""")

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Parameters")
    num_bits = st.slider(
        "Photons Alice sends:", min_value=8, max_value=64, value=20, step=4,
        help="More photons → longer sifted key and a more reliable QBER estimate.",
    )
    eve_present = st.toggle(
        "Eve intercepts every photon", value=False,
        help="Simulates a full intercept-resend attack on every photon in the channel.",
    )
    sample_fraction = st.slider(
        "Fraction sacrificed for QBER check:", min_value=0.10, max_value=0.50,
        value=0.25, step=0.05, format="%.2f",
        help="These bits are publicly compared and then discarded — they cannot be part of the key.",
    )
    qber_threshold = st.slider(
        "Abort if QBER exceeds (%):", min_value=5, max_value=25, value=11,
        help="A common practical threshold is ~11%. Above this, information-theoretic security cannot be guaranteed.",
    )
    st.divider()
    run = st.button("Run Simulation", type="primary", use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# Simulation output
# ─────────────────────────────────────────────────────────────────────────────

if not run:
    st.info("Configure the parameters in the sidebar and click **Run Simulation** to begin.")
    st.stop()

sim  = run_bb84(num_bits, eve_present, sample_fraction)
step = 0  # incremented before each section


# ── Step 1: Alice prepares ───────────────────────────────────────────────────
step += 1
st.header(f"Step {step} — Alice prepares and sends photons")
st.write(
    "Alice uses a quantum random number generator to produce a random bit string. "
    "She also independently picks a random *basis* for each bit — either rectilinear (`+`) "
    "or diagonal (`×`). The bit and the basis together determine which of the four polarisation "
    "states she prepares. She sends each photon across the quantum channel one at a time."
)

df_alice = pd.DataFrame({
    "Photon":       range(1, num_bits + 1),
    "Alice bit":    sim["alice_bits"],
    "Alice basis":  sim["alice_bases"],
    "State sent":   [PHOTON_STATE[(b, bs)]
                     for b, bs in zip(sim["alice_bits"], sim["alice_bases"])],
})
st.dataframe(df_alice, use_container_width=True, hide_index=True)


# ── Step 2 (optional): Eve intercepts ───────────────────────────────────────
if eve_present:
    step += 1
    st.header(f"Step {step} — Eve intercepts")
    st.write(
        "Eve taps the quantum channel between Alice and Bob. For each photon she randomly "
        "picks a measurement basis, records the result, and then **re-sends a fresh photon** "
        "prepared in her measured state and basis. She cannot do better than this — the "
        "no-cloning theorem prohibits her from making a perfect copy and passing on the original."
    )
    st.write(
        "When Eve's basis happens to match Alice's (about 50% of photons), her measurement is "
        "correct and the re-sent photon is physically identical to the original — no disturbance "
        "reaches Bob. When they differ, Eve's outcome is random and the photon she resends is in "
        "a different state, which will eventually show up as errors in the QBER check."
    )

    df_eve = pd.DataFrame({
        "Photon":        range(1, num_bits + 1),
        "Alice basis":   sim["alice_bases"],
        "Eve basis":     sim["eve_bases"],
        "Bases match":   ["Yes" if a == e else "No"
                          for a, e in zip(sim["alice_bases"], sim["eve_bases"])],
        "Eve measured":  sim["eve_bits"],
        "State re-sent": [PHOTON_STATE[(b, bs)]
                          for b, bs in zip(sim["eve_bits"], sim["eve_bases"])],
    })

    st.dataframe(
        df_eve.style.apply(hl_eve, axis=1),
        use_container_width=True, hide_index=True,
    )

    n_eve_right = sum(a == e for a, e in zip(sim["alice_bases"], sim["eve_bases"]))
    st.write(
        f"Eve chose the correct basis for **{n_eve_right} / {num_bits}** photons. "
        f"She introduced potential errors into the remaining **{num_bits - n_eve_right}** photons."
    )


# ── Step: Bob measures ───────────────────────────────────────────────────────
step += 1
st.header(f"Step {step} — Bob measures")
st.write(
    "Bob independently selects a random measurement basis for each arriving photon — he has no "
    "knowledge of Alice's (or Eve's) choices at this stage. When his basis matches the basis of "
    "the photon that arrives (which may have been re-sent by Eve), he recovers the bit exactly. "
    "When it differs, the outcome is governed by the Born rule and is essentially a coin flip."
)

# Column order chosen so the reader can compare bases before seeing the result
df_bob = pd.DataFrame({
    "Photon":       range(1, num_bits + 1),
    "Alice basis":  sim["alice_bases"],
    "Bob basis":    sim["bob_bases"],
    "Bases match":  ["Yes" if a == b else "No"
                     for a, b in zip(sim["alice_bases"], sim["bob_bases"])],
    "Alice bit":    sim["alice_bits"],
    "Bob result":   sim["bob_bits"],
})
st.dataframe(
    df_bob.style.apply(hl_bob, axis=1),
    use_container_width=True, hide_index=True,
)

n_match = sum(sim["sifted_mask"])
st.write(
    f"Bob's basis matched Alice's original basis for **{n_match} / {num_bits}** photons "
    f"({100 * n_match / num_bits:.0f}%). "
    "Only these photons carry usable information — the others are discarded in the next step."
)


# ── Step: Sifting ────────────────────────────────────────────────────────────
step += 1
st.header(f"Step {step} — Sifting")
st.write(
    "Alice and Bob communicate over a **public, authenticated classical channel** "
    "(a phone call, a classical internet connection — it can be monitored freely). "
    "They announce *which basis* they used for each photon, but **not the bit values**. "
    "Any photon where they disagree on the basis is thrown away. "
    "The survivors form the *sifted key*."
)
st.write(
    "Note: Eve can hear this conversation too, but she only learns the *bases*, not the bits. "
    "Knowing only the bases of sifted photons gives her zero information about the key bits."
)

sifted_idx = sim["sifted_idx"]

if not sifted_idx:
    st.warning(
        "No photons survived sifting in this run — this is very unlikely with 8+ photons. "
        "Try clicking Run Simulation again."
    )
    st.stop()

df_sifted = pd.DataFrame({
    "Original photon #": [i + 1 for i in sifted_idx],
    "Shared basis":      [sim["alice_bases"][i] for i in sifted_idx],
    "Alice bit":         sim["alice_sifted"],
    "Bob bit":           sim["bob_sifted"],
    "Agree":             ["Yes" if a == b else "No"
                          for a, b in zip(sim["alice_sifted"], sim["bob_sifted"])],
})
st.dataframe(
    df_sifted.style.apply(hl_sifted, axis=1),
    use_container_width=True, hide_index=True,
)

n_agree  = sum(a == b for a, b in zip(sim["alice_sifted"], sim["bob_sifted"]))
n_sifted = len(sifted_idx)
st.write(
    f"Sifted key length: **{n_sifted} bits** (from {num_bits} photons sent). "
    f"Alice and Bob hold **identical bits at {n_agree} positions** and "
    f"**differ at {n_sifted - n_agree}**. "
    "Those disagreements indicate either channel noise or eavesdropping."
)


# ── Step: QBER estimation ────────────────────────────────────────────────────
step += 1
st.header(f"Step {step} — Error rate estimation (QBER)")
st.write(
    f"Alice and Bob randomly select **{len(sim['sample_pos'])} bits** from the sifted key "
    f"({sample_fraction * 100:.0f}% of {n_sifted}) and compare their values publicly. "
    "These bits are permanently sacrificed after comparison — they can never be secret now. "
    "The fraction that disagree is the **Quantum Bit Error Rate (QBER)**."
)

df_sample = pd.DataFrame({
    "Sifted position": [p + 1 for p in sim["sample_pos"]],
    "Alice bit":       sim["sample_alice"],
    "Bob bit":         sim["sample_bob"],
    "Match":           ["Yes" if a == b else "No"
                        for a, b in zip(sim["sample_alice"], sim["sample_bob"])],
})
st.dataframe(
    df_sample.style.apply(hl_sample, axis=1),
    use_container_width=True, hide_index=True,
)

qber_pct = sim["qber"] * 100
col_q1, col_q2, col_q3 = st.columns(3)
col_q1.metric("Bits sampled",      len(sim["sample_pos"]))
col_q2.metric("Errors found",      sim["errors"])
col_q3.metric("QBER",              f"{qber_pct:.1f}%")

if qber_pct > qber_threshold:
    st.error(
        f"QBER = {qber_pct:.1f}% exceeds the threshold of {qber_threshold}%. "
        "Alice and Bob abort the protocol. No key is established. "
        "They should assume the channel is compromised and try again over a different path."
    )
else:
    st.success(
        f"QBER = {qber_pct:.1f}% is within the acceptable threshold of {qber_threshold}%. "
        "The estimated eavesdropping level is low enough to proceed."
    )

if eve_present:
    st.info(
        "With a full intercept-resend attack (Eve measures every photon in a random basis), "
        "the theoretical expected QBER is **25%**. Derivation: Eve guesses the wrong basis "
        "with probability 0.5. When she does, the photon she re-sends is in a random state relative "
        "to Alice's original basis. Bob, measuring in Alice's basis (sifted case), then gets the "
        "wrong bit with probability 0.5. Net error probability = 0.5 × 0.5 = 0.25."
    )
else:
    st.info(
        "With no eavesdropping on an ideal, noiseless channel the expected QBER is **0%**. "
        "In real deployments, detector dark counts, photon loss, and optical misalignment "
        "typically push the baseline QBER to 1–5%, which is why the threshold is set above zero."
    )


# ── Step: Final key ──────────────────────────────────────────────────────────
step += 1
st.header(f"Step {step} — Final shared key")

if qber_pct > qber_threshold:
    st.write("Protocol aborted due to high QBER. No key was established in this run.")
    st.stop()

if not sim["alice_key"]:
    st.warning(
        "Not enough bits remain after the QBER check to form a key. "
        "Increase the number of photons or reduce the sample fraction and run again."
    )
    st.stop()

st.write(
    "The sifted bits that were *not* used in the QBER check form the raw shared key. "
    "Both Alice and Bob hold the same string — Alice because she generated it; Bob because "
    "his basis matched Alice's for each of these photons and (assuming low QBER) their bits agree."
)
st.write(
    "In a production system, two more stages would follow: "
    "**error correction** (e.g., Cascade or LDPC codes) to fix any residual mismatches, "
    "and **privacy amplification** (hashing the corrected string) to collapse any partial "
    "information Eve may have learned into zero usable knowledge. We skip both here."
)

col_k1, col_k2 = st.columns(2)
with col_k1:
    st.write("**Alice's key**")
    st.code("".join(str(b) for b in sim["alice_key"]))
with col_k2:
    st.write("**Bob's key**")
    st.code("".join(str(b) for b in sim["bob_key"]))

keys_match = sim["alice_key"] == sim["bob_key"]
n_key = len(sim["alice_key"])

if keys_match:
    st.success(f"Keys match exactly. Shared secret: **{n_key} bits**.")
else:
    n_diff = sum(a != b for a, b in zip(sim["alice_key"], sim["bob_key"]))
    st.warning(
        f"Keys differ at **{n_diff} / {n_key}** position(s). "
        "In a real deployment, error correction would reconcile these before the key is used."
    )

# Summary
st.divider()
st.subheader("Run summary")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Photons sent",          num_bits)
c2.metric("Survived sifting",      n_sifted)
c3.metric("Sacrificed for QBER",   len(sim["sample_pos"]))
c4.metric("Final key length",      n_key)
c5.metric("Key rate",              f"{n_key / num_bits * 100:.1f}%")

st.write(
    f"On average, BB84 yields roughly **{1/4:.0%}** of sent photons as key bits "
    f"(~50% survive sifting, then ~{sample_fraction*100:.0f}% of those are sacrificed for QBER). "
    f"This run achieved **{n_key / num_bits * 100:.1f}%**."
)
