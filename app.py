import streamlit as st
import random
import pandas as pd

st.set_page_config(page_title="QKD Interactive Platform", layout="wide")

st.title("Quantum Key Distribution — Interactive Platform")
st.write(
    "A single platform for students learning BB84, educators building curriculum, "
    "and industry professionals assessing the quantum threat to classical cryptography."
)

tab_student, tab_educator, tab_industry = st.tabs(
    ["Students — BB84 Simulator", "Educators — Teaching Modules", "Industry — Quantum Readiness"]
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared physics helpers (used only in the Students tab)
# ─────────────────────────────────────────────────────────────────────────────

BASES = ["+", "×"]

PHOTON_STATE = {
    (0, "+"): "|0⟩  (vertical)",
    (1, "+"): "|1⟩  (horizontal)",
    (0, "×"): "|+⟩  (diagonal 45°)",
    (1, "×"): "|−⟩  (anti-diagonal 135°)",
}


def measure(bit: int, sender_basis: str, receiver_basis: str) -> int:
    if receiver_basis == sender_basis:
        return bit
    return random.randint(0, 1)


def run_bb84(num_bits: int, eve_present: bool, sample_fraction: float) -> dict:
    alice_bits  = [random.randint(0, 1) for _ in range(num_bits)]
    alice_bases = [random.choice(BASES)  for _ in range(num_bits)]

    eve_bases: list = []
    eve_bits:  list = []
    channel_bits  = alice_bits[:]
    channel_bases = alice_bases[:]

    if eve_present:
        for i in range(num_bits):
            eb = random.choice(BASES)
            em = measure(alice_bits[i], alice_bases[i], eb)
            eve_bases.append(eb)
            eve_bits.append(em)
            channel_bits[i]  = em
            channel_bases[i] = eb

    bob_bases = [random.choice(BASES) for _ in range(num_bits)]
    bob_bits  = [
        measure(channel_bits[i], channel_bases[i], bob_bases[i])
        for i in range(num_bits)
    ]

    sifted_mask  = [alice_bases[i] == bob_bases[i] for i in range(num_bits)]
    sifted_idx   = [i for i, m in enumerate(sifted_mask) if m]
    alice_sifted = [alice_bits[i] for i in sifted_idx]
    bob_sifted   = [bob_bits[i]   for i in sifted_idx]

    n_sifted   = len(sifted_idx)
    n_sample   = max(1, round(n_sifted * sample_fraction))
    sample_pos = sorted(random.sample(range(n_sifted), min(n_sample, n_sifted)))

    sample_alice = [alice_sifted[i] for i in sample_pos]
    sample_bob   = [bob_sifted[i]   for i in sample_pos]
    errors       = sum(a != b for a, b in zip(sample_alice, sample_bob))
    qber         = errors / len(sample_pos) if sample_pos else 0.0

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


def _hl(row, col, yes_color="#d4edda", no_color="#f8d7da"):
    color = yes_color if row[col] == "Yes" else no_color
    return [f"background-color: {color}"] * len(row)

hl_bob     = lambda row: _hl(row, "Bases match")
hl_eve     = lambda row: _hl(row, "Bases match", no_color="#fff3cd")
hl_sifted  = lambda row: _hl(row, "Agree")
hl_sample  = lambda row: _hl(row, "Match")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — STUDENTS
# ═════════════════════════════════════════════════════════════════════════════

with tab_student:

    st.subheader("BB84 Protocol — Step-by-step Simulator")
    st.write(
        "Work through every phase of the BB84 quantum key distribution protocol. "
        "Adjust the parameters below, toggle Eve on and off, and observe how eavesdropping "
        "leaves a detectable signature in the error rate."
    )

    with st.expander("Background: how does BB84 work?"):
        st.markdown("""
**The problem.** Alice and Bob want to share a secret random key over a channel Eve can monitor.
Classical methods like Diffie-Hellman are secure only if certain maths problems are hard —
a large quantum computer breaks them. BB84 uses *quantum mechanics* instead.

**Why eavesdropping is detectable.**
The no-cloning theorem states that an arbitrary unknown quantum state cannot be copied perfectly.
If Eve intercepts a photon, she must measure it in *some* basis and then re-send a fresh photon.
Whenever she picks the wrong basis she disturbs the state irreversibly — that disturbance shows
up as errors that Alice and Bob would not otherwise see.

**The four BB84 states.**
""")
        st.table(pd.DataFrame({
            "Bit": ["0", "1"],
            "Rectilinear basis (+)": ["|0⟩  vertical", "|1⟩  horizontal"],
            "Diagonal basis (×)":    ["|+⟩  diagonal 45°", "|−⟩  anti-diagonal 135°"],
        }))
        st.markdown("""
**The five phases:**
1. Alice sends N photons, each in a randomly chosen state.
2. Eve (optionally) intercepts, measures in a random basis, and re-sends.
3. Bob measures each photon in a randomly chosen basis.
4. Sifting — they compare bases publicly and discard mismatches (~50% survive).
5. QBER check — a sample of sifted bits is compared. No Eve → QBER ≈ 0%. Full attack → QBER ≈ 25%.
""")

    # Controls in a horizontal row
    st.divider()
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        num_bits = st.slider("Photons sent:", 8, 64, 20, 4)
    with c2:
        sample_fraction = st.slider("QBER sample fraction:", 0.10, 0.50, 0.25, 0.05, format="%.2f")
    with c3:
        qber_threshold = st.slider("Abort threshold (%):", 5, 25, 11)
    with c4:
        eve_present = st.toggle("Eve intercepts every photon", value=False)
    with c5:
        st.write("")
        st.write("")
        run = st.button("Run", type="primary", use_container_width=True)

    st.divider()

    if not run:
        st.info("Set parameters above and click **Run** to begin.")
    else:
        sim  = run_bb84(num_bits, eve_present, sample_fraction)
        step = 0

        # Step 1 — Alice prepares
        step += 1
        st.header(f"Step {step} — Alice prepares and sends photons")
        st.write(
            "Alice generates a random bit string and independently picks a random basis per bit. "
            "The (bit, basis) pair determines the polarisation state of each photon she sends."
        )
        df_alice = pd.DataFrame({
            "Photon":      range(1, num_bits + 1),
            "Alice bit":   sim["alice_bits"],
            "Alice basis": sim["alice_bases"],
            "State sent":  [PHOTON_STATE[(b, bs)]
                            for b, bs in zip(sim["alice_bits"], sim["alice_bases"])],
        })
        st.dataframe(df_alice, use_container_width=True, hide_index=True)

        # Step 2 — Eve (optional)
        if eve_present:
            step += 1
            st.header(f"Step {step} — Eve intercepts")
            st.write(
                "Eve measures each photon in a randomly chosen basis and re-sends a fresh photon. "
                "She cannot clone the original — the no-cloning theorem forbids it. "
                "When her basis matches Alice's (green), no disturbance is introduced. "
                "When it differs (yellow), the photon she re-sends is in a different state, "
                "which will eventually produce errors in the QBER check."
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
            st.dataframe(df_eve.style.apply(hl_eve, axis=1),
                         use_container_width=True, hide_index=True)
            n_right = sum(a == e for a, e in zip(sim["alice_bases"], sim["eve_bases"]))
            st.write(
                f"Eve guessed the correct basis for **{n_right} / {num_bits}** photons. "
                f"She introduced potential errors into the remaining {num_bits - n_right}."
            )

        # Step — Bob measures
        step += 1
        st.header(f"Step {step} — Bob measures")
        st.write(
            "Bob independently picks a random measurement basis per photon. "
            "Matching basis (green) → deterministic correct result. "
            "Wrong basis (red) → random outcome; that photon is discarded in sifting."
        )
        df_bob = pd.DataFrame({
            "Photon":       range(1, num_bits + 1),
            "Alice basis":  sim["alice_bases"],
            "Bob basis":    sim["bob_bases"],
            "Bases match":  ["Yes" if a == b else "No"
                             for a, b in zip(sim["alice_bases"], sim["bob_bases"])],
            "Alice bit":    sim["alice_bits"],
            "Bob result":   sim["bob_bits"],
        })
        st.dataframe(df_bob.style.apply(hl_bob, axis=1),
                     use_container_width=True, hide_index=True)
        n_match = sum(sim["sifted_mask"])
        st.write(
            f"Bob's basis matched Alice's for **{n_match} / {num_bits}** photons "
            f"({100 * n_match / num_bits:.0f}%). Only these survive sifting."
        )

        # Step — Sifting
        step += 1
        st.header(f"Step {step} — Sifting")
        st.write(
            "Alice and Bob announce their bases over a public classical channel — not the bit values. "
            "Photons where bases differ are discarded. The survivors form the sifted key. "
            "Eve can hear this exchange, but learning the bases reveals nothing about the bit values."
        )
        sifted_idx = sim["sifted_idx"]

        if not sifted_idx:
            st.warning("No photons survived sifting. Try running again.")
        else:
            df_sifted = pd.DataFrame({
                "Original photon #": [i + 1 for i in sifted_idx],
                "Shared basis":      [sim["alice_bases"][i] for i in sifted_idx],
                "Alice bit":         sim["alice_sifted"],
                "Bob bit":           sim["bob_sifted"],
                "Agree":             ["Yes" if a == b else "No"
                                      for a, b in zip(sim["alice_sifted"], sim["bob_sifted"])],
            })
            st.dataframe(df_sifted.style.apply(hl_sifted, axis=1),
                         use_container_width=True, hide_index=True)
            n_sifted = len(sifted_idx)
            n_agree  = sum(a == b for a, b in zip(sim["alice_sifted"], sim["bob_sifted"]))
            st.write(
                f"Sifted key: **{n_sifted} bits**. "
                f"Alice and Bob agree on **{n_agree}** and disagree on **{n_sifted - n_agree}**."
            )

            # Step — QBER
            step += 1
            st.header(f"Step {step} — QBER estimation")
            st.write(
                f"A random sample of **{len(sim['sample_pos'])} sifted bits** "
                f"({sample_fraction * 100:.0f}%) is compared publicly. "
                "These bits are then permanently discarded. "
                "The fraction that disagrees is the Quantum Bit Error Rate (QBER)."
            )
            df_sample = pd.DataFrame({
                "Sifted position": [p + 1 for p in sim["sample_pos"]],
                "Alice bit":       sim["sample_alice"],
                "Bob bit":         sim["sample_bob"],
                "Match":           ["Yes" if a == b else "No"
                                    for a, b in zip(sim["sample_alice"], sim["sample_bob"])],
            })
            st.dataframe(df_sample.style.apply(hl_sample, axis=1),
                         use_container_width=True, hide_index=True)

            qber_pct = sim["qber"] * 100
            q1, q2, q3 = st.columns(3)
            q1.metric("Bits sampled", len(sim["sample_pos"]))
            q2.metric("Errors found", sim["errors"])
            q3.metric("QBER",         f"{qber_pct:.1f}%")

            if qber_pct > qber_threshold:
                st.error(
                    f"QBER = {qber_pct:.1f}% exceeds {qber_threshold}%. Protocol aborted. "
                    "Alice and Bob discard everything and retry on a different channel."
                )
            else:
                st.success(
                    f"QBER = {qber_pct:.1f}% is within {qber_threshold}%. Channel accepted as secure."
                )

            if eve_present:
                st.info(
                    "Expected QBER with a full intercept-resend attack: **25%**. "
                    "Eve guesses the wrong basis 50% of the time; on those photons Bob's "
                    "measurement in Alice's basis is random → error probability = 0.5 × 0.5 = 0.25."
                )
            else:
                st.info(
                    "Expected QBER with no eavesdropping on an ideal channel: **0%**. "
                    "Real systems see 1–5% from detector noise and optical misalignment."
                )

            # Step — Final key
            step += 1
            st.header(f"Step {step} — Final shared key")

            if qber_pct > qber_threshold:
                st.write("Protocol aborted due to high QBER. No key established.")
            elif not sim["alice_key"]:
                st.warning("No bits remain after QBER sampling. Increase photon count and run again.")
            else:
                st.write(
                    "The remaining sifted bits form the raw shared key. "
                    "A production system would follow this with **error correction** (e.g., Cascade or LDPC) "
                    "and **privacy amplification** (hashing the string down to remove any partial "
                    "information Eve gathered). Both are skipped here."
                )

                kc1, kc2 = st.columns(2)
                with kc1:
                    st.write("**Alice's key**")
                    st.code("".join(str(b) for b in sim["alice_key"]))
                with kc2:
                    st.write("**Bob's key**")
                    st.code("".join(str(b) for b in sim["bob_key"]))

                n_key = len(sim["alice_key"])
                if sim["alice_key"] == sim["bob_key"]:
                    st.success(f"Keys match. Shared secret: **{n_key} bits**.")
                else:
                    n_diff = sum(a != b for a, b in zip(sim["alice_key"], sim["bob_key"]))
                    st.warning(f"Keys differ at {n_diff} / {n_key} positions. Error correction needed.")

                st.divider()
                st.subheader("Run summary")
                s1, s2, s3, s4, s5 = st.columns(5)
                s1.metric("Photons sent",        num_bits)
                s2.metric("Survived sifting",    n_sifted)
                s3.metric("Sacrificed for QBER", len(sim["sample_pos"]))
                s4.metric("Final key length",    n_key)
                s5.metric("Key rate",            f"{n_key / num_bits * 100:.1f}%")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — EDUCATORS
# ═════════════════════════════════════════════════════════════════════════════

with tab_educator:

    st.subheader("Teaching Modules for QKD Curriculum")
    st.write(
        "Eight self-contained modules: classical cryptography foundations (RSA, ECC, Shor's algorithm), "
        "the quantum mechanics needed for QKD, the BB84 protocol in depth, its security guarantees, "
        "and real-world deployment context. Each module includes learning objectives, content, and "
        "suggested discussion questions."
    )

    # ── Module 1: Why do we need secure key exchange? ────────────────────────
    with st.expander("Module 1 — Why do we need secure key exchange?", expanded=True):
        st.markdown("""
**Learning objectives**
- Explain the difference between symmetric and asymmetric encryption.
- Describe the key distribution problem and why it is non-trivial.
- Identify the mathematical assumptions underlying Diffie-Hellman and RSA.

---

**Background**

All classical encryption ultimately reduces to a shared secret: Alice and Bob both know a key, and
anyone who intercepts their messages but doesn't know the key cannot read them. The problem is
*getting* that shared key to both parties without a pre-existing secure channel.

**Symmetric encryption** (e.g., AES) is fast and secure but requires both parties to already share
a key. If Alice and Bob have never met, how do they agree on one over an open network?

**Asymmetric (public-key) encryption** solves this. Each party has a public key (freely shared) and
a private key (secret). The security of schemes like RSA and Diffie-Hellman rests on the hardness
of specific mathematical problems:
- **RSA** → factoring a large integer *n = p × q* into its prime factors is hard.
- **Diffie-Hellman / ECDH** → the discrete logarithm problem: given *g^x mod p*, find *x*.

These are *computationally* hard on classical computers, not *fundamentally* impossible.
A sufficiently powerful computer running the right algorithm could break them.

**Diffie-Hellman key exchange** (simplified):
1. Alice and Bob publicly agree on parameters *g* and *p*.
2. Alice picks secret *a*, sends *g^a mod p* to Bob.
3. Bob picks secret *b*, sends *g^b mod p* to Alice.
4. Both compute *g^(ab) mod p* — this is the shared secret.
5. An eavesdropper sees *g^a mod p* and *g^b mod p*, but computing *g^(ab) mod p* from these
   requires solving the discrete logarithm — hard classically, easy on a quantum computer (Shor, 1994).

---

**Discussion questions**
1. If a courier delivers the key in person, is the encryption "unbreakable"? What are the operational
   limitations of this approach at scale?
2. Why is the hardness of factoring not a *proof* of security? What would a proof require?
3. If RSA keys are doubled in length (1024 → 2048 bits), how much harder does factoring become
   classically? How does this scale on a quantum computer running Shor's algorithm?
""")

    # ── Module 2: RSA ─────────────────────────────────────────────────────────
    with st.expander("Module 2 — RSA: Key Generation, Encryption, and the Factoring Problem"):
        st.markdown("""
**Learning objectives**
- Describe RSA key generation step by step.
- Explain encryption and decryption using modular exponentiation.
- Identify the integer factoring problem as RSA's security foundation.
- Explain why larger key sizes slow down classical factoring but not Shor's algorithm.

---

**What problem does RSA solve?**

Before RSA (Rivest, Shamir, Adleman, 1977), two parties had to share a secret key in advance —
by courier, phone, or in person. RSA allows two strangers to exchange encrypted messages over
a public channel with no prior contact.

**Key generation**

1. Choose two large distinct primes *p* and *q* (each 1024–2048 bits in practice).
2. Compute the modulus *n = p × q*.
3. Compute Euler's totient *φ(n) = (p−1)(q−1)*.
4. Choose a public exponent *e* such that *1 < e < φ(n)* and *gcd(e, φ(n)) = 1*.
   In practice *e = 65537* is almost universally used (small, fixed, odd, no small prime factors).
5. Compute the private exponent *d* as the modular inverse of *e*: *d = e⁻¹ mod φ(n)*.
   This means *e × d ≡ 1 (mod φ(n))*.

**Public key**: *(n, e)* — shared openly.
**Private key**: *(n, d)* — kept secret. (Equivalently, the factorisation *p, q*.)

**Encryption** (sender knows *(n, e)*):
*c = mᵉ mod n*
where *m* is the message encoded as an integer with *m < n*.

**Decryption** (recipient knows *(n, d)*):
*m = cᵈ mod n*

This works because Euler's theorem guarantees *(mᵉ)ᵈ = m^(ed) ≡ m (mod n)* when *gcd(m, n) = 1*.

**Why it is secure (classically)**

To recover *d* from the public key *(n, e)*, an attacker must compute *φ(n) = (p−1)(q−1)*,
which requires knowing *p* and *q* — i.e., factoring *n*.

The best known classical factoring algorithm, the General Number Field Sieve (GNFS), runs in
sub-exponential time roughly *exp(O((log n)^(1/3) (log log n)^(2/3)))*.
For a 2048-bit modulus, factoring would take far longer than the age of the universe on any
classical computer. This is why RSA-2048 is currently considered safe against classical adversaries.

**Practical notes**
- Raw RSA (textbook RSA) is not semantically secure. Real implementations use OAEP padding for
  encryption and PSS padding for signatures.
- RSA private-key operations (decryption, signing) are computationally expensive: ~1000× slower
  than AES for equivalent data. In practice, RSA encrypts a symmetric key; the symmetric key then
  encrypts the bulk data.
- NIST recommends RSA-3072 or above for new systems; RSA-2048 is acceptable through 2030.

---

**Discussion questions**
1. Why can't the attacker simply compute *d = e⁻¹ mod n* directly (without factoring *n*)?
   What piece of information are they missing?
2. If *p* and *q* are accidentally chosen to be close together (close prime attack), what happens?
   How does this motivate the requirement that *p* and *q* be "far apart"?
3. RSA signing is: *s = mᵈ mod n*; verification is: *m = sᵉ mod n*.
   How does this differ structurally from encryption? What could go wrong if the same key pair
   is used for both encryption and signing?
""")

    # ── Module 3: ECC ─────────────────────────────────────────────────────────
    with st.expander("Module 3 — Elliptic Curve Cryptography (ECC)"):
        st.markdown("""
**Learning objectives**
- Describe what an elliptic curve is over a finite field.
- Explain point addition geometrically and algebraically.
- State the Elliptic Curve Discrete Logarithm Problem (ECDLP).
- Describe ECDH key exchange and ECDSA signing.
- Compare ECC and RSA in terms of key size, performance, and security assumptions.

---

**What is an elliptic curve?**

An elliptic curve over a finite field *F_p* (integers mod a prime *p*) is the set of points
*(x, y)* satisfying:

*y² ≡ x³ + ax + b (mod p)*

together with a special "point at infinity" *O* that acts as the group identity.

For cryptographic use, the parameters *(a, b, p)* are fixed and public. A *generator point* *G*
on the curve is also specified. Every party uses the same curve and the same *G*.

**Point addition**

Given two points *P* and *Q* on the curve, their sum *P + Q* is defined geometrically: draw the
line through *P* and *Q*, find its third intersection with the curve, and reflect that point over
the x-axis. For *P + P* (point doubling), use the tangent line at *P* instead.

This operation is closed (the result is always on the curve), associative, commutative, and has
an identity element *O*. The curve points under addition form an abelian group.

**Scalar multiplication**

For a positive integer *k* and point *P*, define:
*kP = P + P + ... + P* (*k* times)

This can be computed efficiently using double-and-add (analogous to fast exponentiation): O(log k)
point doublings and additions. For *k* of 256 bits, this takes roughly 384 operations.

**The Elliptic Curve Discrete Logarithm Problem (ECDLP)**

Given a generator point *G* and a public point *Q = kG*, find *k*.

This is believed to be computationally hard. No sub-exponential classical algorithm for ECDLP
is known (unlike for ordinary discrete log, where index calculus works). This means ECC achieves
the same security level as RSA with much smaller keys:

| Security level | RSA key size | ECC key size |
|---------------|-------------|-------------|
| 128-bit        | 3072 bits    | 256 bits     |
| 192-bit        | 7680 bits    | 384 bits     |
| 256-bit        | 15360 bits   | 521 bits     |

**ECDH key exchange**

1. Alice picks private key *a* (a random integer); computes public key *A = aG*.
2. Bob picks private key *b*; computes public key *B = bG*.
3. They exchange *A* and *B* over a public channel.
4. Alice computes *aB = a(bG) = abG*.
5. Bob computes *bA = b(aG) = abG*.
6. Both arrive at the same shared secret point *abG*. Eve sees *A* and *B* but cannot compute
   *abG* without solving ECDLP.

**ECDSA digital signatures** (in brief)

To sign message hash *h* with private key *d*:
1. Pick a random *k*, compute *R = kG*, let *r = R_x mod n*.
2. Compute *s = k⁻¹(h + dr) mod n*.
3. Signature is *(r, s)*.

Verification uses the public key *Q = dG* to confirm the relationship without revealing *d*.
Critical: *k* must be uniformly random and never reused. The Sony PlayStation 3 private key was
extracted in 2010 because their ECDSA implementation used a fixed *k*.

**Common curves**
- **NIST P-256 / secp256r1** — standard in TLS, used by most browsers and servers.
- **X25519 (Curve25519)** — preferred for ECDH; designed to resist several implementation
  attacks; now widely used in TLS 1.3, Signal, WireGuard.
- **secp256k1** — Bitcoin and Ethereum signing (ECDSA).

---

**Discussion questions**
1. RSA has a trapdoor (the factorisation). What is the analogous trapdoor in ECC?
   Why is the ECDLP believed to be hard while ordinary integer factoring has sub-exponential
   classical algorithms?
2. Why does reusing *k* in ECDSA leak the private key? Derive the formula.
   Why is X25519 designed to avoid this class of mistake?
3. Compared to NIST P-256, Curve25519 was designed with different priorities.
   What are they, and what does this tell you about the difference between a standard being
   *secure* and being *trustworthy*?
""")

    # ── Module 4: Shor's Algorithm ────────────────────────────────────────────
    with st.expander("Module 4 — Shor's Algorithm: How Quantum Computers Break RSA and ECC"):
        st.markdown("""
**Learning objectives**
- Explain at a conceptual level how Shor's algorithm reduces integer factoring to period finding.
- Describe why the Quantum Fourier Transform makes period finding efficient on a quantum computer.
- State the resource requirements for breaking RSA-2048.
- Explain why Shor's algorithm also breaks ECC and Diffie-Hellman.

---

**Historical context**

In 1994, Peter Shor (then at Bell Labs) published an algorithm that runs on a quantum computer
and solves two problems in polynomial time:

1. **Integer factoring** — given *n*, find *p* and *q* such that *n = p × q*.
2. **Discrete logarithm** — given *g, h, p*, find *x* such that *g^x ≡ h (mod p)*.

These two problems are the security foundations of RSA and Diffie-Hellman respectively.
The elliptic curve discrete logarithm problem (ECDLP) is also solved by a generalisation of
Shor's discrete log algorithm. In other words, Shor's algorithm breaks RSA, DH, ECDH, and ECDSA
simultaneously.

**From factoring to period finding**

Shor's key insight is a classical reduction: factoring *n* is equivalent to finding the *period*
of the function:

*f(x) = aˣ mod n*

for a randomly chosen *a* coprime to *n*.

The period *r* is the smallest positive integer such that *aʳ ≡ 1 (mod n)*.
Once *r* is known, one can compute *gcd(a^(r/2) ± 1, n)* — this yields non-trivial factors of
*n* with high probability (roughly 50% per attempt; a few repetitions suffice).

Finding *r* classically is just as hard as factoring — it requires evaluating *f* exponentially
many times. The quantum speedup comes from finding *r* efficiently.

**Where the quantum speedup comes from**

A quantum computer can prepare a superposition of all inputs simultaneously:

*|0⟩ → (1/√N) Σ|x⟩*

and evaluate *f(x)* for all *x* at once, producing:

*(1/√N) Σ|x⟩|f(x)⟩*

This is not useful directly — measuring collapses it to a single value. But applying the
**Quantum Fourier Transform (QFT)** to the *x* register transforms this superposition into one
that is peaked at multiples of *1/r*. Measuring then gives a value close to *j/r* for some
integer *j*, from which *r* can be extracted using classical continued fraction algorithms.

The classical DFT runs in O(N log N) for N points. The QFT runs in O(log² N) on a quantum
computer — an exponential improvement. This is what gives Shor's algorithm its power.

**Resource requirements**

Breaking RSA-2048 with Shor's algorithm requires approximately:
- **~4,000 logical qubits** (qubits with error correction applied).
- **~10⁹ gate operations** (T-gates, which are expensive to implement fault-tolerantly).
- Each logical qubit requires roughly **1,000–10,000 physical qubits** depending on the error
  correction code and hardware error rates.
- Total physical qubit count: **millions**.

Current state-of-the-art quantum processors have a few hundred to low thousands of physical
qubits with error rates around 0.1–1%, far from the ~0.01% threshold needed for the error
correction codes used in Shor estimates. The consensus timeline for a cryptographically relevant
quantum computer (CRQC) is approximately **10–20 years**, with substantial uncertainty.

**Grover's algorithm (a separate threat to symmetric cryptography)**

Grover's algorithm provides a quadratic speedup for unstructured search. For a symmetric key of
length *n* bits, Grover's reduces effective security from *n* bits to *n/2* bits:
- AES-128 → ~64-bit security against a quantum adversary.
- AES-256 → ~128-bit security (still safe; NIST retains AES-256 as quantum-resistant).

Grover is a much smaller threat than Shor: doubling key sizes compensates entirely. Post-quantum
symmetric cryptography is primarily a matter of key length, not algorithm replacement.

**The difference between breaking RSA and breaking symmetric encryption**

Shor's provides an *exponential* speedup for factoring (polynomial vs exponential time).
Grover's provides only a *quadratic* speedup for search. This is why RSA and ECC require complete
replacement, while AES-256 and SHA-3 can be retained with appropriate parameter choices.

---

**Discussion questions**
1. Shor's algorithm is probabilistic — it succeeds with probability roughly 1/2 per run and must
   be repeated. How does this affect the practical time to break RSA-2048?
2. The QFT requires coherent superposition across many qubits for many gate operations.
   What physical challenges make this hard to achieve, and how do quantum error correction
   codes address them?
3. Grover's algorithm is sometimes described as "breaking" AES-128. Is this accurate?
   What would an attacker actually need to do to decrypt AES-128-encrypted data with Grover's
   algorithm, and why is this impractical even with a CRQC?
""")

    # ── Module 5: Quantum mechanics background ────────────────────────────────
    with st.expander("Module 5 — Quantum mechanics background for QKD"):
        st.markdown("""
**Learning objectives**
- Define quantum superposition and explain what "collapsing" a superposition means.
- Describe photon polarisation as a physical qubit.
- State and explain the no-cloning theorem at an intuitive level.
- Explain why measuring a quantum state in the wrong basis gives a random result.

---

**Polarisation as a qubit**

Light is an electromagnetic wave, and its electric field oscillates in a direction — the
*polarisation*. A photon can be polarised vertically (|0⟩), horizontally (|1⟩), at 45° (|+⟩),
or at 135° (|−⟩). A polarising filter lets through only photons aligned with it.

In quantum mechanics, a photon does not have a single definite polarisation until it is measured.
Before measurement, it exists in a **superposition** — a combination of two basis states.

**Measurement and basis**

If you prepare a photon in state |0⟩ (vertical) and measure it with a rectilinear filter (+):
- Vertical filter: 100% probability of passing → you measure 0, consistently.

If you instead measure that same |0⟩ photon with a diagonal filter (×):
- 45° filter: 50% probability of passing → random outcome, 0 or 1 with equal probability.

After the measurement, the photon's state has been **projected** (collapsed) into one of the
diagonal basis states — the original vertical polarisation is gone.

**The no-cloning theorem (Wootters & Zurek, 1982)**

It is impossible to create a perfect copy of an arbitrary unknown quantum state.

Formal statement: there is no unitary operation *U* such that
*U|ψ⟩|0⟩ = |ψ⟩|ψ⟩* for all *|ψ⟩*.

The intuition: to copy a state you must first know what it is. To know what it is you must
measure it. Measurement disturbs the state (unless you happen to measure in exactly the right
basis, which you cannot guarantee without prior knowledge). Therefore perfect copying is impossible.

Implication for eavesdropping: Eve cannot intercept a photon, copy its state for later analysis,
and pass the original on undisturbed. She must interact with the photon, and that interaction
leaves a trace.

**Teaching note**
A good analogy: imagine a die that is mid-roll, with no definite face up. Once you look at it
(measure it), it "collapses" to a definite face. If you then want to tell someone the number, you
already know it — but the die is now *committed* to that face. The original mid-roll state is gone.
The analogy breaks down (dice are classical) but it conveys the irreversibility of measurement.

---

**Discussion questions**
1. The no-cloning theorem is a *theorem* — it follows from the linearity of quantum mechanics.
   What does linearity mean here, and why does cloning violate it?
2. Is the no-cloning theorem a practical limitation or a fundamental one? Could a future technology
   circumvent it?
3. How does Heisenberg's uncertainty principle relate to the randomness of wrong-basis measurements?
   Are they the same statement?
""")

    # ── Module 6: The BB84 protocol ───────────────────────────────────────────
    with st.expander("Module 6 — The BB84 protocol in depth"):
        st.markdown("""
**Learning objectives**
- Describe each of the five phases of BB84 with physical justification.
- Derive the expected QBER under a full intercept-resend attack.
- Distinguish what information is shared publicly versus kept secret.
- Explain why the public basis announcements do not help an eavesdropper.

---

**Phase 1 — Quantum transmission**

Alice randomly generates a bit string *b₁b₂…bₙ* and a basis string *θ₁θ₂…θₙ*, each bit chosen
uniformly at random. She prepares photon *i* in the state determined by *(bᵢ, θᵢ)*:

| bᵢ | θᵢ = + (rectilinear) | θᵢ = × (diagonal) |
|----|---------------------|--------------------|
| 0  | \\|0⟩ vertical         | \\|+⟩ 45°            |
| 1  | \\|1⟩ horizontal       | \\|−⟩ 135°           |

She sends the photons one at a time through the quantum channel (an optical fibre or free-space
link). *No classical information travels on this channel during transmission.*

**Phase 2 — Bob's measurement**

Bob independently picks a random basis *φᵢ* for each photon and measures it.
- If *φᵢ = θᵢ*: measurement is in the correct basis → Bob recovers *bᵢ* exactly.
- If *φᵢ ≠ θᵢ*: the photon is in a superposition relative to Bob's basis → random outcome.

Bob records his basis choices and measurement outcomes.

**Phase 3 — Sifting**

Over a public classical channel (authenticated but not secret), Alice announces *θ₁…θₙ*.
Bob announces *φ₁…φₙ*. Both discard positions where *θᵢ ≠ φᵢ*. On average, ~50% survive.
The surviving bits are the *sifted key*.

What Eve learns: the bases of sifted photons. This is useless because the bit value is
*orthogonal* information — knowing the basis of a sifted photon tells you nothing about the bit.

**Phase 4 — QBER estimation**

Alice and Bob publicly sacrifice a random subset *S* of the sifted key and compare values.
QBER = |{i ∈ S : Alice's bit ≠ Bob's bit}| / |S|.

Derivation of expected QBER under full intercept-resend:
- Eve picks the wrong basis with probability 1/2.
- When she does, she resends a photon in her basis. Bob (in Alice's basis, i.e., the sifted case)
  measures that photon in the wrong basis → random result → error with probability 1/2.
- Combined: *P(error in sifted key) = 1/2 × 1/2 = 1/4 = 25%*.

**Phase 5 — Key reconciliation and privacy amplification**

If QBER is below threshold:
1. **Error correction** — Alice and Bob run a classical error-correcting protocol (e.g., Cascade)
   to make their sifted keys identical. This leaks some information to Eve.
2. **Privacy amplification** — they apply a universal hash function to compress the key.
   Compression by *k* bits reduces Eve's information exponentially in *k*, making her expected
   knowledge about the final key essentially zero.

The final string is the **quantum-secure shared key**.

---

**Discussion questions**
1. Why does BB84 require an *authenticated* classical channel for sifting? What attack becomes
   possible if the classical channel is unauthenticated?
2. If Alice and Bob sacrifice 25% of the sifted key for QBER estimation, and there is no Eve,
   what is the overall key rate as a fraction of photons sent? Work it out numerically.
3. A partial intercept-resend attack (Eve only intercepts fraction *f* of photons) gives QBER = f/4.
   At what *f* does QBER cross the 11% threshold? What does this imply for Eve's information gain?
""")

    # ── Module 7: Security analysis ───────────────────────────────────────────
    with st.expander("Module 7 — Security: information-theoretic vs computational"):
        st.markdown("""
**Learning objectives**
- Contrast information-theoretic security with computational security.
- Explain what "unconditional security" means and what it requires in practice.
- Identify the assumptions BB84's security proofs rely on.
- Describe the role of privacy amplification in the security argument.

---

**Two kinds of security**

**Computational security** (RSA, AES, Diffie-Hellman): breaking the scheme requires solving a
problem assumed to be computationally hard. Security is conditional on that hardness assumption
and on no adversary having sufficient computing power. A faster algorithm or a more powerful
computer can, in principle, break it.

**Information-theoretic (unconditional) security**: no adversary, regardless of computing power,
can extract the plaintext. The one-time pad is the classic example. BB84, when implemented
correctly, achieves this for key distribution.

**The BB84 security argument**

The original security proof (Mayers 1996, Lo & Chau 1999, Shor & Preskill 2000 simplified) shows:

1. Any eavesdropping strategy Eve uses introduces disturbance that increases the QBER.
2. The QBER is an upper bound on the information Eve can have about the sifted key.
3. Privacy amplification reduces Eve's information to ε-close to zero (exponentially small in the
   length of the privacy amplification parameter).
4. The final key is ε-secure: Eve cannot distinguish it from a uniformly random string.

**Practical caveats — the assumptions**

The proof assumes:
- **Perfect single-photon sources.** Real laser sources emit weak coherent pulses, not single
  photons. Multi-photon pulses allow a *photon number splitting* (PNS) attack. Decoy-state
  protocols (Hwang 2003, Lo et al. 2005) address this.
- **Trusted measurement devices.** Device-independent QKD (DI-QKD) removes this assumption
  but is much harder to implement experimentally.
- **An authenticated classical channel.** Without authentication, a man-in-the-middle can replace
  both Alice and Bob with impersonators. Authentication can be done with a small pre-shared secret
  and information-theoretically secure MACs.
- **No side-channel leakage.** Real hardware leaks timing, power, and optical signals. Side-channel
  attacks on QKD hardware have been demonstrated in the lab.

---

**Discussion questions**
1. The one-time pad is provably secure (Shannon 1949). Why is it not used everywhere?
   In what sense does BB84 solve the problem the one-time pad leaves open?
2. If a laser pulse contains on average 0.1 photons (standard in practice), what fraction of pulses
   contain exactly 2 photons? (Use the Poisson distribution.) Why are two-photon pulses dangerous?
3. "Quantum cryptography is unbreakable." Critique this claim precisely.
""")

    # ── Module 8: Real-world deployments ─────────────────────────────────────
    with st.expander("Module 8 — Real-world QKD deployments and open problems"):
        st.markdown("""
**Learning objectives**
- Describe the main physical implementations of QKD (fibre, free-space, satellite).
- Identify the distance and rate limitations of current systems.
- Explain the role of quantum repeaters and why they are hard to build.
- List active research directions in QKD and post-quantum cryptography.

---

**Fibre-based QKD**

Single photons can travel through standard telecom optical fibre, but they are absorbed
exponentially with distance. At 1550 nm (telecom C-band), typical loss is ~0.2 dB/km.
After ~200 km, the signal rate drops below the dark-count noise floor of single-photon detectors.
Current commercial QKD systems (ID Quantique, Toshiba) operate at distances up to ~100–150 km
with key rates of tens of kbps.

**Trusted nodes** extend range: Alice sends to a relay node over a secure QKD link, the relay
re-encrypts and forwards to Bob. The relay must be physically trusted — a compromise point.

**Quantum repeaters** would allow true end-to-end quantum security over arbitrary distances by
entanglement swapping and purification. They require quantum memories (not yet available
commercially) and are an active research frontier.

**Free-space and satellite QKD**

Photons can travel through free-space (air, vacuum) with lower loss than fibre over long distances.
China's Micius satellite (2016) demonstrated satellite-based QKD at distances up to ~1200 km
(ground to satellite), achieving intercontinental QKD between China and Austria (2017).
Free-space systems are limited by atmospheric turbulence and require line-of-sight.

**Current deployment examples**
- Tokyo QKD Network (NEC/Toshiba/NTT, 2010)
- Madrid Metro QKD test (UPM/Telefónica, 2021)
- UK National Quantum Network (BT, 2023)
- HSBC/BT Openreach QKD trial on London production fibre (2023)
- Singapore's Quantum Engineering Programme national QKD testbed

**Open problems and research directions**
- Quantum repeaters with long-coherence-time memories
- Device-independent QKD at practical rates
- Continuous-variable (CV-QKD): using coherent states and homodyne detection rather than
  single photons — compatible with standard telecom hardware
- Composable security proofs for finite-length keys (real-world key blocks are short)
- Hybrid QKD + post-quantum cryptography architectures

---

**Discussion questions**
1. A trusted relay node breaks the end-to-end quantum security of QKD.
   In what threat model is a network of trusted relays still useful?
2. Satellite QKD currently works only at night (daylight photons swamp single-photon detectors).
   What engineering approaches could address this?
3. Compare the security assumptions of CV-QKD with those of single-photon BB84.
   Under what conditions would you prefer one over the other?
""")

    st.divider()
    st.caption(
        "Suggested course sequence: Modules 1–4 as prerequisites (classical crypto, RSA, ECC, Shor's), "
        "Module 5 (quantum mechanics), Module 6 (BB84 protocol), Module 7 (security theory), "
        "Module 8 (applications). The Students tab provides a live simulator to accompany Module 6."
    )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — INDUSTRY
# ═════════════════════════════════════════════════════════════════════════════

with tab_industry:

    st.subheader("Quantum Readiness for Financial Institutions")
    st.write(
        "A briefing on the quantum threat to classical cryptography, the NIST post-quantum "
        "standards, and the strategic choices facing banks and financial market infrastructure "
        "as they plan their cryptographic migration."
    )

    # ── Section 1: The quantum threat ─────────────────────────────────────────
    st.header("1. The Quantum Threat to Cryptography")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown("""
In 1994, Peter Shor published a quantum algorithm that can factor integers and solve the discrete
logarithm problem in **polynomial time** on a sufficiently large quantum computer. This directly
breaks RSA, Diffie-Hellman, and elliptic curve cryptography (ECC) — the three algorithms that
secure virtually all internet communications today, including SWIFT messaging, TLS connections to
banking APIs, digital signatures on securities transactions, and encrypted storage.

Grover's algorithm (1996) provides a quadratic speedup for searching unstructured databases,
which effectively halves the security level of symmetric keys. AES-128 drops to approximately
64-bit security against a quantum adversary; AES-256 retains approximately 128-bit security.
**Symmetric encryption is weakened but not broken.** The critical threat is to public-key cryptography.

A quantum computer capable of breaking 2048-bit RSA would need roughly **4,000 logical qubits**
running fault-tolerantly for hours. Current state-of-the-art quantum processors have hundreds to
low thousands of *physical* qubits with high error rates. The consensus estimate for a
cryptographically relevant quantum computer (CRQC) is **10–20 years**, though uncertainty is high
in both directions.
""")
    with col_b:
        st.info(
            "**Algorithms at risk**\n\n"
            "RSA (all key sizes)\n\n"
            "Diffie-Hellman\n\n"
            "Elliptic curve cryptography (ECDH, ECDSA)\n\n"
            "---\n\n"
            "**Not directly broken**\n\n"
            "AES-256 (weakened: ~128-bit security)\n\n"
            "SHA-256 / SHA-3 (weakened: ~128-bit)\n\n"
            "HMAC-SHA-256"
        )

    # ── Section 2: Harvest now, decrypt later ─────────────────────────────────
    st.header("2. Harvest Now, Decrypt Later")

    st.warning(
        "This is the most immediate threat for financial institutions, and it is active **today** — "
        "not in 10–20 years."
    )
    st.markdown("""
Adversaries — nation-state intelligence agencies are the primary concern — do not need a quantum
computer *now* to threaten data encrypted *now*. They can:

1. **Intercept and store** encrypted network traffic, signed documents, and key exchange records today.
2. **Wait** until a CRQC becomes available.
3. **Decrypt retrospectively** using Shor's algorithm.

This is sometimes called the **"store now, decrypt later"** or **SNDL** threat.

**Why this matters for financial institutions specifically:**
- Regulatory requirements in many jurisdictions mandate retention of trade records, communications,
  and audit logs for 5–10 years. These are exactly the data classes adversaries would target.
- Long-lived digital signatures on securities, contracts, and property records must remain
  verifiable for decades. A signature made with ECDSA today can be forged retroactively once
  ECC is broken.
- Customer data (KYC records, account details) has indefinite sensitivity.

**Mosca's theorem** provides a useful planning frame. Let:
- *X* = years until a CRQC exists (unknown; estimate 10–20)
- *Y* = years your current encrypted data must remain confidential (known for each asset class)
- *Z* = years required to complete your cryptographic migration (known from your IT programme)

If *Z + Y > X*, you have a problem. For data with 10-year confidentiality requirements and a
5-year migration programme, you need to start migration *now* even if a CRQC is 10 years away.
""")

    # ── Section 3: NIST PQC standards ─────────────────────────────────────────
    st.header("3. NIST Post-Quantum Cryptography Standards")

    st.markdown("""
After an eight-year global evaluation process, NIST published three finalized **post-quantum
cryptography (PQC)** standards in August 2024. These are drop-in replacements for current
public-key algorithms and require only software changes — no new hardware infrastructure.
Full documentation is available on the NIST CSRC website:
[FIPS 203 (ML-KEM)](https://csrc.nist.gov/pubs/fips/203/final) ·
[FIPS 204 (ML-DSA)](https://csrc.nist.gov/pubs/fips/204/final) ·
[FIPS 205 (SLH-DSA)](https://csrc.nist.gov/pubs/fips/205/final) ·
[PQC project overview](https://csrc.nist.gov/projects/post-quantum-cryptography)
""")

    pqc_data = pd.DataFrame({
        "Standard":    ["FIPS 203 (ML-KEM)", "FIPS 204 (ML-DSA)", "FIPS 205 (SLH-DSA)"],
        "Based on":    ["CRYSTALS-Kyber", "CRYSTALS-Dilithium", "SPHINCS+"],
        "Purpose":     ["Key encapsulation (replaces ECDH/RSA key exchange)",
                        "Digital signatures (replaces ECDSA/RSA-PSS)",
                        "Digital signatures (hash-based, conservative fallback)"],
        "Hard problem": ["Module learning with errors (MLWE)",
                         "Module learning with errors / short integer solution",
                         "Hash function security only"],
        "Status":      ["Final (Aug 2024)", "Final (Aug 2024)", "Final (Aug 2024)"],
    })
    st.dataframe(pqc_data, use_container_width=True, hide_index=True)

    st.markdown("""
**What financial institutions should do with these standards:**
- **TLS / API connections**: migrate to ML-KEM for key exchange in TLS 1.3. Chrome and Firefox
  already support hybrid X25519+ML-KEM. OpenSSL 3.x includes ML-KEM support.
- **Digital signatures**: migrate signing infrastructure (code signing, document signing, certificate
  authorities) to ML-DSA. Note that FIPS 204 signature sizes are larger than ECDSA — test for
  performance impact on high-volume signing systems.
- **Certificate infrastructure**: NIST and CA/Browser Forum are coordinating on post-quantum
  X.509 certificates. Expect a multi-year transition period with hybrid certificates
  (classical + post-quantum) as a bridge.
- **HSMs and key management**: most major HSM vendors (Thales, Entrust, Utimaco) have roadmaps
  for FIPS 203/204/205 support. Verify your HSM vendor's timeline against your migration plan.
""")

    # ── Section 4: QKD vs PQC ─────────────────────────────────────────────────
    st.header("4. QKD vs Post-Quantum Cryptography — What is the Difference?")

    st.markdown("""
QKD and PQC are complementary, not competing, approaches to the same problem. Understanding the
distinction is important for investment and procurement decisions.
""")

    comparison = pd.DataFrame({
        "Property":              [
            "Security basis",
            "Hardware required",
            "Distance",
            "Integration cost",
            "Maturity",
            "Standardisation",
            "Protects against CRQC",
            "Protects against classical attacks",
            "Authentication requirement",
        ],
        "QKD":                   [
            "Physical laws (no-cloning theorem)",
            "Dedicated quantum channel + single-photon hardware",
            "~100–150 km per segment (trusted relays for longer)",
            "Very high — new fibre, detectors, hardware refresh cycles",
            "Lab-proven; limited commercial deployments",
            "No global interoperability standard yet",
            "Yes (for key distribution)",
            "Yes",
            "Requires a pre-shared secret or PQC for classical channel auth",
        ],
        "PQC (NIST FIPS 203/204)": [
            "Mathematical hardness (MLWE — believed quantum-hard)",
            "Software only — runs on existing hardware",
            "Unlimited",
            "Low to moderate — library + protocol updates",
            "Mature algorithms; standardised Aug 2024",
            "NIST FIPS 203, 204, 205 — global standard",
            "Yes (assuming hardness holds)",
            "Yes",
            "Self-contained — no pre-shared secret needed",
        ],
    })
    st.dataframe(comparison, use_container_width=True, hide_index=True)

    st.markdown("""
**Practical guidance:**

- **For most financial institutions, PQC is the primary migration path.** It is cheaper, faster to
  deploy, requires no physical infrastructure, and is standardised. NIST-compliant PQC libraries
  are available today in OpenSSL, BouncyCastle, and AWS/Azure/GCP SDK updates.

- **QKD is relevant for specific high-value, fixed-topology links** where information-theoretic
  security is required and capital expenditure is justified — for example, a data centre
  interconnect carrying real-time settlement data between two sites owned by the same institution.

- **A hybrid architecture** (QKD-derived keys XOR'd with PQC-derived keys) provides the highest
  assurance: even if one mechanism is broken, the combined key remains secure.
  ETSI GS QKD 014 specifies a REST API for integrating QKD key servers into standard applications.
""")

    # ── Section 5: Regulatory landscape ──────────────────────────────────────
    st.header("5. Regulatory Landscape and Industry Guidance")

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        st.markdown("""
**United States**
- **[NSA CNSA 2.0](https://media.defense.gov/2022/Sep/07/2003071836/-1/-1/0/CSI_CNSA_2.0_FAQ_.PDF)** (Sep 2022): mandates migration to PQC for national security systems by 2033.
  NSA explicitly recommends against procuring new QKD for government use pending further study.
- **[CISA Post-Quantum Cryptography Initiative](https://www.cisa.gov/topics/risk-management/quantum)**: inventory and prioritisation
  guidance for critical infrastructure, including the
  [Quantum-Readiness Migration factsheet](https://www.cisa.gov/resources-tools/resources/quantum-readiness-migration-post-quantum-cryptography).
- **[OMB M-23-02](https://www.whitehouse.gov/wp-content/uploads/2022/11/M-23-02-M-Memo-on-Migrating-to-Post-Quantum-Cryptography.pdf)** (Nov 2022): requires federal agencies to inventory cryptographic systems and designate a migration lead.
- **SEC**: no specific PQC rule yet, but cybersecurity disclosure rules (2023) implicitly cover
  material quantum risks.

**European Union**
- **[ENISA Post-Quantum Cryptography: Current State and Quantum Mitigation](https://www.enisa.europa.eu/publications/post-quantum-cryptography-current-state-and-quantum-mitigation)**
  (2021, updated 2022): recommends hybrid (classical + PQC) as the transition approach.
  See also: [PQC Integration Study](https://www.enisa.europa.eu/publications/post-quantum-cryptography-integration-study).
- **ECB**: no dedicated PQC regulation; included in broader cyber resilience expectations (TIBER-EU).
- **DORA** (Digital Operational Resilience Act, effective Jan 2025): requires financial entities
  to manage ICT risk including emerging technology threats — quantum readiness will fall under scope.
""")

    with col_r2:
        st.markdown("""
**United Kingdom**
- **[NCSC: Preparing for Quantum-Safe Cryptography](https://www.ncsc.gov.uk/whitepaper/quantum-safe-cryptography)**:
  sets out the NCSC position and recommends beginning migration planning now; endorses NIST PQC standards.
  See also: [Next steps in preparing for PQC](https://www.ncsc.gov.uk/whitepaper/next-steps-preparing-for-post-quantum-cryptography)
  and [PQC migration timelines](https://www.ncsc.gov.uk/guidance/pqc-migration-timelines).
- **Bank of England / PRA**: no specific QKD/PQC guidance yet; watch for CBEST and cyber stress
  testing updates.
- **FCA**: cyber and operational resilience rules require firms to identify and manage technology
  risks including quantum threats.

**Industry bodies**
- **SWIFT**: quantum-readiness working group; expects PQC to be incorporated into SWIFT standards
  as NIST standards mature.
- **[ETSI QKD Industry Specification Group](https://www.etsi.org/technologies/quantum-key-distribution)**:
  produces interoperability specs including
  [GS QKD 004](https://www.etsi.org/deliver/etsi_gs/QKD/001_099/004/02.01.01_60/gs_qkd004v020101p.pdf)
  (application interface) for QKD network integration.
- **ISO/IEC JTC 1/SC 27**: developing international PQC standards (ISO/IEC 14888-x family) aligned
  with NIST output.
- **BIS / CPMI**: no dedicated quantum guidance; systemic risk from quantum threats to payment
  infrastructure is an area of growing attention.
""")

    # ── Section 6: Migration roadmap ──────────────────────────────────────────
    st.header("6. Suggested Migration Roadmap")

    st.markdown("""
A quantum cryptography migration is a multi-year programme. The following phased structure is
consistent with guidance from NCSC, CISA, and NIST.
""")

    roadmap = pd.DataFrame({
        "Phase":    ["1 — Inventory", "2 — Prioritise", "3 — Pilot", "4 — Migrate", "5 — Operate"],
        "Horizon":  ["Now – 12 months", "6 – 18 months", "12 – 30 months", "2 – 5 years", "Ongoing"],
        "Activities": [
            "Catalogue all cryptographic assets: algorithms, key lengths, protocols, data flows, HSMs, certificates. Identify where RSA/ECC is used.",
            "Classify data by sensitivity and retention period. Apply Mosca's theorem. Identify highest-risk assets (long-lived signatures, archival data, inter-DC links).",
            "Deploy hybrid TLS (X25519 + ML-KEM) on a non-critical perimeter. Evaluate ML-DSA for code signing. Assess HSM vendor timelines.",
            "Systematic rollout of PQC across TLS, certificate infrastructure, signing systems, and HSMs. Update key management procedures.",
            "Monitor NIST for algorithm updates. Maintain crypto-agility (ability to swap algorithms without re-architecting). Track QKD developments for high-value links.",
        ],
    })
    st.dataframe(roadmap, use_container_width=True, hide_index=True)

    st.info(
        "**Crypto-agility** — designing systems so that the cryptographic algorithm is a "
        "configurable parameter rather than a hardcoded assumption — is the single most valuable "
        "architectural investment a financial institution can make today. It makes the migration "
        "from classical to PQC, and any future algorithm transitions, significantly cheaper."
    )

    st.divider()
    st.markdown(
        "<small>Sources: "
        "[NIST FIPS 203](https://csrc.nist.gov/pubs/fips/203/final), "
        "[FIPS 204](https://csrc.nist.gov/pubs/fips/204/final), "
        "[FIPS 205](https://csrc.nist.gov/pubs/fips/205/final) (Aug 2024) · "
        "[NSA CNSA 2.0 FAQ](https://media.defense.gov/2022/Sep/07/2003071836/-1/-1/0/CSI_CNSA_2.0_FAQ_.PDF) (Sep 2022) · "
        "[NCSC Quantum-Safe Cryptography](https://www.ncsc.gov.uk/whitepaper/quantum-safe-cryptography) · "
        "[ENISA PQC Report](https://www.enisa.europa.eu/publications/post-quantum-cryptography-current-state-and-quantum-mitigation) · "
        "[CISA PQC Initiative](https://www.cisa.gov/topics/risk-management/quantum) · "
        "[OMB M-23-02](https://www.whitehouse.gov/wp-content/uploads/2022/11/M-23-02-M-Memo-on-Migrating-to-Post-Quantum-Cryptography.pdf) · "
        "[ETSI QKD](https://www.etsi.org/technologies/quantum-key-distribution) · "
        "Mosca (2018) 'Cybersecurity in an era with quantum computers'. "
        "This page is for educational purposes and does not constitute regulatory or legal advice.</small>",
        unsafe_allow_html=True,
    )
