# -*- coding: utf-8 -*-
"""Worked solutions — Sections 5 to 13 and the appendices."""

SECTIONS_REST = [

# ---------------------------------------------------------------- SECTION 5
{
 "num": 5,
 "kicker": "SEQUENCES & PATTERNS",
 "title": "Sequences and Series in Context",
 "intro": ("Two classic models: <b>arithmetic</b> (constant difference, linear total) and "
           "<b>geometric</b> (constant ratio, often with an infinite sum)."),
 "tasks": [
  {
   "id": "S1", "title": "Saving Up", "criteria": ["D", "B"],
   "diff": "Applying", "marks": 10,
   "stem": "Kofi saves 500 CFA in week 1 and 250 CFA more each week thereafter.",
   "parts": [
    {"p": "(a)",
     "work": ["Arithmetic sequence with a = 500 and d = 250:",
              "u₁₂ = 500 + 11(250) = 500 + 2750"],
     "ans": "3 250 CFA in week 12",
     "mb": "1 mark for the rule · 1 mark for the value with units."},

    {"p": "(b)",
     "work": ["Total after n weeks is the sum of an arithmetic series:",
              "T(n) = n/2 [2a + (n − 1)d]",
              "= n/2 [1000 + 250(n − 1)]",
              "= n/2 [750 + 250n]",
              "= 125n(3 + n)",
              "T(n) = 125n(n + 3)",
              "Check n = 3: 500 + 750 + 1000 = 2250 and 125(3)(6) = 2250 ✓"],
     "ans": "T(n) = 125n(n + 3)",
     "mb": "2 marks for the series formula · 1 mark for factorising · 1 mark for the check."},

    {"p": "(c)",
     "work": ["125n(n + 3) = 70 000  →  n(n + 3) = 560",
              "n² + 3n − 560 = 0",
              "n = [−3 + √(9 + 2240)]/2 = (−3 + 47.42)/2 = 22.21",
              "n must be a whole number: after 22 weeks T = 68 750 CFA, after 23 weeks T = 74 750 CFA.",
              "So the target is first passed during week 23."],
     "ans": "23 weeks (the total passes 70 000 CFA during that week)",
     "mb": "1 mark for the equation · 2 marks for solving · 1 mark for interpreting the non-integer result."}
   ],
   "note": ("Part (c) is a <i>“first exceeds”</i> question: solve, then round <b>up</b> and check both "
            "sides. Giving n = 22.2 without interpretation loses the final mark.")
  },

  {
   "id": "S2", "title": "Bouncing Ball", "criteria": ["B", "D"],
   "diff": "Reasoning", "marks": 10,
   "stem": "A ball is dropped from 2 m and rebounds to 80% of its previous height after each bounce.",
   "parts": [
    {"p": "(a)",
     "work": ["Each height is 0.8 times the previous one:",
              "h₁ = 2(0.8) = 1.6 m",
              "h₂ = 1.6(0.8) = 1.28 m",
              "h₃ = 1.28(0.8) = 1.024 m"],
     "ans": "1.6 m, 1.28 m, 1.024 m",
     "mb": "1 mark per height."},

    {"p": "(b)",
     "work": ["After n bounces the height is the initial height multiplied by 0.8, n times."],
     "ans": "hₙ = 2(0.8)ⁿ metres",
     "mb": "1 mark for the structure · 1 mark for the correct formula."},

    {"p": "(c)",
     "work": ["Distance = first fall + 2 × (each rise), because every rebound is travelled up and then down:",
              "D = 2 + 2(1.6 + 1.28 + 1.024 + 0.8192)",
              "= 2 + 2(4.7232)"],
     "ans": "≈ 11.45 m by the 5th impact",
     "mb": "1 mark for the structure (2× rebounds) · 1 mark for the five terms · 1 mark for the total."},

    {"p": "(d)",
     "work": ["As the number of bounces grows, the bounce heights form a geometric series with |r| &lt; 1, so the total converges:",
              "D∞ = 2 + 2 × 1.6/(1 − 0.8) = 2 + 2(8) = 18 m",
              "The model predicts the ball makes infinitely many ever-smaller bounces and comes to rest after travelling about 18 m. In reality it stops when the rebound is too small to see (energy is also lost to sound and heat)."],
     "ans": "The distance converges to 18 m; the ball effectively stops, though the model allows infinitely many bounces.",
     "mb": "1 mark for recognising a convergent geometric series · 1 mark for the interpretation."}
   ],
   "note": ("The factor of 2 on the rebounds is the most common omission. Only the first fall happens once.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 6
{
 "num": 6,
 "kicker": "ALGEBRA",
 "title": "Equations, Inequalities and Fractions",
 "intro": ("Accuracy of manipulation and clarity of method: every line should follow logically from "
           "the one above it, and every solution should be checked."),
 "tasks": [
  {
   "id": "A1", "title": "Solving Equations — Mixed Practice", "criteria": ["C"],
   "diff": "Applying", "marks": 12,
   "stem": "Solve each equation or inequality, showing all steps.",
   "parts": [
    {"p": "(a)",
     "work": ["3(2x − 5) = 4(x + 1) − 7",
              "6x − 15 = 4x + 4 − 7",
              "6x − 15 = 4x − 3",
              "2x = 12",
              "x = 6",
              "Check: 3(12 − 5) = 21 and 4(7) − 7 = 21 ✓"],
     "ans": "x = 6",
     "mb": "1 mark for expanding both sides · 1 mark for collecting terms · 1 mark for x = 6."},

    {"p": "(b)",
     "work": ["2x + y = 7        (1)",
              "3x − 2y = 8       (2)",
              "From (1): y = 7 − 2x. Substitute into (2):",
              "3x − 2(7 − 2x) = 8",
              "3x − 14 + 4x = 8",
              "7x = 22  →  x = 22/7",
              "y = 7 − 2(22/7) = 49/7 − 44/7 = 5/7",
              "Check in (2): 3(22/7) − 2(5/7) = 66/7 − 10/7 = 56/7 = 8 ✓"],
     "ans": "x = 22/7 ≈ 3.14,  y = 5/7 ≈ 0.71",
     "mb": "1 mark for substitution · 1 mark for solving x · 1 mark for y (exact fractions preferred)."},

    {"p": "(c)",
     "work": ["5 − 2x ≤ 13",
              "−2x ≤ 8",
              "Divide by −2 and <b>reverse the inequality</b>: x ≥ −4",
              "Number line: a solid circle at −4 with the arrow pointing right."],
     "ans": "x ≥ −4",
     "mb": "1 mark for rearranging · 1 mark for reversing the sign · 1 mark for a correct number line."},

    {"p": "(d)",
     "work": ["s = ut + ½at²  →  ½at² + ut − s = 0",
              "Multiply by 2:  at² + 2ut − 2s = 0",
              "This is a quadratic in t with A = a, B = 2u, C = −2s, so",
              "t = [−2u ± √(4u² + 8as)]/(2a) = [−u ± √(u² + 2as)]/a"],
     "ans": "at² + 2ut − 2s = 0, giving t = [−u ± √(u² + 2as)]/a",
     "mb": "1 mark for rearranging · 1 mark for identifying the quadratic · 1 mark for the formula."}
   ],
   "note": ("In (d) the equation is ready to solve but not solved for a specific number: leaving it in "
            "general form with the quadratic formula is the expected answer.")
  },

  {
   "id": "A2", "title": "Algebraic Fractions", "criteria": ["C"],
   "diff": "Reasoning", "marks": 12,
   "stem": "Simplify, combine and solve expressions involving algebraic fractions.",
   "parts": [
    {"p": "(a)",
     "work": ["Factorise both parts:",
              "x² − 4x − 5 = (x − 5)(x + 1)",
              "x² − 1 = (x − 1)(x + 1)",
              "(x − 5)(x + 1)/[(x − 1)(x + 1)] = (x − 5)/(x − 1),  x ≠ ±1"],
     "ans": "(x − 5)/(x − 1),  x ≠ 1, x ≠ −1",
     "mb": "1 mark per factorisation · 1 mark for cancelling · 1 mark for the restrictions."},

    {"p": "(b)",
     "work": ["Common denominator (x + 1)(x − 2):",
              "2/(x + 1) + 3/(x − 2) = [2(x − 2) + 3(x + 1)]/[(x + 1)(x − 2)]",
              "= (2x − 4 + 3x + 3)/[(x + 1)(x − 2)]",
              "= (5x − 1)/[(x + 1)(x − 2)]"],
     "ans": "(5x − 1)/[(x + 1)(x − 2)],  x ≠ −1, 2",
     "mb": "1 mark for the common denominator · 2 marks for the numerator · 1 mark for the restrictions."},

    {"p": "(c)",
     "work": ["3/x + 2/(x + 1) = 4,  x ≠ 0, −1",
              "Multiply through by x(x + 1):",
              "3(x + 1) + 2x = 4x(x + 1)",
              "3x + 3 + 2x = 4x² + 4x",
              "4x² − x − 3 = 0",
              "(4x + 3)(x − 1) = 0",
              "x = 1 or x = −3/4",
              "Checks: x = 1 → 3 + 1 = 4 ✓;  x = −0.75 → −4 + 8 = 4 ✓"],
     "ans": "x = 1 or x = −3/4",
     "mb": "1 mark for clearing the fractions · 1 mark for the quadratic · 1 mark for both roots · 1 mark for checking."}
   ],
   "note": ("Restrictions belong with the answer, not just the working — state them wherever a "
            "denominator could be zero.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 7
{
 "num": 7,
 "kicker": "QUADRATIC RELATIONSHIPS",
 "title": "Modelling with Quadratics",
 "intro": ("Quadratic models describe projectile motion. The vertex gives the maximum, the roots give "
           "the times when the object is at ground level, and the axis of symmetry links the two."),
 "tasks": [
  {
   "id": "Q1", "title": "Projectile Motion", "criteria": ["D", "C"],
   "diff": "Reasoning", "marks": 14,
   "stem": "A ball is thrown from a 2 m platform: h(t) = −5t² + 15t + 2, height in metres, time in seconds.",
   "parts": [
    {"p": "(a)",
     "work": ["At t = 0:  h(0) = −5(0) + 15(0) + 2 = 2.",
              "The constant term of the model is exactly the initial height."],
     "ans": "2 m — the constant term in the formula.",
     "mb": "1 mark for the value · 1 mark for linking it to the constant term."},

    {"p": "(b)",
     "work": ["The ball hits the ground when h = 0:",
              "−5t² + 15t + 2 = 0  →  5t² − 15t − 2 = 0",
              "t = [15 ± √(225 + 40)]/10 = [15 ± √265]/10",
              "t = (15 + 16.279)/10 = 3.128  or  t = (15 − 16.279)/10 = −0.128",
              "The negative root is rejected (time cannot be negative before the throw)."],
     "ans": "t ≈ 3.13 s",
     "mb": "1 mark for setting h = 0 · 1 mark for the quadratic formula · 1 mark for the positive root · 1 mark for rejecting the negative root."},

    {"p": "(c)",
     "work": ["Complete the square: h = −5(t² − 3t) + 2 = −5[(t − 1.5)² − 2.25] + 2",
              "= −5(t − 1.5)² + 11.25 + 2",
              "= −5(t − 1.5)² + 13.25",
              "So the maximum height is 13.25 m, reached at t = 1.5 s.",
              "Check by symmetry: the vertex is midway between the roots, t = (3.128 − 0.128)/2 = 1.5 ✓"],
     "ans": "Maximum 13.25 m at t = 1.5 s",
     "mb": "2 marks for completing the square · 1 mark for the maximum height · 1 mark for the time."},

    {"p": "(d)",
     "work": ["Set h = 8:  −5t² + 15t + 2 = 8  →  5t² − 15t + 6 = 0",
              "t = [15 ± √(225 − 120)]/10 = [15 ± √105]/10 = [15 ± 10.247]/10",
              "t = 0.475 s and t = 2.525 s",
              "Interpretation: the ball passes 8 m on the way up (0.48 s) and again on the way down (2.52 s)."],
     "ans": "t ≈ 0.48 s (rising) and t ≈ 2.52 s (falling)",
     "mb": "1 mark for the equation · 2 marks for both roots · 1 mark for the interpretation."}
   ],
   "note": ("Both roots of (d) are physically meaningful, and the two answers are symmetric about the "
            "vertex at t = 1.5 s — a good way to check.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 8
{
 "num": 8,
 "kicker": "FUNCTIONS & GRAPHS",
 "title": "Trigonometric Models",
 "intro": ("Sine and cosine models describe anything that repeats: tides, daylight, temperatures, "
           "circuits. Identify the midline, the amplitude and the period before calculating."),
 "tasks": [
  {
   "id": "F1", "title": "Tidal Heights", "criteria": ["D", "B"],
   "diff": "Extension Challenge", "marks": 14,
   "stem": "Harbour depth d(t) = 4 + 2 sin(30t°) metres, t hours after midnight.",
   "parts": [
    {"p": "(a)",
     "work": ["At t = 0:  d(0) = 4 + 2 sin 0° = 4 + 0."],
     "ans": "4 m",
     "mb": "1 mark for substitution · 1 mark for the answer."},

    {"p": "(b)",
     "work": ["The sine term ranges from −1 to +1, so d ranges from 4 − 2 = 2 m to 4 + 2 = 6 m.",
              "Maximum when sin(30t°) = 1:  30t = 90  →  t = 3 h (and every 12 hours after: 15 h, 27 h…).",
              "Minimum when sin(30t°) = −1:  30t = 270  →  t = 9 h (and 21 h…)."],
     "ans": "Max 6 m at t = 3 h; min 2 m at t = 9 h.",
     "mb": "1 mark for the range · 1 mark for the maximum time · 1 mark for the minimum time · 1 mark for the values."},

    {"p": "(c)",
     "work": ["The coefficient of t is 30 degrees per hour, so a full 360° cycle takes",
              "T = 360/30 = 12 hours."],
     "ans": "12 hours (semidiurnal tide)",
     "mb": "1 mark for the method · 1 mark for 12 h."},

    {"p": "(d)",
     "work": ["4 + 2 sin(30t°) ≥ 3  →  sin(30t°) ≥ −0.5",
              "In the first 12 hours, 30t runs from 0° to 360°. Since sin x ≥ −0.5 for 0° ≤ x ≤ 210° and 330° ≤ x ≤ 360°:",
              "30t ≤ 210  →  t ≤ 7 h     and     30t ≥ 330  →  t ≥ 11 h",
              "So the depth is at least 3 m from midnight to 7 h, and again from 11 h to noon: 8 hours in total."],
     "ans": "0 ≤ t ≤ 7 and 11 ≤ t ≤ 12 — 8 hours in total.",
     "mb": "2 marks for the correct inequality in sine · 1 mark for the intervals · 1 mark for the total."},

    {"p": "(e)",
     "work": ["The model assumes a perfectly regular, symmetric tide with a constant period and amplitude.",
              "Real tides vary with the moon's phase, the season, wind and atmospheric pressure, and many coasts have two unequal high tides per day."],
     "ans": "Real tides are not perfectly sinusoidal or constant in amplitude.",
     "mb": "1 mark for a valid limitation · 1 mark for the explanation."}
   ],
   "note": ("The 12-hour period means the pattern repeats at t + 12. Answers that list only the first "
            "occurrence of a maximum or minimum are incomplete.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 9
{
 "num": 9,
 "kicker": "GEOMETRY & MEASUREMENT",
 "title": "Circle Theorems, Solids and Scale",
 "intro": ("Diagrams, theorems and units: state the theorem you use, keep exact values where possible, "
           "and give answers with correct units."),
 "tasks": [
  {
   "id": "G1", "title": "Intersecting Chords", "criteria": ["C"],
   "diff": "Applying", "marks": 10,
   "stem": "Chords AB and CD intersect at E inside a circle.",
   "parts": [
    {"p": "(a)",
     "work": ["If two chords intersect inside a circle, the products of the segments of each chord are equal:",
              "AE × EB = CE × ED"],
     "ans": "AE · EB = CE · ED",
     "mb": "2 marks for the complete statement."},

    {"p": "(b)",
     "work": ["6 × 4 = 3 × ED",
              "24 = 3 ED",
              "ED = 8"],
     "ans": "ED = 8",
     "mb": "1 mark for the equation · 1 mark for solving · 1 mark for units/statement."},

    {"p": "(c)",
     "work": ["CD = CE + ED = 3 + 8"],
     "ans": "CD = 11",
     "mb": "1 mark for the sum · 1 mark for the answer."},

    {"p": "(d)",
     "work": ["AB is a diameter of length 12, so the radius is 6 and the centre is 6 cm from each end. E is 2 cm from the centre, so",
              "AE = 6 + 2 = 8  and  EB = 6 − 2 = 4",
              "AE × EB = 8 × 4 = 32, so CE × ED = 32.",
              "If CD is perpendicular to AB, then E is the midpoint of CD: CE = ED = √32 = 4√2.",
              "CD = 2 × 4√2 = 8√2 ≈ 11.3 cm."],
     "ans": "CE · ED = 32; if CD ⊥ AB then CD = 8√2 ≈ 11.3 cm.",
     "mb": "1 mark for splitting the diameter · 1 mark for the product 32 · 1 mark for the conclusion."}
   ],
   "note": ("Part (d) is deliberately open: the product relationship always holds, but the length CD can "
            "only be found if CD is also perpendicular to the diameter — which is what makes E the midpoint.")
  },

  {
   "id": "G2", "title": "Volumes of 3D Shapes", "criteria": ["D", "C"],
   "diff": "Applying", "marks": 13,
   "stem": "A cone with r = 5 cm, h = 18 cm and a sphere with r = 6 cm.",
   "parts": [
    {"p": "(a)",
     "work": ["V(cone) = (1/3)πr²h = ⅓π(25)(18)",
              "= 150π"],
     "ans": "150π ≈ 471.2 cm³",
     "mb": "1 mark for the formula · 1 mark for substitution · 1 mark for the exact value."},

    {"p": "(b)",
     "work": ["V(sphere) = (4/3)πr³ = (4/3)π(216)",
              "= 288π"],
     "ans": "288π ≈ 904.8 cm³",
     "mb": "1 mark for the formula · 1 mark for substitution · 1 mark for the exact value."},

    {"p": "(c)",
     "work": ["288π − 150π = 138π ≈ 433.5 cm³"],
     "ans": "The sphere is larger by 138π ≈ 433.5 cm³.",
     "mb": "1 mark for the comparison · 1 mark for the difference."},

    {"p": "(d)",
     "work": ["Removing the sphere leaves a cylindrical hole of the same volume.",
              "V = πr²Δh  →  288π = π(6)²Δh = 36π Δh",
              "Δh = 288π/36π = 8"],
     "ans": "The level drops by 8 cm.",
     "mb": "1 mark for equating volumes · 1 mark for dividing by 36π · 1 mark for the answer."},

    {"p": "(e)",
     "work": ["Volume is conserved when the cone is recast:",
              "150π = π(5)²h  →  150π = 25π h  →  h = 6"],
     "ans": "h = 6 cm",
     "mb": "1 mark for equating volumes · 1 mark for the answer."}
   ],
   "note": ("Leaving answers in terms of π first makes (c) and (d) almost trivial — exact values are also "
            "easier to check.")
  },

  {
   "id": "G3", "title": "Pyramid Roof", "criteria": ["D", "C"],
   "diff": "Reasoning", "marks": 12,
   "stem": "A square base of side 6 m with a pyramid roof whose apex is 4 m above the centre.",
   "parts": [
    {"p": "(a)",
     "work": ["The slant height is the hypotenuse of a right triangle whose legs are the height (4 m) and the distance from the centre to the midpoint of a side (3 m):",
              "l² = 4² + 3² = 16 + 9 = 25",
              "l = 5"],
     "ans": "Slant height = 5 m",
     "mb": "1 mark for identifying the triangle · 1 mark for Pythagoras · 1 mark for the answer."},

    {"p": "(b)",
     "work": ["Each face is a triangle with base 6 m and slant height 5 m:",
              "Area of one face = ½ × 6 × 5 = 15 m²",
              "Four faces = 4 × 15 = 60 m²"],
     "ans": "15 m² per face; 60 m² in total",
     "mb": "1 mark for the triangle area formula · 1 mark for one face · 1 mark for the total · 1 mark for units."},

    {"p": "(c)",
     "work": ["60 m² × 7500 CFA/m²"],
     "ans": "450 000 CFA",
     "mb": "1 mark for the multiplication · 1 mark for the answer with units."},

    {"p": "(d)",
     "work": ["V = (1/3) × base area × height = ⅓ × (6 × 6) × 4",
              "= ⅓ × 36 × 4"],
     "ans": "48 m³",
     "mb": "1 mark for the formula · 1 mark for the base area · 1 mark for the volume."}
   ],
   "note": ("The slant height is <i>not</i> the height of the pyramid: the triangle uses half the base "
            "(3 m), not the full side (6 m).")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 10
{
 "num": 10,
 "kicker": "STATISTICS",
 "title": "Working with Grouped Data",
 "intro": ("For grouped data, estimate each value by the class mid-point. The shape of the distribution "
           "tells you how mean, median and mode will compare."),
 "tasks": [
  {
   "id": "St1", "title": "Analysing Height Data", "criteria": ["D", "C"],
   "diff": "Applying", "marks": 12,
   "stem": "Heights of 200 students in 5 cm classes from 140–145 to 180–185.",
   "parts": [
    {"p": "(a)",
     "work": ["Frequencies rise to a peak in 155–160 (44 students) and then fall away on both sides, roughly symmetrically.",
              "The modal class is the class with the highest frequency."],
     "ans": "Roughly symmetric, single-peaked; modal class 155–160 cm.",
     "mb": "1 mark for shape · 1 mark for the modal class · 1 mark for using frequencies."},

    {"p": "(b)",
     "work": ["Use class mid-points × frequency, then divide by 200."],
     "tbl": {"widths": ["24%", "20%", "20%", "36%"],
             "head": ["Class (cm)", "Mid-point", "Frequency", "Mid-point × frequency"],
             "rows": [["140–145", "142.5", "8", "1 140"],
                      ["145–150", "147.5", "18", "2 655"],
                      ["150–155", "152.5", "32", "4 880"],
                      ["155–160", "157.5", "44", "6 930"],
                      ["160–165", "162.5", "42", "6 825"],
                      ["165–170", "167.5", "29", "4 857.5"],
                      ["170–175", "172.5", "17", "2 932.5"],
                      ["175–180", "177.5", "8", "1 420"],
                      ["180–185", "182.5", "2", "365"],
                      ["Total", "—", "200", "32 005"]]},
     "ans": "Estimated mean = 32 005/200 = 160.0 cm",
     "mb": "2 marks for mid-points · 1 mark for the products · 1 mark for the total · 1 mark for the mean."},

    {"p": "(c)",
     "work": ["The distribution is close to symmetric, so the balance point (mean) and the middle value (median) nearly coincide.",
              "Skewness pulls the mean towards the longer tail; here there is very little skew (only 2 students above 180 and 26 below 150)."],
     "ans": "The data are nearly symmetric, so mean ≈ median.",
     "mb": "1 mark for “symmetric” · 1 mark for explaining the effect of skew."},

    {"p": "(d)",
     "work": ["Students between 150 and 175 cm: 32 + 44 + 42 + 29 + 17 = 164.",
              "164/200 = 82%.",
              "So 82% — about four in five — lie in that range, but 36 students (18%) lie outside it."],
     "ans": "Broadly true but overstated: 82%, not “almost all”.",
     "mb": "1 mark for the calculation · 1 mark for evaluating the wording."}
   ],
   "note": ("“Almost all” is an evaluative phrase: quote the percentage and say whether the phrase is "
            "justified. 82% is a large majority, not almost all.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 11
{
 "num": 11,
 "kicker": "PROBABILITY",
 "title": "Tree Diagrams Without Replacement",
 "intro": ("Without replacement, the denominator of the second branch changes, and so do the numerators. "
           "Every path probability is a product; paths that satisfy the event are added."),
 "tasks": [
  {
   "id": "P1", "title": "Two Marbles Without Replacement", "criteria": ["D", "C"],
   "diff": "Applying", "marks": 12,
   "stem": "A bag contains 5 red and 4 blue marbles; two are drawn without replacement.",
   "parts": [
    {"p": "(a)",
     "work": ["First draw: 9 marbles in total, 5 red and 4 blue.",
              "Second draw: only 8 marbles remain, and one marble of the first colour has gone.",
              "Note: the tree printed in the question paper shows 3/5 and 2/5 on the first branches and 1/2, 3/4 on the second — those values do not match 5 red and 4 blue. The correct tree is:"],
     "tbl": {"widths": ["22%", "26%", "26%", "26%"],
             "head": ["First draw", "Second draw", "Path", "Probability"],
             "rows": [["Red 5/9", "Red 4/8", "RR", "20/72 = 5/18"],
                      ["Red 5/9", "Blue 4/8", "RB", "20/72 = 5/18"],
                      ["Blue 4/9", "Red 5/8", "BR", "20/72 = 5/18"],
                      ["Blue 4/9", "Blue 3/8", "BB", "12/72 = 1/6"]]},
     "ans": "P(R) = 5/9, P(B) = 4/9; then 4/8 or 5/8, and 4/8 or 3/8.",
     "mb": "1 mark for the first branches · 2 marks for the second branches · 1 mark for correct path products."},

    {"p": "(b)",
     "work": ["P(RR) = (5/9) × (4/8) = 20/72"],
     "ans": "5/18 ≈ 0.278",
     "mb": "1 mark for the product · 1 mark for the simplified fraction."},

    {"p": "(c)",
     "work": ["Different colours means RB or BR:",
              "P(RB) = (5/9)(4/8) = 5/18",
              "P(BR) = (4/9)(5/8) = 5/18",
              "P(different) = 5/18 + 5/18 = 10/18"],
     "ans": "5/9 ≈ 0.556",
     "mb": "1 mark for the two paths · 1 mark for adding · 1 mark for simplifying."},

    {"p": "(d)",
     "work": ["P(second red) = P(RR) + P(BR) = 5/18 + 5/18 = 10/18 = 5/9.",
              "This equals P(first red) = 5/9.",
              "Comment: the second draw is not affected in the long run — the marbles are exchangeable, so any draw has the same 5/9 chance of being red. Removing a marble changes the second probability <i>given</i> the first result, but not the overall probability."],
     "ans": "5/9 — the same as the first draw.",
     "mb": "1 mark for the calculation · 2 marks for the insight about symmetry/exchangeability."}
   ],
   "note": ("Part (d) is the classic “surprising symmetry” result. The check is that the total probability "
            "of red on the second draw must be 5/9, since the colours are randomly arranged in the bag.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 12
{
 "num": 12,
 "kicker": "FINANCIAL MATHEMATICS",
 "title": "Depreciation and Reducing Balance",
 "intro": ("Reducing-balance depreciation is compound interest with a negative rate: multiply by "
           "(1 − r) each year. Straight-line depreciation subtracts a fixed amount instead."),
 "tasks": [
  {
   "id": "Fn1", "title": "Depreciating a Motorcycle", "criteria": ["D", "B"],
   "diff": "Applying", "marks": 12,
   "stem": "A new motorcycle costs 1 200 000 CFA and depreciates at 12% per year (reducing balance).",
   "parts": [
    {"p": "(a)",
     "work": ["After 1 year: 1 200 000(0.88) = 1 056 000",
              "After 3 years: 1 200 000(0.88)³ = 1 200 000 × 0.681472 = 817 766.4"],
     "ans": "1 056 000 CFA after 1 year; ≈ 817 766 CFA after 3 years",
     "mb": "1 mark for the multiplier 0.88 · 1 mark for year 1 · 1 mark for year 3."},

    {"p": "(b)",
     "work": ["Each year the value is 88% of the previous year's value."],
     "ans": "V(t) = 1 200 000(0.88)ᵗ",
     "mb": "1 mark for the structure · 1 mark for the correct constants."},

    {"p": "(c)",
     "work": ["1 200 000(0.88)ᵗ &lt; 500 000  →  (0.88)ᵗ &lt; 0.416667",
              "t &gt; log(0.416667)/log(0.88) = (−0.38021)/(−0.05552) = 6.85",
              "So the value is still above 500 000 after 6 years (557 285 CFA) and below it after 7 years (490 411 CFA)."],
     "ans": "After 7 complete years",
     "mb": "1 mark for the inequality · 2 marks for solving with logs · 1 mark for the year and check."},

    {"p": "(d)",
     "work": ["Reducing balance after 5 years: 1 200 000(0.88)⁵ = 1 200 000 × 0.527732 = 633 278 CFA",
              "Straight line: 12% of 1 200 000 = 144 000 per year, so V = 1 200 000 − 5(144 000) = 480 000 CFA",
              "Difference: 633 278 − 480 000 = 153 278 CFA"],
     "ans": "Reducing balance is higher by ≈ 153 278 CFA.",
     "mb": "1 mark for the reducing-balance value · 1 mark for the straight-line value · 1 mark for the comparison."}
   ],
   "note": ("Reducing balance depreciates more slowly in money terms at first, so it leaves a higher "
            "value than straight line for the same nominal rate.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 13
{
 "num": 13,
 "kicker": "MIXED CHALLENGE",
 "title": "MYP 5 eAssessment Challenges",
 "intro": ("These tasks combine topics in unfamiliar settings. Before calculating, write down the model "
           "you will use and the assumptions it makes."),
 "tasks": [
  {
   "id": "M1", "title": "Planning a Concert", "criteria": ["D", "C", "B"],
   "diff": "eAssessment Challenge", "marks": 18,
   "stem": "A hall seats 800. Fixed costs: venue 500 000, performer 300 000, security 200 000 CFA; variable cost 500 CFA per person. Ticket price x CFA. Demand N(x) = 800 − 0.05x.",
   "parts": [
    {"p": "(a)",
     "work": ["Fixed costs = 500 000 + 300 000 + 200 000 = 1 000 000 CFA",
              "Variable cost for 800 tickets = 800 × 500 = 400 000 CFA",
              "Revenue if all 800 sell at x CFA = 800x"],
     "ans": "1 000 000 CFA; 400 000 CFA; 800x CFA",
     "mb": "1 mark for fixed · 1 mark for variable · 2 marks for revenue."},

    {"p": "(b)",
     "work": ["Profit = revenue − total cost",
              "P(x) = 800x − (1 000 000 + 400 000)",
              "P(x) = 800x − 1 400 000"],
     "ans": "P(x) = 800x − 1 400 000",
     "mb": "2 marks for the cost structure · 1 mark for the simplified form."},

    {"p": "(c)",
     "work": ["Break-even: 800x − 1 400 000 = 0",
              "x = 1 400 000/800 = 1750"],
     "ans": "1 750 CFA per ticket",
     "mb": "1 mark for setting P = 0 · 1 mark for the value."},

    {"p": "(d)",
     "work": ["A constant 800 tickets sold at every price is unrealistic: as the price rises, some people decide not to come.",
              "The model N(x) = 800 − 0.05x reduces the number sold by 0.05 tickets for every 1 CFA increase (50 tickets for each 1000 CFA), which matches the usual downward-sloping demand.",
              "It also stays sensible: at x = 0 (free entry) N = 800, the full capacity."],
     "ans": "Demand falls as price rises; it is capped at the 800-seat capacity.",
     "mb": "2 marks for the reasoning · 1 mark for linking to capacity/context."},

    {"p": "(e)",
     "work": ["Revenue = price × number sold = x(800 − 0.05x)",
              "Variable cost = 500 × N(x) = 500(800 − 0.05x) = 400 000 − 25x",
              "Π(x) = x(800 − 0.05x) − 1 000 000 − (400 000 − 25x)",
              "= 800x − 0.05x² − 1 000 000 − 400 000 + 25x",
              "Π(x) = −0.05x² + 825x − 1 400 000"],
     "ans": "Π(x) = −0.05x² + 825x − 1 400 000",
     "mb": "1 mark for revenue · 1 mark for variable cost · 1 mark for simplifying."},

    {"p": "(f)",
     "work": ["The quadratic opens downwards, so the vertex gives the maximum.",
              "x = −b/(2a) = −825/(2 × −0.05) = 8250",
              "Π(8250) = −0.05(8250)² + 825(8250) − 1 400 000",
              "= −3 403 125 + 6 806 250 − 1 400 000 = 2 003 125",
              "Tickets sold: N(8250) = 800 − 412.5 = 387.5 ≈ 388.",
              "So the optimum is a high price with only about half the hall full."],
     "ans": "x = 8 250 CFA, maximum profit ≈ 2 003 125 CFA (≈ 388 tickets).",
     "mb": "1 mark for the vertex method · 1 mark for the price · 1 mark for the profit."}
   ],
   "note": ("The “all tickets sell” model and the demand model give very different answers — a good "
            "discussion point about how modelling assumptions change conclusions.")
  },

  {
   "id": "M2", "title": "Cell Growth and Medication", "criteria": ["D", "B", "C"],
   "diff": "eAssessment Challenge", "marks": 18,
   "stem": "Strain P: P(t) = 200 + 80t. Strain Q: Q(t) = 50 × 2^(t/3). Medication kills 90% of Q when Q exceeds 5000.",
   "parts": [
    {"p": "(a)",
     "work": ["P(0) = 200 + 0 = 200",
              "Q(0) = 50 × 2⁰ = 50"],
     "ans": "P: 200; Q: 50",
     "mb": "1 mark each."},

    {"p": "(b)",
     "work": ["At t = 0 the linear strain grows at 80 cells per hour.",
              "Q grows exponentially; its instantaneous rate at t = 0 is Q′(0) = 50 × (ln 2)/3 ≈ 11.5 cells per hour.",
              "So P is growing faster at t = 0 — but Q's rate doubles every 3 hours."],
     "ans": "P (80 per hour vs ≈ 11.5 per hour initially).",
     "mb": "1 mark for P's rate · 1 mark for comparing with Q · 1 mark for the conclusion."},

    {"p": "(c)",
     "work": ["t = 6:  P = 200 + 480 = 680;   Q = 50 × 2² = 200",
              "t = 12: P = 200 + 960 = 1160;  Q = 50 × 2⁴ = 800"],
     "ans": "t = 6: 680 and 200;  t = 12: 1 160 and 800",
     "mb": "1 mark per correct pair (2) · 2 marks for accuracy."},

    {"p": "(d)",
     "work": ["50 × 2^(t/3) = 5000  →  2^(t/3) = 100",
              "t/3 = log₂ 100 = 6.644",
              "t = 19.93"],
     "ans": "t ≈ 20 hours",
     "mb": "1 mark for dividing by 50 · 2 marks for logs · 1 mark for rounding to the nearest hour."},

    {"p": "(e)",
     "work": ["Just before treatment Q ≈ 5080, so after killing 90% about 508 remain.",
              "From then on Q(t) = 508 × 2^((t − 20)/3).",
              "Q exceeds 5000 again when 2^((t−20)/3) = 10  →  (t − 20)/3 = 3.322",
              "t − 20 = 9.97  →  t ≈ 30 hours"],
     "ans": "About 10 hours later, at t ≈ 30 hours.",
     "mb": "1 mark for the reduced population · 1 mark for the factor of 10 · 1 mark for the time."},

    {"p": "(f)",
     "work": ["In the long run the exponential strain dominates: Q grows without limit while P grows only linearly, so Q becomes vastly larger than P.",
              "Limitations: unlimited exponential growth is unrealistic (nutrients run out), the “instant” 90% kill ignores how the drug is absorbed, and the model has no resistance or repeated dosing."],
     "ans": "Q dominates long-term; both models ignore resource limits and drug dynamics.",
     "mb": "1 mark for the long-term comparison · 2 marks for limitations."}
   ],
   "note": ("Part (e) is a two-stage exponential: reset the population, then restart the clock. "
            "Students often answer 20 hours again.")
  },

  {
   "id": "M3", "title": "The Clock Tower", "criteria": ["D", "C"],
   "diff": "eAssessment Challenge", "marks": 16,
   "stem": "From C (25 m from the base B) the angle of elevation to the top A is 32°; from D, further back on the same line, it is 20°.",
   "parts": [
    {"p": "(a)",
     "work": ["A labelled diagram should show: a vertical tower AB with B at ground level, C and D on the horizontal line through B, and the two right angles at B.",
              "Mark 25 m from B to C, the angle 32° at C and 20° at D, with D beyond C."],
     "ans": "Vertical tower, horizontal ground, both angles measured from the ground at C and D.",
     "mb": "1 mark for the layout · 1 mark for the labels."},

    {"p": "(b)",
     "work": ["In the right triangle ABC, AB is opposite the 32° angle and BC = 25 is adjacent:",
              "tan 32° = AB/25  →  AB = 25 tan 32° = 25 × 0.624869"],
     "ans": "AB ≈ 15.6 m",
     "mb": "1 mark for the tangent ratio · 1 mark for substitution · 1 mark for the answer to 0.1 m."},

    {"p": "(c)",
     "work": ["For the larger triangle ABD: tan 20° = AB/BD  →  BD = AB/tan 20°",
              "BD = 15.6217/0.363970 = 42.920",
              "CD = BD − BC = 42.920 − 25"],
     "ans": "BD ≈ 42.9 m; CD ≈ 17.9 m",
     "mb": "2 marks for BD · 1 mark for the subtraction · 1 mark for the answer."},

    {"p": "(d)",
     "work": ["The clock has diameter 2 m centred at height AB, so its top and bottom are at heights AB + 1 and AB − 1:",
              "top: tan α = 16.6217/25  →  α = 33.62°",
              "bottom: tan β = 14.6217/25  →  β = 30.32°",
              "Angle subtended = α − β = 3.30°"],
     "ans": "≈ 3.3° (between the lines of sight to the top and bottom of the clock)",
     "mb": "2 marks for the two heights · 1 mark for both angles · 1 mark for the difference."},

    {"p": "(e)",
     "work": ["<b>Assumption:</b> the ground is horizontal and level, the tower is vertical, and C, D, B are collinear.",
              "<b>Error source:</b> the clinometer reading of 1°–2°, the measurement of 25 m, or the height of the observer's eye if the angles were taken from eye level rather than the ground."],
     "ans": "Level ground/vertical tower; angle and distance measurement error.",
     "mb": "1 mark for an assumption · 1 mark for an error source · 1 mark for explanation."}
   ],
   "note": ("Part (d) is an <i>angle subtended</i> question: find the elevation of the top and of the "
            "bottom, then subtract. Do not simply halve the diameter.")
  },

  {
   "id": "M4", "title": "Rational Function Drug Model", "criteria": ["B", "C", "D"],
   "diff": "eAssessment Challenge", "marks": 14,
   "stem": "Drug concentration C(t) = 20t/(t² + 4) mg/L, t ≥ 0 hours after injection.",
   "parts": [
    {"p": "(a)",
     "work": ["C(1) = 20(1)/(1 + 4) = 20/5",
              "C(4) = 80/(16 + 4) = 80/20"],
     "ans": "C(1) = 4 mg/L and C(4) = 4 mg/L",
     "mb": "1 mark each."},

    {"p": "(b)",
     "work": ["The degree of the denominator (2) exceeds the degree of the numerator (1), so C(t) → 0 as t → ∞.",
              "Horizontal asymptote: y = 0 (the t-axis).",
              "Meaning: the drug is eventually eliminated, so the concentration approaches zero."],
     "ans": "y = 0; concentration tends to zero in the long run.",
     "mb": "1 mark for the asymptote · 2 marks for the meaning/reasoning."},

    {"p": "(c)",
     "work": ["20t/(t² + 4) = 4  →  20t = 4t² + 16",
              "4t² − 20t + 16 = 0  →  t² − 5t + 4 = 0",
              "(t − 1)(t − 4) = 0",
              "t = 1 or t = 4"],
     "ans": "t = 1.00 h and t = 4.00 h",
     "mb": "1 mark for clearing the fraction · 1 mark for the quadratic · 2 marks for both roots."},

    {"p": "(d)",
     "work": ["Complete the square in the denominator, or use the quotient rule:",
              "C′(t) = [20(t² + 4) − 20t(2t)]/(t² + 4)² = (80 − 20t²)/(t² + 4)²",
              "Set C′ = 0: 80 − 20t² = 0  →  t² = 4  →  t = 2 (t ≥ 0).",
              "C(2) = 40/8 = 5",
              "So the maximum concentration is 5 mg/L at t = 2 hours."],
     "ans": "Maximum 5 mg/L at t = 2 h",
     "mb": "1 mark for the derivative/approach · 1 mark for t = 2 · 1 mark for 5 mg/L."},

    {"p": "(e)",
     "work": ["C(t) ≥ 4 between the two solutions found in (c): from t = 1 to t = 4.",
              "Duration = 4 − 1 = 3 hours."],
     "ans": "3 hours (1 ≤ t ≤ 4)",
     "mb": "1 mark for the interval · 1 mark for the duration."}
   ],
   "note": ("Parts (c)–(e) connect: the two solutions of C = 4 are the times the drug enters and leaves "
            "the effective range, and the peak sits midway at t = 2.")
  }
 ]
}
]

# ------------------------------------------------------------------ APPENDICES
APPENDICES = [
 {
  "num": "A",
  "kicker": "MARK SCHEME",
  "title": "How the Marks Are Awarded",
  "intro": "The conventions used throughout this answer sheet, and how they map to the three MYP criteria.",
  "blocks": [
   {"kind": "paras", "items": [
     "<b>M — method marks</b> are for a valid approach: choosing the correct formula, setting up an equation, drawing a correct diagram, or starting a valid chain of reasoning. A method mark can be earned even if the arithmetic later slips.",
     "<b>A — accuracy marks</b> are for correct values, correct units and correct rounding. They usually depend on the method mark in the same part.",
     "<b>R — reasoning and communication marks</b> are for explanation, justification, correct notation and a logical sequence of steps. This is where Criterion C is assessed.",
     "<b>D — interpretation marks</b> are for reading the answer back into the context: stating what it means, checking whether it is reasonable, naming assumptions and limitations.",
     "<b>Follow-through:</b> an arithmetic slip early in a question does not automatically lose later marks — a correct method applied to an incorrect value still earns method marks. Accuracy marks, however, are lost.",
     "<b>Equivalent methods</b> are always accepted: trial and improvement, graphing, the quadratic formula or completing the square are all valid where the mathematics allows. This document shows <i>a</i> model solution, not <i>the only</i> solution.",
     "<b>Rounding:</b> keep full accuracy in the working and round only at the end, to the precision requested (or 3 significant figures where none is stated). Premature rounding is the most common cause of lost accuracy marks."
   ]},
   {"kind": "table",
    "widths": ["20%", "40%", "40%"],
    "head": ["Criterion", "What is assessed", "What earns the top band"],
    "rows": [
      ["B — Investigating patterns", "Recognising patterns, describing them as relationships or general rules, and justifying or proving them.", "A general rule stated algebraically, tested on further cases, and justified structurally — not just inferred from a table."],
      ["C — Communicating", "Using forms of representation, moving between them, and communicating reasoning with correct notation and logical structure.", "Clear, sequenced working; correct notation and units; labelled diagrams; every step justified."],
      ["D — Applying mathematics", "Identifying relevant elements, selecting appropriate tools, applying them and evaluating the results in context.", "An explicit model, stated assumptions, accurate calculation, and a critical evaluation of reasonableness and limitations."]
    ]}
  ],
  "after": [
    "Each criterion is marked out of 8, so the four criteria together give a maximum of 32 — the structure used by the MYP Mathematics eAssessment. The bands below describe the kind of performance associated with each level.",
    {"kind": "table",
     "widths": ["11%", "30%", "30%", "29%"],
     "head": ["Level", "Criterion B", "Criterion C", "Criterion D"],
     "rows": [
       ["1–2", "Makes a limited attempt to use a strategy; recognises little or no pattern.", "Uses limited forms of representation; communication is unclear or incomplete.", "Identifies few relevant elements; applies little mathematics."],
       ["3–4", "Applies a strategy with guidance; describes a simple pattern.", "Uses appropriate forms of representation, with some success in communicating reasoning.", "Identifies some relevant elements; applies straightforward tools with partial success."],
       ["5–6", "Selects and applies appropriate strategies; describes patterns as general rules and begins to justify them.", "Moves between forms of representation; communicates coherent reasoning with generally correct notation.", "Selects appropriate tools; applies them accurately; gives a reasonable interpretation of results."],
       ["7–8", "Uses flexible and efficient strategies; states general rules and justifies or proves them, testing and refining.", "Moves fluently between forms; communicates complete, precise and logically structured reasoning.", "Identifies relevant elements fully, models effectively, evaluates results critically and discusses limitations."]
     ]},
    "<font color='#5F7182'>These descriptors are a study aid summarising the spirit of the criteria, not an official IB publication. Always use your school's task-specific clarifications when a task is actually assessed.</font>",
    "Every task in the bank carries one criterion as its <b>main</b> focus and often one or two supporting criteria. Use the table below to build a revision plan that targets a specific criterion.",
    {"kind": "coverage"},
    "Where marks are most often lost in each criterion: <b>B</b> — giving a formula with no evidence of how it was found, or generalising from too few cases. <b>C</b> — correct answers with no working, missing units, unlabelled diagrams, and conclusions that are asserted rather than explained. <b>D</b> — jumping to the calculation before defining the model, ignoring units, and never commenting on whether the answer is reasonable."
  ]
 },
 {
  "num": "B",
  "kicker": "REFERENCE",
  "title": "Formula Bank",
  "intro": "Every formula used in this question bank, grouped by topic. Learn the structure, not just the symbols.",
  "blocks": [
   {"kind": "grid", "items": [
     {"h": "Sequences", "rows": [
       "Arithmetic term: uₙ = a + (n − 1)d",
       "Arithmetic sum: Sₙ = n/2[2a + (n − 1)d]",
       "Geometric term: uₙ = arⁿ⁻¹",
       "Geometric sum: Sₙ = a(1 − rⁿ)/(1 − r)",
       "Infinite sum (|r| &lt; 1): S∞ = a/(1 − r)"
     ]},
     {"h": "Quadratics", "rows": [
       "Roots: x = [−b ± √(b² − 4ac)] / (2a)",
       "Vertex form: y = a(x − h)² + k",
       "Axis of symmetry: x = −b/(2a)",
       "Discriminant: b² − 4ac",
       "Completed square: a(x + b/2a)² + c − b²/(4a)"
     ]},
     {"h": "Growth and finance", "rows": [
       "Compound: A = P(1 + r)ᵗ",
       "Compounded n times: A = P(1 + r/n)^(nt)",
       "Simple: A = P(1 + rt)",
       "Doubling time: t = ln 2 / ln(1 + r)",
       "Depreciation: V = V₀(1 − r)ᵗ",
       "Effective rate: (1 + r/n)ⁿ − 1"
     ]},
     {"h": "Geometry", "rows": [
       "Circle: A = πr², C = 2πr",
       "Arc length: (θ/360) × 2πr",
       "Sector area: (θ/360) × πr²",
       "Cylinder: V = πr²h, curved area 2πrh",
       "Cone: V = (1/3)πr²h, slant l = √(r² + h²)",
       "Sphere: V = (4/3)πr³, A = 4πr²",
       "Pyramid: V = (1/3) × base area × height"
     ]},
     {"h": "Trigonometry", "rows": [
       "sin θ = opp/hyp, cos θ = adj/hyp, tan θ = opp/adj",
       "Sine rule: a/sin A = b/sin B",
       "Cosine rule: a² = b² + c² − 2bc cos A",
       "Area of triangle = ½ab sin C",
       "sin²θ + cos²θ = 1",
       "sin 30° = ½, cos 30° = √3/2, tan 45° = 1"
     ]},
     {"h": "Statistics and probability", "rows": [
       "Mean of grouped data: Σfx/Σf",
       "IQR = Q3 − Q1; range = max − min",
       "P(A or B) = P(A) + P(B) − P(A and B)",
       "P(A and B) = P(A) × P(B | A)",
       "P(B | A) = P(A and B)/P(A)",
       "Expected value: E(X) = Σ x P(x)"
     ]},
     {"h": "Circle theorems", "rows": [
       "Angle in a semicircle = 90° (Thales)",
       "Angle at centre = 2 × angle at circumference",
       "Angles in the same segment are equal",
       "Cyclic quadrilateral: opposite angles sum to 180°",
       "Tangent ⊥ radius at the point of contact",
       "Intersecting chords: AE × EB = CE × ED"
     ]},
     {"h": "Angles, bearings and units", "rows": [
       "Bearings: three figures, measured clockwise from north",
       "Back-bearing = bearing ± 180°",
       "Angles of elevation are measured from the horizontal",
       "1 m³ = 1000 litres; 1 litre = 1000 cm³",
       "1 hectare = 10 000 m²",
       "Speed = distance ÷ time (km/h ↔ m/s: ÷ 3.6)"
     ]}
   ]}
  ]
 },
 {
  "num": "C",
  "kicker": "EXAM TECHNIQUE",
  "title": "Ten Habits That Earn Marks",
  "intro": "The patterns that separate a solid answer from an excellent one in the eAssessment.",
  "blocks": [
   {"kind": "numbered", "items": [
     "<b>Read the command word.</b> “Describe” needs words, “determine” needs a calculation, “justify” needs a reason, “evaluate” needs a judgement.",
     "<b>Name the model before substituting.</b> A single line — “using the cosine rule” — earns the method mark even if the arithmetic goes wrong.",
     "<b>Draw and label.</b> Bearing, ladder and tower problems become straightforward once the right angle and the included angle are marked.",
     "<b>Keep exact values.</b> Carry π, √ and fractions to the end; round only for the final statement.",
     "<b>State units every time.</b> A gradient of 6 means nothing until it is “6 dollars per hour”.",
     "<b>Comment on the answer.</b> Is a population of 343 000 plausible? Is 58 cents per game fair? The interpretation is worth marks.",
     "<b>Show the check.</b> Substituting back, or testing either side of a threshold, is quick and often earns a mark.",
     "<b>Test a general rule.</b> After finding M(n) = 2n + 1, verify n = 4 against the diagram before moving on.",
     "<b>For “show that”, work forwards.</b> Start from one side and transform it into the other — never assume the result you are asked to show.",
     "<b>Manage the time.</b> Aim for roughly a mark a minute, and take the accessible parts of every question before returning to the harder ones."
   ]},
   {"kind": "paras", "items": [
     "<b>Note on this answer sheet.</b> The tasks are practice items written in the style of the MYP 5 eAssessment. Several parts are deliberately open — for example B2(e), D5(d) and D8 — so that students must <i>interpret</i> a result rather than simply calculate one. Where the printed question paper contains an inconsistency (the tree diagram in P1 and the gradient quoted in D8), the model answer says so explicitly and accepts both readings."
   ]}
  ]
 }
 ,
 {
  "num": "D",
  "kicker": "QUICK REFERENCE",
  "title": "Answer Key at a Glance",
  "intro": ("Every final answer in one place, for fast checking. The full method for each task is in the "
            "sections earlier in this document."),
  "blocks": [
   {"kind": "answerkey"}
  ]
 }
]
