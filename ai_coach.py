import streamlit as st
import requests
import datetime
import json
import re
import os

# ── Phase 3: RAG System ───────────────────────────────────────────────────────
def get_rag_context(query, n_results=3):
    """Search the ChromaDB knowledge base for relevant content."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        if not os.path.exists("./knowledge_base"):
            return ""
        client = chromadb.PersistentClient(path="./knowledge_base")
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        collection = client.get_collection(
            name="student_knowledge",
            embedding_function=ef
        )
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count())
        )
        if results and results["documents"] and results["documents"][0]:
            context = "\n\n---\n\n".join(results["documents"][0])
            topics  = [m["topic"] for m in results["metadatas"][0]]
            return f"[Retrieved knowledge on: {', '.join(topics)}]\n\n{context}"
        return ""
    except Exception:
        return ""

RAG_ENABLED = os.path.exists("./knowledge_base")

# ── Claude API call with RAG ──────────────────────────────────────────────────
def get_claude_response(messages, student_context=""):
    """Call Claude API with RAG-enhanced context."""
    try:
        user_msg  = messages[-1]["content"] if messages else ""
        rag_ctx   = get_rag_context(user_msg) if RAG_ENABLED else ""
        rag_block = f"\n\nRelevant knowledge from knowledge base:\n{rag_ctx}" if rag_ctx else ""

        system_prompt = f"""You are an expert AI Academic Coach embedded inside a Student Performance Predictor app.
You are warm, encouraging, highly knowledgeable, and give DETAILED, PRACTICAL advice.

Student context:
{student_context}
{rag_block}

Rules:
- Give detailed, personalized advice based on the student's actual data
- For subject questions (Maths, Physics, Chemistry, CS etc.) give actual formulas, steps, and examples
- For study strategies give science-backed, actionable techniques
- Always be specific — never give generic one-line answers
- Format with numbered steps or bullet points
- Address student by name if available
- End with encouragement
- Aim for 150-300 words per response"""

        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": messages
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            return smart_fallback(user_msg, student_context)

    except Exception:
        user_msg = messages[-1]["content"] if messages else ""
        return smart_fallback(user_msg, student_context)


# ── Phase 2 + 3: Smart subject-aware fallback ─────────────────────────────────
def smart_fallback(user_msg, student_context=""):
    """Detailed fallback covering 20+ subjects when API unavailable."""
    msg  = user_msg.lower()
    name = ""
    for line in student_context.split('\n'):
        if "Student Name:" in line:
            name = line.replace("Student Name:", "").strip()
            break
    hi = f"**{name}!** " if name and name != "Student" else ""

    # ── RAG fallback: if knowledge base exists, search it ────────────────────
    rag_ctx = get_rag_context(user_msg, n_results=2) if RAG_ENABLED else ""
    if rag_ctx and len(rag_ctx) > 100:
        return f"""📚 {hi}Here's what I found in the knowledge base:\n\n{rag_ctx[:1500]}\n\n
💡 **Quick Study Tip:** Read this thoroughly, then close it and try to recall the key points from memory (active recall). This is 50% more effective than re-reading!

You've got this! 💪"""

    # ── MATHEMATICS ─────────────────────────────────────────────────────────
    if "binomial" in msg:
        return f"""📐 {hi}**Binomial Theorem — Complete Guide!**

**Core Formula:** (a+b)ⁿ = Σ ⁿCr × aⁿ⁻ʳ × bʳ

**Most Important: General Term**
T(r+1) = ⁿCr × aⁿ⁻ʳ × bʳ

**5 Things to Master:**
1. **Middle Term:** Even n → one middle term T(n/2+1). Odd n → two terms
2. **Constant term:** Set power of x = 0, solve for r
3. **Coefficient of xᵏ:** Set power = k, solve for r
4. **Sum of coefficients:** Put x=1 → answer is 2ⁿ
5. **Greatest term:** Use |T(r+1)/Tr| ≥ 1 to find r

**3-Day Plan:**
- Day 1: General term + 15 practice problems
- Day 2: Middle term, constant term, specific coefficient (15 problems)
- Day 3: Previous year questions only

**Common Mistakes:** Forgetting ⁿCr, wrong sign in (a-b)ⁿ

Master the general term first — 80% of exam questions use it! 🎯"""

    if any(x in msg for x in ["p and c", "p&c", "permutation", "combination", "pnc"]):
        return f"""🔢 {hi}**Permutations & Combinations — Full Guide!**

**Golden Rule:**
- Order MATTERS → Permutation: nPr = n!/(n-r)!
- Order DOESN'T matter → Combination: nCr = n!/(r!(n-r)!)

**Key Tricks:**
1. **Items always together:** Treat as one block → (n-1)! × internal arrangements
2. **Items never together:** Total − (items together)
3. **Circular arrangement:** (n-1)! ways
4. **Identical items in boxes:** Stars & Bars = (n+r-1)C(r-1)

**Solving Strategy:**
Step 1: Identify if it's arrangement (P) or selection (C)
Step 2: Check for restrictions — handle them first
Step 3: Apply multiplication rule (AND = ×) or addition rule (OR = +)

**4-Day Plan:**
- Day 1: Basic nPr and nCr (20 problems)
- Day 2: Restrictions (together / not together)
- Day 3: Circular + distributions
- Day 4: Mixed previous year questions

**Tip:** "At least one" = Total − None. Always! 💪"""

    if any(x in msg for x in ["calculus", "differentiat", "integrat", "limit"]):
        return f"""📈 {hi}**Calculus — Key Concepts & Formulas!**

**Differentiation Formulas (Must Memorize):**
- d/dx(xⁿ) = nxⁿ⁻¹
- d/dx(eˣ) = eˣ, d/dx(aˣ) = aˣ ln a
- d/dx(ln x) = 1/x
- d/dx(sin x) = cos x, d/dx(cos x) = −sin x
- Chain rule: d/dx[f(g(x))] = f'(g(x)) · g'(x)
- Product rule: (uv)' = u'v + uv'

**Integration (Reverse of Differentiation):**
- ∫xⁿ dx = xⁿ⁺¹/(n+1) + C
- ∫eˣ dx = eˣ + C, ∫(1/x)dx = ln|x| + C
- Integration by parts: ∫u dv = uv − ∫v du (ILATE rule)

**Maxima/Minima:**
1. Find f'(x) = 0 → critical points
2. f''(x) > 0 → minimum, f''(x) < 0 → maximum

**L'Hopital's Rule:** For 0/0 or ∞/∞ forms → differentiate numerator & denominator separately

Focus on chain rule and integration by parts — they appear every exam! 🎯"""

    if any(x in msg for x in ["trigonometry", "trig", "sin", "cos", "tan"]):
        return f"""📐 {hi}**Trigonometry — Essential Formulas!**

**Pythagorean Identities (Foundation):**
- sin²x + cos²x = 1
- 1 + tan²x = sec²x
- 1 + cot²x = cosec²x

**Double Angle (Very Frequently Asked):**
- sin 2x = 2 sin x cos x
- cos 2x = cos²x − sin²x = 1−2sin²x = 2cos²x−1
- tan 2x = 2tan x/(1−tan²x)

**Sum Formulas:**
- sin(A±B) = sinA cosB ± cosA sinB
- cos(A±B) = cosA cosB ∓ sinA sinB

**Study Strategy:**
1. Memorize only the 3 Pythagorean identities
2. Derive double angle from sin(A+A)
3. Never memorize all formulas — derive them!
4. Practice 10 identity proofs daily

**General Solutions:** sinx=0→x=nπ | cosx=0→x=(2n+1)π/2 | tanx=0→x=nπ 🌟"""

    if any(x in msg for x in ["matrices", "determinant", "matrix"]):
        return f"""🔢 {hi}**Matrices & Determinants — Complete Guide!**

**Determinant of 2×2:** |a b; c d| = ad − bc

**Properties to Know:**
- det(AB) = det(A)·det(B)
- det(Aᵀ) = det(A)
- Inverse exists only if det(A) ≠ 0
- A⁻¹ = adj(A)/det(A)

**Finding Inverse (3×3):**
1. Find cofactor matrix
2. Transpose it → Adjugate
3. Divide by det(A)

**Solving Linear Equations:**
- Matrix method: AX = B → X = A⁻¹B
- Cramer's rule: xᵢ = det(Aᵢ)/det(A)
- Row reduction: Most reliable method

**Eigenvalues:** Solve det(A − λI) = 0
- Sum of eigenvalues = Trace(A)
- Product of eigenvalues = det(A)

Practice finding inverse of 3×3 — it appears in almost every exam! 💪"""

    # ── PHYSICS ─────────────────────────────────────────────────────────────
    if any(x in msg for x in ["physics", "mechanics", "newton", "force", "motion"]):
        return f"""⚡ {hi}**Physics — Mechanics & Newton's Laws!**

**Newton's Laws:**
1. Object stays at rest/motion unless external force acts (Inertia)
2. F = ma (Force = mass × acceleration)
3. Every action has equal & opposite reaction

**Equations of Motion (Uniform Acceleration):**
- v = u + at
- s = ut + ½at²
- v² = u² + 2as

**Projectile Motion:**
- Horizontal velocity: constant (vₓ = u cosθ)
- Vertical: free fall (vᵧ = u sinθ − gt)
- Range: R = u²sin(2θ)/g (max at θ=45°)
- Time of flight: T = 2u sinθ/g
- Max height: H = u²sin²θ/2g

**Work-Energy Theorem:** Work done = Change in KE = ½mv² − ½mu²

**Conservation Laws:**
- Momentum: p = mv (conserved in absence of external force)
- Energy: Total mechanical energy = KE + PE = constant

Start with equations of motion — they're the base for everything! 🚀"""

    if any(x in msg for x in ["electricity", "current", "circuit", "ohm", "resistor"]):
        return f"""⚡ {hi}**Electricity & Circuits — Key Concepts!**

**Ohm's Law:** V = IR
- Current I = V/R (Amperes)
- Power P = VI = I²R = V²/R (Watts)

**Resistors:**
- Series: R_total = R1 + R2 + R3 (same current)
- Parallel: 1/R = 1/R1 + 1/R2 + 1/R3 (same voltage)

**Kirchhoff's Laws:**
- KCL: Sum of currents at junction = 0
- KVL: Sum of voltages in any closed loop = 0

**Capacitors:**
- Series: 1/C = 1/C1 + 1/C2 (opposite of resistors!)
- Parallel: C = C1 + C2
- Energy: E = ½CV²

**Electromagnetic Induction:**
- Faraday: EMF = −dΦ/dt
- Lenz's law: Induced current opposes change that caused it
- Transformer: V1/V2 = N1/N2

**Problem-Solving Steps:**
1. Redraw circuit, identify series/parallel combinations
2. Find equivalent resistance
3. Apply Ohm's law for each component

Master KVL & KCL — they solve any circuit! 💡"""

    if any(x in msg for x in ["thermodynamics", "heat", "temperature", "entropy"]):
        return f"""🌡️ {hi}**Thermodynamics — Complete Guide!**

**The 4 Laws:**
0. If A=B and B=C in thermal equilibrium → A=C (basis of temperature)
1. ΔU = Q − W (Energy conservation)
2. Entropy always increases in isolated system
3. Entropy → 0 as T → 0K

**Processes:**
| Process | Constant | Special |
|---------|----------|---------|
| Isothermal | T | ΔU=0, Q=W |
| Adiabatic | Q=0 | ΔU=−W, PVᵞ=const |
| Isobaric | P | Q=nCpΔT |
| Isochoric | V | W=0, Q=ΔU |

**Ideal Gas Law:** PV = nRT
- Boyle's: P1V1 = P2V2 (constant T)
- Charles's: V1/T1 = V2/T2 (constant P)

**Carnot Engine:** η = 1 − T_cold/T_hot (maximum possible efficiency)

**Specific Heat:** Cp − Cv = R (for ideal gas) and Cp > Cv always

Focus on process identification first — it determines which formula to use! 🎯"""

    # ── CHEMISTRY ─────────────────────────────────────────────────────────
    if any(x in msg for x in ["chemistry", "organic", "reaction", "compound", "bond"]):
        return f"""🧪 {hi}**Chemistry — Organic Reactions Guide!**

**Reaction Types (Master These):**

**1. Substitution:**
- SN1: Tertiary carbon, polar protic solvent, 2-step, carbocation
- SN2: Primary carbon, polar aprotic solvent, 1-step, inversion

**2. Addition to Alkenes:**
- Markovnikov's rule: H adds to carbon with MORE hydrogens
- Anti-Markovnikov: Peroxide present → reverse
- Electrophilic addition: HX, H2O, halogen (Cl2, Br2)

**3. Elimination:**
- E1: 2-step, tertiary, Zaitsev product (more substituted alkene)
- E2: 1-step, anti-periplanar, strong base needed

**4. Benzene (EAS):**
- Nitration: HNO3 + H2SO4
- Halogenation: X2 + Lewis acid
- Friedel-Crafts: Alkyl/acyl + Lewis acid

**IUPAC Naming Steps:**
1. Find longest carbon chain
2. Give lowest numbers to substituents
3. Alphabetical order for multiple substituents
4. Functional group suffix: -ol, -al, -one, -oic acid

Make a reaction map — connect all reactions visually! 🗺️"""

    if any(x in msg for x in ["physical chemistry", "mole", "equilibrium", "kinetics", "electrochemistry"]):
        return f"""⚗️ {hi}**Physical Chemistry — Key Concepts!**

**Mole Concept:**
- 1 mole = 6.022×10²³ particles
- Molarity (M) = moles/litre
- Molality (m) = moles/kg solvent

**Chemical Equilibrium:**
- Kc = [P]p[Q]q / [A]a[B]b (products over reactants)
- Le Chatelier: System opposes any disturbance
- Temperature↑ → favors endothermic direction

**Electrochemistry:**
- E°cell = E°cathode − E°anode
- Nernst: E = E° − (0.0592/n)log Q at 25°C
- Faraday: Mass = (M/nF) × charge

**Chemical Kinetics:**
- Rate = k[A]^m [B]^n
- First order: t½ = 0.693/k (constant half-life)
- Zero order: t½ = [A]₀/2k

**Thermochemistry:**
- Hess's law: ΔH is path independent
- Bond enthalpy: ΔH = Bonds broken − Bonds formed

Practice Kc and Kp interconversion — it appears every year! 🎯"""

    # ── COMPUTER SCIENCE ─────────────────────────────────────────────────
    if any(x in msg for x in ["data structure", "algorithm", "dsa", "array", "linked list", "tree", "graph", "sorting"]):
        return f"""💻 {hi}**Data Structures & Algorithms — Complete Guide!**

**Time Complexity (Memorize This Order):**
O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2ⁿ) < O(n!)

**Data Structures Quick Reference:**
| Structure | Access | Search | Insert | Delete |
|-----------|--------|--------|--------|--------|
| Array | O(1) | O(n) | O(n) | O(n) |
| Linked List | O(n) | O(n) | O(1) | O(1) |
| BST (balanced) | O(log n) | O(log n) | O(log n) | O(log n) |
| Hash Table | O(1) | O(1) | O(1) | O(1) |
| Heap | O(1) min/max | O(n) | O(log n) | O(log n) |

**Sorting Algorithms:**
- Bubble, Selection, Insertion: O(n²) — avoid for large data
- Merge Sort: O(n log n) — stable, guaranteed
- Quick Sort: O(n log n) avg, O(n²) worst — fastest in practice
- Heap Sort: O(n log n) — in-place

**Graph Algorithms:**
- BFS: Queue, O(V+E) — shortest path in unweighted
- DFS: Stack/recursion, O(V+E) — cycle detection
- Dijkstra: O(V² or E log V) — shortest path weighted

**Dynamic Programming Checklist:**
1. Overlapping subproblems? ✓
2. Optimal substructure? ✓
3. Memoize or tabulate!

Start with arrays and recursion — everything else builds on them! 🚀"""

    if any(x in msg for x in ["dbms", "database", "sql", "query", "normalization", "transaction"]):
        return f"""🗄️ {hi}**DBMS — Complete Study Guide!**

**ACID Properties (Very Important):**
- **A**tomicity: All or nothing
- **C**onsistency: DB stays valid
- **I**solation: Transactions don't interfere
- **D**urability: Committed changes are permanent

**Normalization:**
- 1NF: Atomic values, no repeating groups
- 2NF: No partial dependency (all non-key attributes depend on WHOLE primary key)
- 3NF: No transitive dependency
- BCNF: Every determinant is a candidate key

**SQL Must-Know Queries:**
```sql
SELECT * FROM table WHERE condition;
SELECT a, COUNT(*) FROM t GROUP BY a HAVING COUNT(*)>1;
SELECT * FROM t1 INNER JOIN t2 ON t1.id = t2.id;
```

**Joins:**
- INNER JOIN: Only matching rows
- LEFT JOIN: All left + matching right (NULL if no match)
- FULL OUTER JOIN: All rows from both tables

**Keys:** Primary (unique identifier) → Foreign (references PK) → Candidate (could be PK) → Super (superset of candidate)

**Indexing:** B-tree index speeds up SELECT, slows INSERT/UPDATE/DELETE

Practice writing complex SQL queries daily — normalization + SQL = 70% of exams! 💪"""

    if any(x in msg for x in ["operating system", "os", "process", "thread", "deadlock", "scheduling", "memory"]):
        return f"""⚙️ {hi}**Operating Systems — Key Concepts!**

**Process vs Thread:**
- Process: Independent program, own memory space
- Thread: Lightweight, shares process memory
- Context switch between processes is expensive

**CPU Scheduling Algorithms:**
- FCFS: Simple, convoy effect (long jobs block short ones)
- SJF: Optimal average wait time, needs future knowledge
- Round Robin: Fair, time quantum determines responsiveness
- Priority: Starvation possible, solve with aging

**Deadlock — 4 Conditions (ALL must hold):**
1. Mutual exclusion
2. Hold and wait
3. No preemption
4. Circular wait

**Prevention:** Eliminate any ONE condition
**Detection:** Resource allocation graph
**Recovery:** Process termination or resource preemption

**Memory Management:**
- Paging: Fixed size, no external fragmentation
- Segmentation: Variable size, matches logical view
- Virtual memory: Use disk as extended RAM

**Page Replacement (Least Faults):**
Optimal > LRU > Clock > FIFO

**Banker's Algorithm:** Deadlock avoidance — check if safe state exists before granting resources

Deadlock and scheduling are asked EVERY semester! 🎯"""

    if any(x in msg for x in ["machine learning", "ml", "deep learning", "neural", "ai", "classification", "regression"]):
        return f"""🤖 {hi}**Machine Learning — Core Concepts!**

**Types of Learning:**
- Supervised: Labeled data → Classification or Regression
- Unsupervised: No labels → Clustering, Dimensionality reduction
- Reinforcement: Agent + Environment + Reward

**Bias-Variance Tradeoff:**
- High bias = Underfitting (model too simple)
- High variance = Overfitting (model memorizes training data)
- Solution: Cross-validation, regularization, more data

**Common Algorithms:**
| Algorithm | Type | When to Use |
|-----------|------|-------------|
| Linear Regression | Regression | Continuous output, linear relationship |
| Logistic Regression | Classification | Binary output |
| Decision Tree | Both | Interpretable, non-linear |
| Random Forest | Both | Reduces overfitting |
| SVM | Classification | High-dimensional data |
| K-Means | Clustering | Unknown structure in data |

**Evaluation Metrics:**
- Classification: Accuracy, Precision, Recall, F1, ROC-AUC
- Regression: MSE, RMSE, MAE, R²
- Use F1 when classes are imbalanced!

**Gradient Descent:**
- Update: w = w − α × ∂L/∂w
- α = learning rate (too high = diverge, too low = slow)

Your own project uses Logistic Regression — you already understand ML! 🌟"""

    if any(x in msg for x in ["python", "programming", "code", "function", "class", "oop"]):
        return f"""🐍 {hi}**Python Programming — Complete Guide!**

**Data Structures:**
- List: Mutable, ordered → `[1, 2, 3]`
- Tuple: Immutable, ordered → `(1, 2, 3)` (use for fixed data)
- Dictionary: Key-value pairs → `{{"key": "value"}}`
- Set: Unique elements → `{{1, 2, 3}}`

**List Comprehension (Write Pythonic Code):**
```python
squares = [x**2 for x in range(10) if x % 2 == 0]
```

**OOP Concepts:**
```python
class Student:
    def __init__(self, name, grade):
        self.name  = name   # instance variable
        self.grade = grade
    def is_passing(self):
        return self.grade >= 50
```

**Key OOP Principles:**
- Encapsulation: Bundle data + methods
- Inheritance: Child class inherits parent
- Polymorphism: Same method, different behavior
- Abstraction: Hide implementation details

**Error Handling:**
```python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {{e}}")
finally:
    print("Always runs")
```

**File I/O:**
```python
with open("file.txt", "r") as f:  # auto-closes
    content = f.read()
```

Practice OOP daily — it's asked in every Python interview! 💻"""

    if any(x in msg for x in ["network", "tcp", "ip", "http", "osi", "protocol"]):
        return f"""🌐 {hi}**Computer Networks — Key Concepts!**

**OSI Model (All People Seem To Need Data Processing):**
7. Application (HTTP, FTP, SMTP, DNS)
6. Presentation (Encryption, Compression)
5. Session (Session management)
4. Transport (TCP, UDP)
3. Network (IP, Routing)
2. Data Link (MAC, Switches)
1. Physical (Cables, Bits)

**TCP vs UDP:**
| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Yes (3-way handshake) | No |
| Reliable | Yes (ACK, retransmit) | No |
| Speed | Slower | Faster |
| Use case | HTTP, Email, FTP | Video, DNS, Gaming |

**TCP 3-Way Handshake:** SYN → SYN-ACK → ACK

**IP Addressing:**
- IPv4: 32 bits, dotted decimal (192.168.1.1)
- Subnet: /24 = 255.255.255.0 = 256 addresses
- Private ranges: 10.x.x.x, 172.16-31.x.x, 192.168.x.x

**Important Port Numbers:**
HTTP=80, HTTPS=443, SSH=22, FTP=21, SMTP=25, DNS=53, DHCP=67

**Routing:** RIP (distance vector) → OSPF (link state) → BGP (path vector, Internet backbone)

OSI layers + TCP vs UDP = 60% of networking exams! 🎯"""

    if any(x in msg for x in ["accounting", "account", "balance sheet", "journal", "ledger", "debit", "credit"]):
        return f"""📊 {hi}**Accounting — Complete Guide!**

**Fundamental Equation:**
Assets = Liabilities + Owner's Equity

**Double Entry System Rules:**
| Account Type | Debit | Credit |
|-------------|-------|--------|
| Assets | Increase | Decrease |
| Liabilities | Decrease | Increase |
| Equity | Decrease | Increase |
| Revenue | Decrease | Increase |
| Expenses | Increase | Decrease |

**Journal Entry Format:**
```
Date | Dr Account     | Amount
     |   Cr Account   |        Amount
     | Narration...
```

**Financial Statements:**
1. **Income Statement:** Revenue − Expenses = Net Profit
2. **Balance Sheet:** Assets = Liabilities + Equity (at a point in time)
3. **Cash Flow:** Operating + Investing + Financing activities

**Depreciation:**
- Straight Line: (Cost − Salvage)/Useful Life (equal every year)
- Written Down Value: Previous WDV × Rate% (decreasing every year)

**Ratio Analysis:**
- Current Ratio = Current Assets / Current Liabilities (>2 = healthy)
- Gross Profit Ratio = Gross Profit / Net Sales × 100
- Return on Equity = Net Profit / Shareholders' Equity × 100

Master journal entries first — they're the foundation of everything! 📚"""

    # ── STUDY STRATEGY ───────────────────────────────────────────────────
    if any(x in msg for x in ["study tips", "how to study", "study strategy", "study technique"]):
        return f"""📚 {hi}**Science-Backed Study Techniques!**

**Top 5 Most Effective Methods:**

**1. Active Recall (Most Powerful)**
Close your book → try to remember everything → check.
50% more effective than re-reading. Use flashcards or self-testing.

**2. Spaced Repetition**
Review after: 1 day → 3 days → 7 days → 21 days.
Reduces forgetting by 80%. Use Anki app to automate.

**3. Pomodoro Technique**
25 min study → 5 min break (repeat 4x) → 20 min break.
Prevents mental fatigue. Phone in ANOTHER ROOM during each session.

**4. Feynman Technique**
Explain the topic as if teaching a 10-year-old.
If you can't explain it simply → you don't understand it yet.

**5. Interleaving**
Mix subjects every 45-60 min instead of studying one subject for 3 hours.
Increases retention by 43% vs blocked practice.

**Avoid These Mistakes:**
❌ Re-reading (feels productive, isn't)
❌ Highlighting (passive, not active)
❌ Studying with phone nearby
❌ Cramming night before

**Best Time to Study:** Morning for hardest subjects (brain freshest). Evening for revision.

Implement just ONE of these techniques this week and see the difference! 🌟"""

    if any(x in msg for x in ["timetable", "time table", "schedule", "plan", "routine"]):
        return f"""📅 {hi}**Personalized Study Timetable!**

**Daily Schedule (Exam Preparation Mode):**
```
6:00 AM  → Wake up + 20 min exercise
6:30 AM  → Hardest subject (fresh brain = best focus)
8:30 AM  → Breakfast + college travel
4:00 PM  → Return + 30 min rest (NO screens)
4:30 PM  → Second most important subject
6:30 PM  → Previous year questions / practice
8:00 PM  → Dinner + break
9:00 PM  → Formula revision + weak topics
10:00 PM → SLEEP (8 hours = non-negotiable)
```

**Weekly Pattern:**
- Mon-Tue: New topics (learn + practice)
- Wed-Thu: Previous year questions
- Friday: Full mock test (exam conditions)
- Saturday: Analyze mistakes + fix weak areas
- Sunday: Light revision + plan next week

**Key Rules:**
✅ Same study time every day → builds automatic habit
✅ Rotate subjects every 45-60 min (interleaving)
✅ No phone in study area
✅ Track daily — use the streak feature in this app!
✅ Adjust based on what works for YOU

**Most Important:** Start tomorrow. Not Monday. Not next month. Tomorrow. 🚀"""

    if any(x in msg for x in ["stress", "anxious", "overwhelmed", "scared", "worried"]):
        return f"""💙 {hi}**Managing Exam Stress — Science-Based Solutions!**

**Immediate Relief (Do This Right Now):**
**4-7-8 Breathing:**
Inhale for 4 counts → Hold for 7 → Exhale for 8.
Repeat 4 times. Activates parasympathetic nervous system in 60 seconds.

**5-4-3-2-1 Grounding:**
Name: 5 things you see → 4 you touch → 3 you hear → 2 you smell → 1 you taste.
Stops anxiety spiraling immediately.

**Long-Term Stress Management:**
- **Exercise:** 20 min walk reduces cortisol by 26% + boosts memory
- **Sleep:** Stress and sleep deprivation create a vicious cycle. Sleep FIRST.
- **Limit caffeine:** More than 2 cups increases anxiety. Switch to water after 2pm.
- **Break tasks down:** "Study Data Structures" → "Understand linked lists (25 min)"

**Reframe Your Thinking:**
Stress = You care + You believe you can do better.
That caring is your STRENGTH, not a weakness.

**Remember:** One exam does not define your intelligence, worth, or future. Your effort RIGHT NOW is what matters.

You're doing better than you think. Take a breath. Start small. 🌟"""

    if any(x in msg for x in ["motivat", "inspire", "give up", "can't", "hopeless"]):
        return f"""🔥 {hi}**You've Got This — Here's Why!**

**The Science of Success:**
Stanford research shows students who believe they can improve (growth mindset) consistently outperform those who think ability is fixed — regardless of starting intelligence.

Your effort RIGHT NOW is literally rewiring your brain. Every hour you study creates new neural connections.

**What Successful Students Do Differently:**
They don't study MORE — they study SMARTER.
They take proper breaks. They ask for help. They fail and try again.
They're not superhuman — they're CONSISTENT.

**Your Current Reality:**
Look at your prediction score in this app.
Now imagine adjusting your study hours from {"{study_hours}" if "study_hours" in student_context else "current"} to 6+ hours.
The model will show you PASS. That's not magic — that's the MATH of effort.

**Action Plan — Start in the Next 5 Minutes:**
1. Close all social media tabs/apps
2. Open your textbook to ONE topic
3. Set a 25-minute timer
4. Just START — motivation follows action

**The Key Insight:**
The fact that you're using this app, asking for help, trying to improve — that already puts you ahead of most people.

Don't quit on a bad day. Every expert was once exactly where you are. 💪

*"It always seems impossible until it's done."* — Nelson Mandela 🌟"""

    if any(x in msg for x in ["exam", "prepare", "preparation", "revision"]):
        return f"""📝 {hi}**Complete Exam Preparation Strategy!**

**2 Weeks Before Exam:**
- Create a topic checklist for EVERY chapter
- Identify weak areas → prioritize them first
- Study 4-5 hours daily using Pomodoro technique
- Make one-page summary notes for each topic

**1 Week Before:**
- Solve previous year papers (under TIMED conditions)
- Review weak topics every morning
- No new topics — only consolidation
- Sleep 8 hours every night (memory consolidates during sleep)

**3 Days Before:**
- Only revision — absolutely no new topics
- Solve 2 full mock papers daily
- Review formula sheets and quick notes
- Check exam pattern, marking scheme, important topics

**Day Before:**
- Light revision (2-3 hours max)
- Organize everything (stationery, hall ticket, ID)
- Sleep by 10pm — this is MORE important than studying

**Exam Day:**
- Good breakfast (glucose fuels the brain)
- Arrive 15 minutes early
- Read ALL questions first, then answer easiest first
- Show ALL working steps (partial marks save grades!)
- Manage time: don't spend >3 min on any single question

You're more prepared than you think. Trust your preparation! 🎯"""

    # ── Default intelligent response ─────────────────────────────────────
    return f"""🤖 {hi}**I'm your AI Academic Coach!**

I can give detailed, personalized help on:

📐 **Mathematics:** Binomial Theorem, P&C, Calculus, Trigonometry, Matrices
⚡ **Physics:** Mechanics, Electricity, Thermodynamics, Optics
🧪 **Chemistry:** Organic reactions, Physical Chemistry, Electrochemistry
💻 **Computer Science:** DSA, DBMS, OS, Networks, Machine Learning, Python
📊 **Accounting:** Journal entries, Financial statements, Ratio analysis
📚 **Study Skills:** Timetables, techniques, exam prep, focus, stress management

**Try asking me:**
- *"Explain Binomial Theorem with examples"*
- *"How do I study for DBMS exam in 3 days?"*
- *"Create a weekly timetable for engineering exams"*
- *"I'm stressed about tomorrow's Physics exam"*
- *"What's the difference between TCP and UDP?"*

The more specific your question, the more detailed and useful my answer! 🌟"""


# ── Chatbot UI renderer ───────────────────────────────────────────────────────
def render_ai_chatbot(profile, study_hours, attendance, prev_score,
                      sleep_hours, assignments, confidence, pred_result):
    """Render the complete AI chatbot interface."""

    student_context = f"""Student Name: {profile.get('name','Student')}
College: {profile.get('college','N/A')} | Class: {profile.get('class_name','N/A')}
Study Hours/Day: {study_hours} | Attendance: {attendance:.0f}%
Previous Score: {prev_score:.0f}/100 | Sleep: {sleep_hours}h | Assignments: {assignments}/10
Prediction: {'PASS' if pred_result==1 else 'FAIL'} ({confidence:.1f}% confidence)
Weak areas: {', '.join([x for x,c in [('study hours',study_hours<5),('attendance',attendance<80),('assignments',assignments<8),('sleep',sleep_hours<7)] if c]) or 'None'}"""

    cL, cR = st.columns([1.2, 1], gap="large")

    with cL:
        # Header with RAG status
        rag_badge = "🟢 RAG Active" if RAG_ENABLED else "🟡 Smart Fallback"
        st.markdown(f"""<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;'>
            <div class='card-title'>🤖 AI Academic Coach</div>
            <div style='font-size:.72rem;color:{"#34d399" if RAG_ENABLED else "#fbbf24"};
                background:rgba(255,255,255,.05);padding:.2rem .7rem;border-radius:20px;
                border:1px solid {"rgba(52,211,153,.3)" if RAG_ENABLED else "rgba(251,191,36,.3)"};'>
                {rag_badge}
            </div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""<p style='color:#a09cc0;font-size:.85rem;margin-bottom:.8rem;'>
            Detailed answers on 20+ subjects · Knows your prediction is
            <strong style='color:{"#34d399" if pred_result==1 else "#f87171"};'>
            {"PASS" if pred_result==1 else "FAIL"}</strong> ({confidence:.0f}%)
            {"· <strong style='color:#34d399'>Knowledge base loaded ✅</strong>" if RAG_ENABLED else ""}
        </p>""", unsafe_allow_html=True)

        # Chat history
        if not st.session_state.chat_messages:
            name  = profile.get('name', 'Student')
            weak  = [x for x,c in [('study hours',study_hours<5),('attendance',attendance<80),
                                    ('assignments',assignments<8),('sleep',sleep_hours<7)] if c]
            w_str = f"Your main focus areas: <strong>{', '.join(weak)}</strong>." if weak else "Your stats look healthy!"
            st.markdown(f"""<div class='chat-bubble-bot'>
                👋 Hi <strong>{name}</strong>! I'm your AI Academic Coach.<br><br>
                📊 <strong>{'✅ PASS' if pred_result==1 else '❌ FAIL'}</strong> ({confidence:.0f}% confidence) ·
                📚 {study_hours}h/day · 🏫 {attendance:.0f}% · 📝 {prev_score:.0f}/100<br>
                {w_str}<br><br>
                I know <strong>Maths, Physics, Chemistry, CS, Accounts</strong> and more.<br>
                Ask me anything specific — I give detailed answers!<br><br>
                Try: <em>"Explain Binomial Theorem"</em> or <em>"Make my timetable"</em>
                <div class='chat-time'>AI Coach · now</div>
            </div>""", unsafe_allow_html=True)
        else:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(f"""<div style='display:flex;justify-content:flex-end;'>
                        <div class='chat-bubble-user'>{msg['content']}
                        <div class='chat-time' style='text-align:right;'>You · {msg['time']}</div></div>
                    </div>""", unsafe_allow_html=True)
                else:
                    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', msg['content'])
                    content = content.replace('\n', '<br>')
                    st.markdown(f"""<div class='chat-bubble-bot'>{content}
                        <div class='chat-time'>AI Coach · {msg['time']}</div>
                    </div>""", unsafe_allow_html=True)

        # Quick action buttons
        st.markdown("<div style='margin:.8rem 0 .4rem;font-size:.72rem;color:#6b5f8a;text-transform:uppercase;letter-spacing:.08em;'>⚡ Quick Questions</div>", unsafe_allow_html=True)
        qa1,qa2,qa3,qa4 = st.columns(4)
        qa5,qa6,qa7,qa8 = st.columns(4)
        qm = None
        if qa1.button("📐 Maths Help"):      qm = "Give me detailed help on the most important Maths topics for my exam with formulas and examples"
        if qa2.button("📅 My Timetable"):    qm = f"Create a detailed personalized weekly study timetable for me. I study {study_hours}h/day, attendance {attendance:.0f}%"
        if qa3.button("😰 Stress Relief"):   qm = "I'm feeling very stressed and overwhelmed about my exams. Give me detailed science-backed stress management advice"
        if qa4.button("💻 CS Concepts"):     qm = "Explain the most important Computer Science concepts I need to know for my engineering exams with examples"
        if qa5.button("⚡ Physics Guide"):   qm = "Give me a complete Physics study guide with the most important formulas and concepts"
        if qa6.button("🧪 Chemistry Tips"):  qm = "Give me detailed tips for studying Organic Chemistry and Physical Chemistry for exams"
        if qa7.button("💪 Motivate Me"):     qm = f"I'm feeling demotivated. My prediction is {'PASS' if pred_result==1 else 'FAIL'}. Give me detailed motivation with an action plan"
        if qa8.button("📝 Exam Strategy"):   qm = "Give me a complete, detailed exam preparation strategy with a day-by-day plan"

        # Input
        user_input = st.text_input(
            "💬 Ask about any subject or study problem...",
            key="chat_input_ai",
            placeholder="e.g. Explain Binomial Theorem with examples and exam tips"
        )
        s1, s2 = st.columns([3, 1])
        send_btn  = s1.button("📤 Send", use_container_width=True)
        clear_btn = s2.button("🗑️ Clear", use_container_width=True)

        if clear_btn:
            st.session_state.chat_messages = []
            st.rerun()

        final_msg = qm or (user_input if send_btn and user_input else None)

        if final_msg:
            now = datetime.datetime.now().strftime("%H:%M")
            st.session_state.chat_messages.append({"role":"user","content":final_msg,"time":now})
            api_messages = [{"role":"user" if m["role"]=="user" else "assistant",
                             "content":m["content"]}
                            for m in st.session_state.chat_messages]
            with st.spinner("🤖 Thinking..."):
                response = get_claude_response(api_messages, student_context)
            st.session_state.chat_messages.append({"role":"bot","content":response,"time":now})
            st.rerun()

    with cR:
        # Pomodoro
        st.markdown("<div class='card-title'>🍅 Pomodoro Timer</div>", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f"""<div style='text-align:center;padding:1rem;background:rgba(167,139,250,.06);
                border:2px solid rgba(167,139,250,.2);border-radius:20px;'>
                <div style='font-size:2rem;'>🍅</div>
                <div style='font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;color:#a78bfa;'>25:00</div>
                <div style='font-size:.72rem;color:#7c6fa0;'>Focus · Done: <strong style='color:#a78bfa;'>{st.session_state.pomodoro_count}</strong></div>
            </div>""", unsafe_allow_html=True)
        with p2:
            st.markdown(f"""<div style='text-align:center;padding:1rem;background:rgba(52,211,153,.06);
                border:2px solid rgba(52,211,153,.2);border-radius:20px;'>
                <div style='font-size:2rem;'>☕</div>
                <div style='font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;color:#34d399;'>5:00</div>
                <div style='font-size:.72rem;color:#7c6fa0;'>Break · Hrs: <strong style='color:#34d399;'>{st.session_state.pomodoro_count*0.42:.1f}h</strong></div>
            </div>""", unsafe_allow_html=True)
        if st.button("▶️ Start Focus Session", use_container_width=True):
            st.session_state.pomodoro_count += 1
            st.toast("🍅 25 min focus! No distractions!", icon="⏱️")

        # Exam Timetable
        st.markdown("<div style='height:.8rem'></div><div class='card-title'>📅 Exam Timetable</div>", unsafe_allow_html=True)
        with st.expander("➕ Add Exam", expanded=len(st.session_state.exams)==0):
            es  = st.text_input("📚 Subject", placeholder="e.g. Mathematics", key="ex_s_ai")
            ed  = st.date_input("📅 Date", min_value=datetime.date.today(), key="ex_d_ai")
            et  = st.time_input("⏰ Time", value=datetime.time(9,0), key="ex_t_ai")
            edf = st.select_slider("Difficulty",["Easy","Medium","Hard","Very Hard"],value="Medium",key="ex_df_ai")
            if st.button("✅ Add Exam", use_container_width=True) and es:
                days = (ed - datetime.date.today()).days
                hrs  = {"Easy":1,"Medium":2,"Hard":3,"Very Hard":4}[edf]
                st.session_state.exams.append({"subject":es,"date":str(ed),"time":str(et),
                                               "difficulty":edf,"days_left":days,"hrs_per_day":hrs})
                st.toast(f"✅ {es} added! {days} days to go!", icon="📅")
                st.rerun()

        if st.session_state.exams:
            for exam in sorted(st.session_state.exams, key=lambda x: x["date"]):
                d  = exam["days_left"]
                uc = "#f87171" if d<=3 else "#fbbf24" if d<=7 else "#34d399"
                ul = "🔴 URGENT" if d<=3 else "🟡 Soon" if d<=7 else "🟢 On Track"
                st.markdown(f"""<div class='exam-card'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div>
                            <div style='font-family:Syne,sans-serif;font-weight:700;color:#c4b5fd;'>📝 {exam['subject']}</div>
                            <div style='font-size:.75rem;color:#6b5f8a;'>📅 {exam['date']} · {exam['difficulty']} · {exam['hrs_per_day']}h/day</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;color:{uc};'>{d}d</div>
                            <div style='font-size:.72rem;color:{uc};'>{ul}</div>
                        </div>
                    </div></div>""", unsafe_allow_html=True)
            if st.button("🗑️ Clear Exams", use_container_width=True):
                st.session_state.exams = []
                st.rerun()

        # Smart Reminders
        st.markdown("<div style='height:.8rem'></div><div class='card-title'>🔔 Smart Reminders</div>", unsafe_allow_html=True)
        hr2  = datetime.datetime.now().hour
        rems = [("🌅 Morning!", "Start with 30-min review — brain is freshest!", "#fbbf24")] if hr2<9 else \
               [("📚 Study Time", "Perfect time for deep focus work!", "#34d399")]           if hr2<12 else \
               [("🍽️ Lunch Break", "Rest your brain — consolidation happens now!", "#60a5fa")] if hr2<14 else \
               [("⚡ Afternoon", "Do a Pomodoro before the afternoon slump!", "#a78bfa")]     if hr2<17 else \
               [("🌆 Evening", "Best time for revision and practice problems!", "#f472b6")]   if hr2<20 else \
               [("🌙 Wind Down", "Stop by 10pm — sleep builds memory!", "#60a5fa")]
        for e in [x for x in st.session_state.exams if x["days_left"]<=3]:
            rems.append((f"🔴 {e['subject']}!", f"Only {e['days_left']} day(s)! Study {e['hrs_per_day']}h today!", "#f87171"))
        for title, msg2, col in rems:
            st.markdown(f"""<div style='background:rgba(255,255,255,.03);border-left:3px solid {col};
                border-radius:0 12px 12px 0;padding:.8rem 1rem;margin-bottom:.5rem;'>
                <div style='font-weight:700;color:{col};font-size:.85rem;'>{title}</div>
                <div style='font-size:.82rem;color:#a09cc0;'>{msg2}</div>
            </div>""", unsafe_allow_html=True)

