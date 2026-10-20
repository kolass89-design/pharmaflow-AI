# -*- coding: utf-8 -*-
"""Worked solutions — Sections 2, 3 and 4 (Criteria B, C and D).

Markup: <b>, <i>, <super>, <sub>.  Bare "<" and ">" must be written &lt; / &gt;
(the renderer also escapes " < " and " > " automatically).
"""

SECTIONS_BCD = [

# ---------------------------------------------------------------- SECTION 2
{
 "num": 2,
 "kicker": "CRITERION B",
 "title": "Investigating Patterns",
 "intro": ("Every answer must move from <i>observation</i> to <i>generalisation</i> to "
           "<i>justification</i>. A formula alone earns about half the marks: the rest "
           "come from describing the pattern in words, testing it and justifying it."),
 "tasks": [
  {
   "id": "B1", "title": "Matchstick Triangles", "criteria": ["B"],
   "diff": "Applying", "marks": 14,
   "stem": "Equilateral triangles are built in a row; each new triangle shares one stick with the previous one.",
   "parts": [
    {"p": "(a)",
     "work": ["Count the sticks in the four printed figures, then continue the pattern:",
              "3, 5, 7, 9, 11, 13 — add 2 for each new triangle."],
     "tbl": {"widths": ["34%"] + ["11%"] * 6,
             "head": ["Figure, n", "1", "2", "3", "4", "5", "6"],
             "rows": [["Matchsticks, M", "3", "5", "7", "9", "11", "13"]]},
     "ans": "M = 3, 5, 7, 9, 11, 13",
     "mb": "1 mark for two correct values · 2 marks for one slip · 3 marks for all six."},

    {"p": "(b)",
     "work": ["Each extra triangle adds <b>two</b> sticks, so the first differences are constant (+2).",
              "Reason: a new triangle shares one of its sides with the triangle before it, so only two of its three sides are new."],
     "ans": "The number of sticks increases by 2 each time (constant first difference).",
     "mb": "1 mark for “+2” · 1 mark for linking it to the shared side."},

    {"p": "(c)",
     "work": ["Start at 3 sticks and add 2 sticks (n − 1) times:",
              "M(n) = 3 + 2(n − 1) = 3 + 2n − 2",
              "M(n) = 2n + 1"],
     "ans": "M(n) = 2n + 1",
     "mb": "1 mark for 3 + 2(n − 1) · 1 mark for simplifying · 1 mark for correct notation."},

    {"p": "(d)",
     "work": ["Substitute n = 20 into the general rule:",
              "M(20) = 2(20) + 1 = 40 + 1 = 41"],
     "ans": "41 matchsticks",
     "mb": "1 mark for substitution · 1 mark for the answer with units."},

    {"p": "(e)",
     "work": ["Set M(n) = 100:  2n + 1 = 100   so   2n = 99   so   n = 49.5.",
              "A figure number must be a whole number, and 49.5 is not.",
              "Check either side: Figure 49 uses 99 sticks and Figure 50 uses 101 sticks, so 100 is skipped."],
     "ans": "No — 100 is not of the form 2n + 1 for a whole number n (99 and 101 are possible).",
     "mb": "1 mark for forming and solving 2n + 1 = 100 · 1 mark for a justified conclusion."},

    {"p": "(f)",
     "work": ["The first triangle needs 3 sticks. Every triangle after the first adds 2 new sticks, because one of its sides is already counted as the right-hand side of the previous triangle.",
              "There are (n − 1) such extra triangles, so M(n) = 3 + 2(n − 1).",
              "This is a structural justification: it explains <i>why</i> the rule works for every n, not just for the figures printed."],
     "ans": "3 + 2(n − 1): one shared side per new triangle gives the constant +2.",
     "mb": "1 mark for identifying the shared side · 1 mark for a general argument covering all n."}
   ],
   "note": ("A table alone is <i>not</i> a justification. Criterion B rewards the move from "
            "“I noticed” to “this is why it must always be true”.")
  },

  {
   "id": "B2", "title": "Square Dot Arrays", "criteria": ["B", "C"],
   "diff": "Reasoning", "marks": 15,
   "stem": "Figure k is a square array with k dots along each side.",
   "parts": [
    {"p": "(a)",
     "work": ["Total dots: each side has n dots, so the array is n × n.",
              "Perimeter dots: count the four sides (4n) and correct the four corner dots counted twice (−4). For n = 1 the single dot is the whole perimeter, so P(1) = 1."],
     "tbl": {"widths": ["34%"] + ["11%"] * 6,
             "head": ["n", "1", "2", "3", "4", "5", "6"],
             "rows": [["Total dots, D(n)", "1", "4", "9", "16", "25", "36"],
                      ["Perimeter dots, P(n)", "1", "4", "8", "12", "16", "20"]]},
     "ans": "D: 1, 4, 9, 16, 25, 36   and   P: 1, 4, 8, 12, 16, 20",
     "mb": "1 mark for the D row · 2 marks for the P row (1 mark if only P(4) onwards is right)."},

    {"p": "(b)",
     "work": ["D(n) = n × n, since Figure n is an n by n square of dots.",
              "P(n) = 4n − 4, because the four sides contribute 4n dots but each of the four corners has been counted twice."],
     "ans": "D(n) = n²   and   P(n) = 4n − 4  (n ≥ 2)",
     "mb": "1 mark for D(n) = n² · 2 marks for P(n) = 4n − 4 with the “−4 corners” reason."},

    {"p": "(c)",
     "work": ["D(n):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1&nbsp;&nbsp;&nbsp;4&nbsp;&nbsp;&nbsp;9&nbsp;&nbsp;&nbsp;16&nbsp;&nbsp;&nbsp;25&nbsp;&nbsp;&nbsp;36",
              "1st diff:&nbsp;&nbsp;&nbsp;3&nbsp;&nbsp;&nbsp;5&nbsp;&nbsp;&nbsp;7&nbsp;&nbsp;&nbsp;9&nbsp;&nbsp;&nbsp;11",
              "2nd diff:&nbsp;&nbsp;&nbsp;2&nbsp;&nbsp;&nbsp;2&nbsp;&nbsp;&nbsp;2&nbsp;&nbsp;&nbsp;2",
              "The second differences are constant, which is the signature of a quadratic sequence."],
     "ans": "Constant second difference of 2, so D(n) is quadratic.",
     "mb": "1 mark for a correct difference table · 1 mark for the conclusion from constant 2nd differences."},

    {"p": "(d)",
     "work": ["I(n) = D(n) − P(n) = n² − (4n − 4)",
              "I(n) = n² − 4n + 4 = (n − 2)²"],
     "ans": "I(n) = n² − 4n + 4 = (n − 2)²",
     "mb": "1 mark for substituting · 1 mark for simplifying · 1 mark for the factorised form."},

    {"p": "(e)",
     "work": ["Set I(n) = P(n):  (n − 2)² = 4n − 4",
              "n² − 4n + 4 = 4n − 4",
              "n² − 8n + 8 = 0",
              "n = [8 ± √(64 − 32)] / 2 = 4 ± 2√2  →  n ≈ 1.17 or n ≈ 6.83",
              "Neither value is a whole number, so no numbered figure has equal interior and perimeter dots; the two counts pass through equality between Figures 6 and 7.",
              "Sanity check at n = 7: I = 25, P = 24 — interior overtakes perimeter here."],
     "ans": "No whole-number solution; equality would occur at n ≈ 6.83 (between Figures 6 and 7).",
     "mb": "1 mark for a correct equation · 1 mark for solving · 1 mark for interpreting the non-integer result."}
   ],
   "note": ("Part (e) is deliberately non-integer: a strong answer <i>interprets</i> the result "
            "rather than forcing n = 7. Accept “no solution in whole numbers” with working.")
  },

  {
   "id": "B3", "title": "Staircase Block Patterns", "criteria": ["B"],
   "diff": "Investigating", "marks": 16,
   "stem": "Staircases are built from unit cubes in columns of heights n, n − 1, …, 1.",
   "parts": [
    {"p": "(a)",
     "work": ["Read each figure column by column: Figure 1 has 1 cube, Figure 2 has 1 + 2, Figure 3 has 1 + 2 + 3, and so on."],
     "tbl": {"widths": ["34%"] + ["11%"] * 6,
             "head": ["n", "1", "2", "3", "4", "5", "6"],
             "rows": [["Cubes, S(n)", "1", "3", "6", "10", "15", "21"]]},
     "ans": "S: 1, 3, 6, 10, 15, 21",
     "mb": "1 mark per two correct entries; 3 marks for an accurate table."},

    {"p": "(b)",
     "work": ["S:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1&nbsp;&nbsp;&nbsp;&nbsp;3&nbsp;&nbsp;&nbsp;&nbsp;6&nbsp;&nbsp;&nbsp;&nbsp;10&nbsp;&nbsp;&nbsp;15&nbsp;&nbsp;&nbsp;21",
              "1st diff:&nbsp;&nbsp;&nbsp;2&nbsp;&nbsp;&nbsp;&nbsp;3&nbsp;&nbsp;&nbsp;&nbsp;4&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5&nbsp;&nbsp;&nbsp;&nbsp;6",
              "2nd diff:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;1&nbsp;&nbsp;&nbsp;&nbsp;1&nbsp;&nbsp;&nbsp;&nbsp;1&nbsp;&nbsp;&nbsp;&nbsp;1",
              "The first differences increase by 1 each time and the second differences are constant, so the sequence is quadratic (triangular numbers)."],
     "ans": "Quadratic sequence — constant second difference of 1.",
     "mb": "1 mark for first differences · 1 mark for second differences · 1 mark for the classification."},

    {"p": "(c)",
     "work": ["Let S(n) = an² + bn + c and substitute three values:",
              "n = 1:  a + b + c = 1        (i)",
              "n = 2:  4a + 2b + c = 3      (ii)",
              "(ii) − (i):  3a + b = 2      (iv)",
              "n = 3:  9a + 3b + c = 6      (iii)",
              "(iii) − (ii):  5a + b = 3    (v)",
              "(v) − (iv):  2a = 1  →  a = ½,  then b = ½,  then c = 0.",
              "S(n) = ½n² + ½n = n(n + 1)/2"],
     "ans": "S(n) = ½n² + ½n, i.e. S(n) = n(n + 1)/2",
     "mb": "2 marks for forming equations · 1 mark for solving a, b · 1 mark for c and the final rule."},

    {"p": "(d)",
     "work": ["S(30) = ½(30)² + ½(30) = 450 + 15 = 465."],
     "ans": "465 cubes",
     "mb": "1 mark for substitution · 1 mark for the answer."},

    {"p": "(e)",
     "work": ["Test the claim T(n) = n(n + 1)(n + 2)/6:",
              "T(1) = 1·2·3/6 = 1 = S(1)  ✓",
              "T(2) = 2·3·4/6 = 4, but S(2) = 3  ✗",
              "One counter-example is enough to disprove a general claim.",
              "Algebraically T(n) = S(n)(n + 2)/3, which equals S(n) only when (n + 2)/3 = 1, i.e. n = 1. For every n ≥ 2, T(n) is strictly larger.",
              "T(n) is in fact the tetrahedral number — the sum of triangular numbers, not the triangular number itself."],
     "ans": "Disproved: T(2) = 4 ≠ 3; T(n) = S(n)(n + 2)/3, so they agree only at n = 1.",
     "mb": "2 marks for checking n = 1 to 4 · 1 mark for the counter-example · 1 mark for the algebraic comparison."}
   ],
   "note": ("Part (e) rewards <i>disproving by counter-example</i> — an important Criterion B skill. "
            "Students who “prove” the claim usually expand both expressions carelessly.")
  },

  {
   "id": "B4", "title": "Hexagonal Flower", "criteria": ["B", "C"],
   "diff": "Extension Challenge", "marks": 18,
   "stem": "A central dot is surrounded by hexagonal rings of dots.",
   "parts": [
    {"p": "(a)",
     "work": ["Ring 1 is the centre itself (1 dot). Ring 2 has 6 dots, ring 3 has 12, ring 4 has 18, ring 5 has 24 — each ring adds 6 more than the one before."],
     "tbl": {"widths": ["30%", "14%", "14%", "14%", "14%", "14%"],
             "head": ["n", "1", "2", "3", "4", "5"],
             "rows": [["Dots added in ring", "1", "6", "12", "18", "24"],
                      ["Total, H(n)", "1", "7", "19", "37", "61"]]},
     "ans": "H: 1, 7, 19, 37, 61 (additions 1, 6, 12, 18, 24)",
     "mb": "2 marks for the “added” row · 2 marks for the totals."},

    {"p": "(b)",
     "work": ["Each hexagonal ring has six sides, and side k − 1 of ring k carries (k − 1) dots.",
              "So ring k (k ≥ 2) contains 6(k − 1) dots."],
     "ans": "Ring k has 6(k − 1) dots (k ≥ 2); ring 1 is the single centre dot.",
     "mb": "1 mark for “six sides” · 2 marks for the formula 6(k − 1)."},

    {"p": "(c)",
     "work": ["H(n) = 1 + 6(1) + 6(2) + … + 6(n − 1)",
              "H(n) = 1 + 6[1 + 2 + … + (n − 1)]",
              "The bracket is the sum of the first (n − 1) integers: (n − 1)n/2.",
              "H(n) = 1 + 6 · n(n − 1)/2 = 1 + 3n(n − 1)",
              "Check: n = 4 gives 1 + 3(4)(3) = 37 ✓, matching the figure."],
     "ans": "H(n) = 1 + 3n(n − 1), derived by summing the six-sided rings.",
     "mb": "2 marks for the summation set-up · 2 marks for summing the series · 1 mark for the check/justification."},

    {"p": "(d)",
     "work": ["H(10) = 1 + 3(10)(9) = 1 + 270 = 271."],
     "ans": "271 dots",
     "mb": "2 marks (1 for substitution, 1 for the value)."},

    {"p": "(e)",
     "work": ["1 + 3n(n − 1) = 217  →  3n(n − 1) = 216  →  n(n − 1) = 72",
              "n² − n − 72 = 0  →  (n − 9)(n + 8) = 0  →  n = 9 (n = −8 rejected)."],
     "ans": "9 rings",
     "mb": "2 marks for a correct equation · 1 mark for solving · 1 mark for rejecting the negative root."}
   ],
   "note": ("The strength of the answer to (c) is the <b>summation argument</b>: the ring sizes form an "
            "arithmetic sequence, so their total is quadratic in n.")
  },

  {
   "id": "B5", "title": "Arithmetic vs Geometric Growth", "criteria": ["B", "C"],
   "diff": "Reasoning", "marks": 15,
   "stem": "Sequence A: first term 20, common difference 15. Sequence G: first term 2, common ratio 2.",
   "parts": [
    {"p": "(a)",
     "work": ["Arithmetic: add 15 each time.   Geometric: multiply by 2 each time."],
     "tbl": {"widths": ["16%", "14%", "14%", "14%", "14%", "14%", "14%"],
             "head": ["n", "1", "2", "3", "4", "5", "6"],
             "rows": [["A(n)", "20", "35", "50", "65", "80", "95"],
                      ["G(n)", "2", "4", "8", "16", "32", "64"]]},
     "ans": "A: 20, 35, 50, 65, 80, 95    G: 2, 4, 8, 16, 32, 64",
     "mb": "2 marks for A · 1 mark for G."},

    {"p": "(b)",
     "work": ["A(n) = 20 + 15(n − 1) = 15n + 5",
              "G(n) = 2 × 2ⁿ⁻¹ = 2ⁿ"],
     "ans": "A(n) = 15n + 5   and   G(n) = 2ⁿ",
     "mb": "2 marks for A(n) · 1 mark for G(n) = 2ⁿ."},

    {"p": "(c)",
     "work": ["2ⁿ &gt; 10 000. Powers of 2: 2¹³ = 8192, 2¹⁴ = 16 384.",
              "So the 14th term is the first to exceed 10 000. (log₂ 10 000 ≈ 13.29 confirms this.)"],
     "ans": "n = 14",
     "mb": "1 mark for a correct strategy (listing or logs) · 1 mark for n = 14."},

    {"p": "(d)",
     "work": ["The arithmetic sequence plots as a <b>straight line</b> with gradient 15 (constant difference).",
              "The geometric sequence plots as an <b>increasing curve</b> that starts below the line, crosses it, and then rises far more steeply.",
              "Both graphs begin near the origin; G is below A until n ≈ 7, then above for all later n."],
     "ans": "Straight line (constant difference) vs. upward curve (constant ratio); G overtakes A near n = 7.",
     "mb": "1 mark for two correct graphs · 2 marks for describing difference in shape · 1 mark for the crossing point."},

    {"p": "(e)",
     "work": ["Compare 2ⁿ with 15n + 5:",
              "n = 6: 64 &lt; 95    n = 7: 128 &gt; 110  →  the smallest n is 7.",
              "Once G(7) &gt; A(7), the gap cannot close: each step multiplies G by 2 while A only adds 15. The ratio G/A = 2ⁿ/(15n + 5) grows without bound, so G stays ahead for all larger n."],
     "ans": "n = 7; exponential growth eventually dominates any linear growth.",
     "mb": "1 mark for testing values · 1 mark for n = 7 · 1 mark for the growth-rate justification."}
   ],
   "note": ("Answers to (e) that only say “the graph is steeper” earn 1 of 3 marks. The key idea is the "
            "<i>ratio</i> between the terms, not a single comparison.")
  },

  {
   "id": "B6", "title": "Transforming y = x²", "criteria": ["B", "C"],
   "diff": "Investigating", "marks": 14,
   "stem": "Investigate how changing the equation of y = x² transforms its graph.",
   "parts": [
    {"p": "(a)",
     "work": ["(i)  y = x² + 3: translate <b>3 units up</b>; vertex (0, 3).",
              "(ii) y = (x + 2)²: translate <b>2 units left</b> (inside the bracket acts the opposite way); vertex (−2, 0).",
              "(iii) y = −x²: <b>reflection in the x-axis</b>; vertex (0, 0), now a maximum.",
              "(iv) y = 2x²: <b>vertical stretch, factor 2</b> (narrower); vertex (0, 0)."],
     "ans": "up 3 · left 2 · reflected in x-axis · stretched ×2 vertically; vertices (0,3), (−2,0), (0,0), (0,0)",
     "mb": "1 mark per transformation and vertex (4 marks)."},

    {"p": "(b)",
     "work": ["Evaluate both sides at three values of x:",
              "x = 0:  (0 − 3)² + 1 = 10  and  0 − 0 + 10 = 10  ✓",
              "x = 1:  (−2)² + 1 = 5  and  1 − 6 + 10 = 5  ✓",
              "x = 2:  (−1)² + 1 = 2  and  4 − 12 + 10 = 2  ✓",
              "Three checks support the claim, but the rigorous proof is the expansion: (x − 3)² + 1 = x² − 6x + 9 + 1 = x² − 6x + 10."],
     "ans": "The two expressions agree at every x (identity), shown by expanding.",
     "mb": "2 marks for three correct substitutions · 1 mark for recognising that expansion is the proof."},

    {"p": "(c)",
     "work": ["y = x² − 4x + 7 = (x² − 4x) + 7 = (x − 2)² − 4 + 7",
              "y = (x − 2)² + 3, so the vertex is (2, 3)."],
     "ans": "y = (x − 2)² + 3, vertex (2, 3)",
     "mb": "1 mark for halving the coefficient · 1 mark for completing the square · 1 mark for the vertex."},

    {"p": "(d)",
     "work": ["y = 2(x + 1)² − 4 compared with y = x²:",
              "• inside the bracket: shift <b>1 unit left</b>;",
              "• coefficient 2: <b>vertical stretch by factor 2</b>;",
              "• −4 outside: shift <b>4 units down</b>;",
              "• no negative sign, so no reflection.",
              "Vertex: (−1, −4); it is a minimum, and the curve is narrower than y = x²."],
     "ans": "Left 1, vertical stretch ×2, down 4; vertex (−1, −4), minimum.",
     "mb": "1 mark per correct transformation (3) · 1 mark for vertex and nature."}
   ],
   "note": ("Watch the classic error in (d): the +1 inside the bracket moves the graph <b>left</b>, not right.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 3
{
 "num": 3,
 "kicker": "CRITERION C",
 "title": "Communicating",
 "intro": ("Criterion C is about the <i>quality of the communication</i>: notation, logical steps, "
           "labelled diagrams, correct units and explanations that a reader can follow. "
           "A correct answer with no working rarely reaches the top band."),
 "tasks": [
  {
   "id": "C1", "title": "Spot the Error: Solving an Equation", "criteria": ["C"],
   "diff": "Applying", "marks": 10,
   "stem": "A student solved 2(x − 3) = 3x + 4 as shown; identify and correct the errors.",
   "parts": [
    {"p": "(a)",
     "work": ["<b>Step 1 is wrong.</b> The bracket was not fully expanded: 2(x − 3) = 2x − 6, not 2x − 3. The 2 must multiply both terms inside the bracket.",
              "<b>Step 2 inherits the error</b> and also mixes up the constant: using the correct expansion, 2x − 6 = 3x + 4 gives −6 − 4 = 3x − 2x.",
              "<b>Step 3 gives −10 = x</b> (not −7 = x).",
              "<b>Step 4 is a sign error:</b> −10 = x means x = −10, not x = 7. A negative number cannot become positive by rearranging."],
     "ans": "Errors at Step 1 (incomplete expansion), Step 2 (wrong constant carried forward) and Step 4 (sign change).",
     "mb": "1 mark for each error correctly identified with a reason (max 3) · 1 mark for clear communication."},

    {"p": "(b)",
     "work": ["2(x − 3) = 3x + 4",
              "2x − 6 = 3x + 4",
              "2x − 3x = 4 + 6",
              "−x = 10",
              "x = −10"],
     "ans": "x = −10",
     "mb": "1 mark for correct expansion · 1 mark for correct rearrangement · 1 mark for x = −10."},

    {"p": "(c)",
     "work": ["LHS: 2(−10 − 3) = 2(−13) = −26",
              "RHS: 3(−10) + 4 = −30 + 4 = −26",
              "Both sides equal −26, so the solution is verified."],
     "ans": "LHS = RHS = −26 ✓",
     "mb": "1 mark for substituting into both sides · 1 mark for a clear conclusion."}
   ],
   "note": ("This task assesses <i>error analysis</i>, a common eAssessment item type: name the error, "
            "explain it, then correct it.")
  },

  {
   "id": "C2", "title": "Reading a Linear Graph", "criteria": ["C", "D"],
   "diff": "Applying", "marks": 12,
   "stem": "A bicycle-hire graph shows cost C (dollars) against hours t; it passes through (0, 10) with gradient 6.",
   "parts": [
    {"p": "(a)",
     "work": ["The fixed deposit is the cost when t = 0, i.e. the <b>y-intercept</b> of the graph: the line crosses the vertical axis at 10."],
     "ans": "$10 (the y-intercept)",
     "mb": "1 mark for reading the intercept · 1 mark for linking it to “cost at zero hours”."},

    {"p": "(b)",
     "work": ["Choosing two points on the line, e.g. (0, 10) and (5, 40):",
              "gradient = (40 − 10)/(5 − 0) = 30/5 = 6",
              "Units: dollars per hour — the hire charge for each additional hour."],
     "ans": "Gradient = 6 dollars per hour (cost per hour of hire).",
     "mb": "2 marks for the calculation with points · 1 mark for the units and interpretation."},

    {"p": "(c)",
     "work": ["C = mt + b with m = 6 and b = 10."],
     "ans": "C = 6t + 10",
     "mb": "1 mark for correct m and b · 1 mark for the equation."},

    {"p": "(d)",
     "work": ["C(5) = 6(5) + 10 = 30 + 10 = 40."],
     "ans": "$40",
     "mb": "1 mark for substitution · 1 mark for the answer with units."},

    {"p": "(e)",
     "work": ["46 = 6t + 10  →  36 = 6t  →  t = 6.",
              "Check: 6(6) + 10 = 46 ✓"],
     "ans": "6 hours",
     "mb": "2 marks for solving the equation · 1 mark for checking/units."}
   ],
   "note": ("Always state units for a gradient in a context question — it is a Criterion C hallmark.")
  },

  {
   "id": "C3", "title": "Analysing a Parabola", "criteria": ["C", "B"],
   "diff": "Reasoning", "marks": 14,
   "stem": "Consider f(x) = x² − 2x − 3 and its graph.",
   "parts": [
    {"p": "(a)",
     "work": ["y-intercept: put x = 0 → f(0) = −3.",
              "x-intercepts: the curve cuts the x-axis at −1 and 3.",
              "Vertex: the lowest point is at x = 1, y = −4."],
     "ans": "(0, −3);  (−1, 0) and (3, 0);  (1, −4)",
     "mb": "1 mark for y-intercept · 2 marks for both x-intercepts · 1 mark for the vertex."},

    {"p": "(b)",
     "work": ["x² − 2x − 3: two numbers with product −3 and sum −2 are −3 and +1.",
              "x² − 2x − 3 = (x − 3)(x + 1)",
              "Roots x = 3 and x = −1, confirming the graph."],
     "ans": "f(x) = (x − 3)(x + 1), so x = 3 or x = −1",
     "mb": "2 marks for the factorisation · 1 mark for stating the roots."},

    {"p": "(c)",
     "work": ["x² − 2x − 3 = (x² − 2x + 1) − 1 − 3",
              "= (x − 1)² − 4",
              "Vertex form y = (x − 1)² − 4 gives vertex (1, −4) — the same as the graph."],
     "ans": "f(x) = (x − 1)² − 4, vertex (1, −4)",
     "mb": "1 mark for (x − 1)² · 1 mark for adjusting the constant · 1 mark for the vertex."},

    {"p": "(d)",
     "work": ["The coefficient of x² is +1 &gt; 0, so the parabola opens upwards: the vertex is the lowest point, hence a <b>minimum</b>.",
              "That minimum value is −4 at x = 1."],
     "ans": "Minimum of −4 (at x = 1), because a = 1 &gt; 0.",
     "mb": "1 mark for “minimum” · 1 mark for the reason based on the sign of a."},

    {"p": "(e)",
     "work": ["Axis of symmetry: x = 1.",
              "From the factored form: the axis lies midway between the roots, x = (−1 + 3)/2 = 1.",
              "From the vertex form: the axis is x = h in y = (x − h)² + k, so x = 1."],
     "ans": "x = 1, found both as the midpoint of the roots and as x = h in vertex form.",
     "mb": "1 mark for x = 1 · 1 mark for both derivations."}
   ],
   "note": ("Comparing three representations (graph, factorised, vertex form) is exactly the kind of "
            "Criterion C “move between forms” the eAssessment rewards.")
  },

  {
   "id": "C4", "title": "Exponential Growth vs Decay", "criteria": ["C", "B"],
   "diff": "Reasoning", "marks": 13,
   "stem": "The graphs of y = 2ˣ and y = (½)ˣ are shown.",
   "parts": [
    {"p": "(a)",
     "work": ["y = 2ˣ has base 2 &gt; 1, so each step multiplies by 2 → <b>growth</b>, curve rising to the right.",
              "y = (½)ˣ has base 0 &lt; ½ &lt; 1, so each step multiplies by ½ → <b>decay</b>, curve falling to the right.",
              "Note (½)ˣ = 2⁻ˣ, a reflection of y = 2ˣ in the y-axis."],
     "ans": "2ˣ is growth (base &gt; 1); (½)ˣ is decay (0 &lt; base &lt; 1).",
     "mb": "1 mark for each identification · 1 mark for the reasoning from the base."},

    {"p": "(b)",
     "work": ["At x = 0, a⁰ = 1 for every a ≠ 0, so both graphs pass through (0, 1).",
              "They cannot pass through (0, 0), because no positive base raised to 0 gives 0."],
     "ans": "(0, 1) for both; every y = aˣ has y-intercept 1 because a⁰ = 1.",
     "mb": "1 mark for the intercept · 2 marks for the explanation."},

    {"p": "(c)",
     "work": ["2ˣ = 16 = 2⁴  →  x = 4.",
              "(½)ˣ = 8  →  2⁻ˣ = 2³  →  −x = 3  →  x = −3."],
     "ans": "x = 4  and  x = −3",
     "mb": "2 marks for 2ˣ = 16 · 1 mark for (½)ˣ = 8."},

    {"p": "(d)",
     "work": ["Both graphs approach the x-axis but never touch it: the horizontal asymptote is y = 0.",
              "In context, an exponentially decaying quantity never quite reaches zero — it keeps halving."],
     "ans": "y = 0; the value becomes arbitrarily small but never zero.",
     "mb": "1 mark for the asymptote · 1 mark for the meaning."},

    {"p": "(e)",
     "work": ["For every real x, 2ˣ &gt; 0. A positive number raised to any power is positive, and the graph never reaches the axis, so 2ˣ = 0 has no real solution."],
     "ans": "No real solution, since 2ˣ &gt; 0 for all x.",
     "mb": "1 mark for “always positive” · 1 mark for a complete explanation."}
   ],
   "note": ("The link (½)ˣ = 2⁻ˣ turns a “two separate graphs” question into one idea — worth stating explicitly.")
  },

  {
   "id": "C5", "title": "Understanding a Rational Function", "criteria": ["C"],
   "diff": "Investigating", "marks": 14,
   "stem": "Consider f(x) = (x − 1)/(x + 2).",
   "parts": [
    {"p": "(a)",
     "work": ["The function is undefined where the denominator is zero: x + 2 = 0 → x = −2.",
              "As x approaches −2 the numerator approaches −3 (non-zero) while the denominator approaches 0, so |f(x)| grows without bound.",
              "Vertical asymptote: x = −2."],
     "ans": "x = −2, because the denominator vanishes there and the numerator does not.",
     "mb": "1 mark for x = −2 · 2 marks for the explanation."},

    {"p": "(b)",
     "work": ["Numerator and denominator have the same degree (both linear), so for large |x| the function behaves like the ratio of leading coefficients: x/x = 1.",
              "Horizontal asymptote: y = 1."],
     "ans": "y = 1 (ratio of the leading coefficients).",
     "mb": "1 mark for y = 1 · 2 marks for the reasoning."},

    {"p": "(c)",
     "work": ["x-intercept: numerator zero → x − 1 = 0 → x = 1, giving (1, 0).",
              "y-intercept: x = 0 → f(0) = −1/2, giving (0, −½)."],
     "ans": "(1, 0) and (0, −½)",
     "mb": "2 marks for the x-intercept · 1 mark for the y-intercept."},

    {"p": "(d)",
     "work": ["(x − 1)/(x + 2) = 3, x ≠ −2",
              "x − 1 = 3(x + 2) = 3x + 6",
              "−7 = 2x",
              "x = −3.5",
              "Check: (−3.5 − 1)/(−3.5 + 2) = (−4.5)/(−1.5) = 3 ✓"],
     "ans": "x = −3.5",
     "mb": "1 mark for clearing the fraction · 1 mark for solving · 1 mark for the check."},

    {"p": "(e)",
     "work": ["Critical values: x = −2 (asymptote) and x = 1 (zero). Test each interval:",
              "x &lt; −2, e.g. x = −3: (−4)/(−1) = 4 &gt; 0  → positive",
              "−2 &lt; x &lt; 1, e.g. x = 0: (−1)/(2) = −½ &lt; 0  → negative",
              "x &gt; 1, e.g. x = 2: (1)/(4) &gt; 0  → positive"],
     "ans": "f(x) &gt; 0 for x &lt; −2 or x &gt; 1.",
     "mb": "1 mark for the critical values · 1 mark for a correct sign table/answer."}
   ],
   "note": ("A sign table is the clearest way to communicate part (e) — exactly what Criterion C is looking for.")
  },

  {
   "id": "C6", "title": "The Unit Circle and Sine/Cosine", "criteria": ["C"],
   "diff": "Reasoning", "marks": 12,
   "stem": "A point on the unit circle makes an angle θ with the positive x-axis.",
   "parts": [
    {"p": "(a)",
     "work": ["The diagram forms a right-angled triangle with the radius as hypotenuse.",
              "The radius of the unit circle is 1, the horizontal leg is cos θ and the vertical leg is sin θ.",
              "By Pythagoras:  (cos θ)² + (sin θ)² = 1², i.e. cos²θ + sin²θ = 1."],
     "ans": "Pythagoras on the right triangle with hypotenuse 1.",
     "mb": "1 mark for identifying the triangle · 2 marks for the complete argument."},

    {"p": "(b)",
     "work": ["Take an equilateral triangle of side 2 and drop an altitude: it bisects the base and the 60° angle, giving a right triangle with hypotenuse 2, short leg 1 and altitude √(4 − 1) = √3.",
              "Half of the equilateral triangle gives the 30° angle:",
              "sin 30° = 1/2,  cos 30° = √3/2",
              "The other angle is 60°:",
              "sin 60° = √3/2,  cos 60° = 1/2"],
     "ans": "sin 30° = ½, cos 30° = √3/2, sin 60° = √3/2, cos 60° = ½",
     "mb": "2 marks for the triangle justification · 2 marks for the four exact values."},

    {"p": "(c)",
     "work": ["Reflecting the point (cos θ, sin θ) in the y-axis gives (−cos θ, sin θ).",
              "The reflected point corresponds to the angle 180° − θ, so cos(180° − θ) = −cos θ and sin(180° − θ) = sin θ.",
              "The y-coordinate (height) is unchanged; the x-coordinate changes sign."],
     "ans": "Reflection in the y-axis keeps the sine and reverses the cosine.",
     "mb": "2 marks for the reflection argument · 1 mark for the conclusion."},

    {"p": "(d)",
     "work": ["150° = 180° − 30° lies in the second quadrant, where sine is positive.",
              "sin 150° = sin 30° = 1/2, a positive value."],
     "ans": "Positive; sin 150° = ½",
     "mb": "1 mark for the sign · 1 mark for the exact value."}
   ],
   "note": ("“With justification” in (b) means the exact values must come from a triangle or the circle — "
            "not from a calculator.")
  },

  {
   "id": "C7", "title": "Proving Thales' Theorem", "criteria": ["C", "B"],
   "diff": "Extension Challenge", "marks": 12,
   "stem": "A, B, C lie on a circle with centre O; AB is a diameter. Prove that angle ACB = 90°.",
   "parts": [
    {"p": "(a)",
     "work": ["OA, OB and OC are all radii of the same circle, so OA = OB = OC.",
              "That is the definition of a circle: every point on it is the same distance from the centre."],
     "ans": "All three are radii, hence equal.",
     "mb": "2 marks for a complete reason (radii of one circle)."},

    {"p": "(b)",
     "work": ["Triangle OAC has OA = OC, so the angles opposite those sides are equal: ∠OAC = ∠OCA.",
              "Triangle OBC has OB = OC, so ∠OBC = ∠OCB.",
              "A triangle with two equal sides (and therefore two equal base angles) is isosceles."],
     "ans": "Both triangles have two radii as sides, so both are isosceles.",
     "mb": "1 mark per triangle · 1 mark for naming the base angles."},

    {"p": "(c)",
     "work": ["Let ∠OCA = α and ∠OCB = β.",
              "In △OAC, the angle sum gives ∠AOC = 180° − 2α.",
              "In △OBC, likewise ∠BOC = 180° − 2β.",
              "A, O, B are collinear, so ∠AOC + ∠BOC = 180°:",
              "(180° − 2α) + (180° − 2β) = 180°",
              "360° − 2(α + β) = 180°  →  2(α + β) = 180°  →  α + β = 90°",
              "But ∠ACB = ∠OCA + ∠OCB = α + β, so ∠ACB = 90°"],
     "ans": "α + β = 90°, and ∠ACB = α + β, hence 90°.",
     "mb": "1 mark for ∠AOC · 1 mark for ∠BOC · 1 mark for the straight line · 2 marks for the algebra and conclusion."},

    {"p": "(d)",
     "work": ["Converse: if a triangle ABC has ∠ACB = 90°, then AB is a diameter of its circumcircle — equivalently, C lies on the circle with diameter AB.",
              "This is the form used to construct right angles and to test whether an angle is right."],
     "ans": "If ∠ACB = 90°, then A, B, C lie on a circle with AB as diameter.",
     "mb": "2 marks for the statement · 1 mark for correct logic (converse swaps hypothesis and conclusion)."}
   ],
   "note": ("In a proof, every line needs a <i>reason</i>: angle sum, radii, straight line. Marks are awarded "
            "for those reasons, not just the final 90°.")
  },

  {
   "id": "C8", "title": "Comparing Two Methods", "criteria": ["C"],
   "diff": "Reasoning", "marks": 10,
   "stem": "Two students simplify (x² − 9)/(x² + 5x + 6).",
   "parts": [
    {"p": "(a)",
     "work": ["Student A “cancels” x² with x² and writes −9/(5x + 6). This is invalid: cancelling is only allowed for <b>common factors</b> of the whole numerator and denominator.",
              "x² and −9 are <b>terms</b> joined by subtraction, not factors. Cancelling them changes the value of the expression.",
              "Numerical check: at x = 4 the original is 7/42 = 1/6, while Student A's expression gives −9/26, which is different."],
     "ans": "Terms cannot be cancelled across a subtraction — only factors of the whole expression can.",
     "mb": "2 marks for the explanation · 1 mark for a numerical or algebraic counter-example."},

    {"p": "(b)",
     "work": ["Numerator: x² − 9 = (x − 3)(x + 3)   [difference of two squares]",
              "Denominator: x² + 5x + 6 = (x + 2)(x + 3)   [numbers with product 6 and sum 5]",
              "(x − 3)(x + 3) / [(x + 2)(x + 3)] = (x − 3)/(x + 2),  x ≠ −3",
              "The common factor (x + 3) cancels because it is a factor of the whole numerator and denominator."],
     "ans": "(x − 3)/(x + 2), with x ≠ −3 and x ≠ −2",
     "mb": "1 mark per factorisation · 1 mark for cancelling · 1 mark for the restriction."},

    {"p": "(c)",
     "work": ["The original expression is undefined when its denominator is zero:",
              "x² + 5x + 6 = 0  →  (x + 2)(x + 3) = 0  →  x = −2 or x = −3.",
              "Both values must be stated, even though (x + 3) cancels — the original expression still has a hole at x = −3."],
     "ans": "x = −2 and x = −3",
     "mb": "1 mark for setting the denominator to zero · 2 marks for both values with the restriction stated."}
   ],
   "note": ("The cancelled factor still creates a <i>hole</i> in the graph. Strong answers mention x ≠ −3 "
            "explicitly and distinguish it from the vertical asymptote at x = −2.")
  }
 ]
},

# ---------------------------------------------------------------- SECTION 4
{
 "num": 4,
 "kicker": "CRITERION D",
 "title": "Applying Mathematics in Real-Life Contexts",
 "intro": ("Criterion D answers need four moves: <b>identify</b> the relevant information, "
           "<b>select</b> a model or tool, <b>apply</b> it accurately, and <b>evaluate</b> the result "
           "in context (units, reasonableness, assumptions, limitations)."),
 "tasks": [
  {
   "id": "D1", "title": "Ladder Safety", "criteria": ["D", "C"],
   "diff": "Applying", "marks": 13,
   "stem": "A 5 m ladder leans against a vertical wall at 65° to the horizontal; the recommended angle is 75°.",
   "parts": [
    {"p": "(a)",
     "work": ["The wall height is the side <b>opposite</b> the 65° angle, and the ladder is the hypotenuse:",
              "sin 65° = h/5  →  h = 5 sin 65°",
              "h = 5 × 0.9063 = 4.5315…"],
     "ans": "h ≈ 4.53 m",
     "mb": "1 mark for choosing sine · 1 mark for substitution · 1 mark for the answer to 2 d.p."},

    {"p": "(b)",
     "work": ["The distance from the wall is the <b>adjacent</b> side:",
              "cos 65° = d/5  →  d = 5 cos 65° = 5 × 0.4226 = 2.1131…"],
     "ans": "d ≈ 2.11 m",
     "mb": "1 mark for cosine · 1 mark for the value."},

    {"p": "(c)",
     "work": ["At 75°: h = 5 sin 75° = 5 × 0.9659 = 4.8296…",
              "Increase: 4.8296 − 4.5315 = 0.2981 ≈ 0.30 m."],
     "ans": "≈ 4.83 m — about 0.30 m higher than at 65°.",
     "mb": "1 mark for the new height · 1 mark for the comparison · 1 mark for the difference."},

    {"p": "(d)",
     "work": ["At 75° the ladder is the hypotenuse and 4.5 m is opposite the angle:",
              "L = 4.5/sin 75° = 4.5/0.9659 = 4.6587…",
              "Rounding <b>up</b> to the nearest 0.5 m gives 5.0 m."],
     "ans": "L ≈ 4.66 m, so a 5.0 m ladder is needed.",
     "mb": "1 mark for the trig ratio · 1 mark for 4.66 m · 1 mark for rounding up to 5.0 m."},

    {"p": "(e)",
     "work": ["<b>Assumption:</b> the wall is vertical, the ground is horizontal and the ladder is rigid and straight, so the situation is a right triangle.",
              "<b>Why longer:</b> the foot must be kept clear of a flower bed or step, the top must extend above the window sill for a safe handhold, and the 75° angle must be measured on uneven ground — all reduce the usable height, so a longer ladder is needed."],
     "ans": "Vertical wall / horizontal ground / rigid ladder; allowances for footing, handhold and uneven ground.",
     "mb": "1 mark for an assumption · 1 mark for a practical reason."}
   ],
   "note": ("State the trig ratio before substituting. Criterion D rewards showing the model explicitly, "
            "not only the number.")
  },

  {
   "id": "D2", "title": "Population Growth of a City", "criteria": ["D", "B"],
   "diff": "Reasoning", "marks": 16,
   "stem": "A city had 250 000 people at the start of 2015 and grows at 3.2% per year, P(t) = P₀(1 + r)ᵗ.",
   "parts": [
    {"p": "(a)",
     "work": ["P₀ is the initial population; r is the annual growth rate as a decimal."],
     "ans": "P₀ = 250 000 and r = 0.032",
     "mb": "1 mark each."},

    {"p": "(b)",
     "work": ["The start of 2025 is t = 10 years after 2015.",
              "P(10) = 250 000(1.032)¹⁰ = 250 000 × 1.37024 = 342 560…"],
     "ans": "≈ 343 000 people (342 560 to the nearest person)",
     "mb": "1 mark for t = 10 · 1 mark for substitution · 1 mark for the rounded answer."},

    {"p": "(c)",
     "work": ["250 000(1.032)ᵗ = 400 000",
              "(1.032)ᵗ = 1.6",
              "t = log 1.6 / log 1.032 = 0.47000 / 0.03150 = 14.92",
              "So t = 15 years, i.e. during 2030.",
              "Check: 1.032¹⁴ gives 1.554 → 388 500 (below); 1.032¹⁵ gives 1.604 → 401 000 (above)."],
     "ans": "2030 (t ≈ 14.9 years)",
     "mb": "1 mark for the equation · 2 marks for solving with logs · 1 mark for interpreting the year."},

    {"p": "(d)",
     "work": ["Doubling requires (1.032)ᵗ = 2:",
              "t = log 2 / log 1.032 = 0.30103 / 0.03150 = 22.006…",
              "So the population doubles after about 22 years, in 2037."],
     "ans": "≈ 22 years (2037)",
     "mb": "1 mark for the doubling equation · 2 marks for the logs · 1 mark for the rounded year."},

    {"p": "(e)",
     "work": ["<b>Limitation:</b> unlimited exponential growth assumes a constant rate for ever; in reality births fall, migration changes, and housing, water and jobs limit growth.",
              "<b>Better model:</b> logistic (S-shaped) growth, which starts exponentially but levels off at a carrying capacity, or a piecewise model with a decreasing rate."],
     "ans": "Constant-rate assumption is unrealistic; a logistic model with carrying capacity is better.",
     "mb": "1 mark for a limitation · 1 mark for the model · 1 mark for justification."}
   ],
   "note": ("“Which year” needs an interpretation, not just t = 14.92. Rounding up matters: the threshold is "
            "crossed during year 15.")
  },

  {
   "id": "D3", "title": "Is the Game Fair?", "criteria": ["D", "C"],
   "diff": "Reasoning", "marks": 14,
   "stem": "A spinner: Red 90° pays $5, Blue 120° pays $2, Green 60° pays $10, Yellow 90° pays $0. Entry fee $3.",
   "parts": [
    {"p": "(a)",
     "work": ["Each probability is the sector angle divided by 360°, since the spinner is equally likely to stop anywhere."],
     "tbl": {"widths": ["20%", "18%", "16%", "20%", "26%"],
             "head": ["Colour", "Angle", "P(colour)", "Payout ($)", "P × payout"],
             "rows": [["Red", "90°", "1/4", "5", "1.25"],
                      ["Blue", "120°", "1/3", "2", "0.6667"],
                      ["Green", "60°", "1/6", "10", "1.6667"],
                      ["Yellow", "90°", "1/4", "0", "0"],
                      ["Total", "360°", "1", "—", "3.5833"]]},
     "ans": "1/4, 1/3, 1/6, 1/4 (total 1)",
     "mb": "1 mark per two correct probabilities · 1 mark for the total of 1."},

    {"p": "(b)",
     "work": ["E(payout) = Σ p × payout",
              "= (1/4)(5) + (1/3)(2) + (1/6)(10) + (1/4)(0)",
              "= 1.25 + 0.6667 + 1.6667 + 0",
              "= 3.5833…"],
     "ans": "≈ $3.58 per spin",
     "mb": "2 marks for the products summed · 1 mark for the value."},

    {"p": "(c)",
     "work": ["Expected profit to the player = payout − fee = 3.5833 − 3 = +0.5833.",
              "Since the expected profit is positive, the game favours the <b>player</b>: on average a player gains about 58 cents per spin."],
     "ans": "≈ +$0.58 per spin — not fair; the player has the advantage.",
     "mb": "1 mark for the difference · 1 mark for the conclusion · 1 mark for interpretation."},

    {"p": "(d)",
     "work": ["For a fair game the fee would equal the expected payout: $3.58.",
              "For the school to make $1 expected profit per game:",
              "fee = 3.5833 + 1 = 4.5833."],
     "ans": "≈ $4.58 (fair price $3.58; school-profit price $4.58)",
     "mb": "2 marks for the correct price · 1 mark for distinguishing “fair” from “$1 profit”."},

    {"p": "(e)",
     "work": ["Expected profit per player = 1 (by design), so for 200 players:",
              "200 × 1 = $200.",
              "(Actual profit varies; $200 is the long-run average.)"],
     "ans": "≈ $200 expected",
     "mb": "1 mark for the multiplication · 1 mark for noting it is an expected value."}
   ],
   "note": ("Read (d) carefully: “fair” means expected profit zero ($3.58), but the school wants $1 profit, "
            "so the price must be higher ($4.58).")
  },

  {
   "id": "D4", "title": "Left-Handed or Right-Handed?", "criteria": ["D", "C"],
   "diff": "Applying", "marks": 12,
   "stem": "120 students classified by gender and dominant hand: left-handed 8 male, 6 female; right-handed 52 male, 54 female.",
   "parts": [
    {"p": "(a)",
     "work": ["Total left-handed = 8 + 6 = 14 out of 120.",
              "P(left) = 14/120 = 7/60 ≈ 0.1167"],
     "ans": "7/60 ≈ 0.117 (11.7%)",
     "mb": "1 mark for 14/120 · 1 mark for the decimal/percentage."},

    {"p": "(b)",
     "work": ["Restrict to females (60 students); 6 are left-handed.",
              "P(left | female) = 6/60 = 0.1"],
     "ans": "0.10 (10%)",
     "mb": "1 mark for the restricted denominator · 1 mark for the value."},

    {"p": "(c)",
     "work": ["Restrict to left-handed students (14); 8 are male.",
              "P(male | left) = 8/14 = 4/7 ≈ 0.571"],
     "ans": "4/7 ≈ 0.571 (57.1%)",
     "mb": "1 mark for 8/14 · 1 mark for simplifying."},

    {"p": "(d)",
     "work": ["Independent means P(left | male) = P(left | female) = P(left).",
              "P(left | male) = 8/60 = 0.1333,  P(left | female) = 6/60 = 0.1000,  P(left) = 0.1167.",
              "Alternatively P(male and left) = 8/120 = 0.0667, while P(male) × P(left) = 0.5 × 0.1167 = 0.0583.",
              "The values differ, so the events are <b>not</b> independent — but the gap is small."],
     "ans": "Not independent (0.133 vs 0.100 vs 0.117), though only slightly dependent.",
     "mb": "1 mark for a valid test · 1 mark for the values · 1 mark for the conclusion."},

    {"p": "(e)",
     "work": ["The direction of the claim is right: 13.3% of males are left-handed compared with 10.0% of females.",
              "But the difference is only 3.3 percentage points and rests on just 8 left-handed males out of 60.",
              "A difference of that size is well within sampling variation, so the data <b>suggest</b> a tendency but do not establish it. Larger samples (and a significance test) would be needed."],
     "ans": "Directionally supported (13.3% vs 10.0%) but the evidence is weak — too few left-handers to conclude.",
     "mb": "1 mark for the percentages · 1 mark for the comparison · 1 mark for evaluating reliability."}
   ],
   "note": ("This is a conditional-probability trap: the denominator changes in (b) and (c). "
            "Reading the table row/column totals carefully is the skill being assessed.")
  },

  {
   "id": "D5", "title": "Designing a Water Tank", "criteria": ["D", "C"],
   "diff": "Reasoning", "marks": 16,
   "stem": "An open-top cylinder must hold 5 m³. Curved surface costs 4000 CFA/m², base 6000 CFA/m².",
   "parts": [
    {"p": "(a)",
     "work": ["V = πr²h = 5 with r = 1:",
              "h = 5/(π × 1²) = 1.5915…"],
     "ans": "h ≈ 1.59 m",
     "mb": "1 mark for the formula · 1 mark for substitution · 1 mark for the answer."},

    {"p": "(b)",
     "work": ["With h = 2:  5 = πr²(2)  →  r² = 5/(2π) = 0.7958",
              "r = 0.8921…"],
     "ans": "r ≈ 0.89 m",
     "mb": "1 mark for rearranging · 2 marks for the value."},

    {"p": "(c)",
     "work": ["Curved area = 2πrh = 2π(0.8921)(2) = 11.210 m² → 11.210 × 4000 = 44 840 CFA",
              "Base area = πr² = 2.500 m² → 2.500 × 6000 = 15 000 CFA",
              "Total ≈ 59 840 CFA"],
     "ans": "≈ 59 840 CFA",
     "mb": "1 mark for each area · 1 mark for each cost · 1 mark for the total."},

    {"p": "(d)",
     "work": ["Write the cost in terms of r only, using h = 5/(πr²):",
              "C(r) = 4000(2πr · 5/(πr²)) + 6000(πr²) = 40 000/r + 6000πr²",
              "Testing r = 0.8 to 1.5 m in steps of 0.1 m:"],
     "tbl": {"widths": ["22%", "26%", "26%", "26%"],
             "head": ["r (m)", "h = 5/(πr²) (m)", "Cost (CFA)", "Comment"],
             "rows": [["0.8", "2.487", "62 064", ""],
                      ["0.9", "1.965", "59 713", ""],
                      ["1.0", "1.592", "58 850", "minimum"],
                      ["1.1", "1.315", "59 172", ""],
                      ["1.2", "1.105", "60 477", ""],
                      ["1.3", "0.942", "62 625", ""],
                      ["1.4", "0.812", "65 517", ""],
                      ["1.5", "0.707", "69 078", ""]]},
     "ans": "r ≈ 1.0 m (analytic optimum r ≈ 1.02 m, h ≈ 1.53 m), cost ≈ 58 800 CFA",
     "mb": "1 mark for the cost function in one variable · 1 mark for a complete table · 1 mark for identifying the minimum · 1 mark for r and h."},

    {"p": "(e)",
     "work": ["• <b>Strength and stability:</b> a very tall narrow tank needs thicker walls and a strong base; a very wide tank needs more ground.",
              "• <b>Access and maintenance:</b> a ladder, a lid to keep out dust and mosquitoes, and room to clean it.",
              "• <b>Local conditions:</b> available ground, delivery of materials, and water pressure for filling."],
     "ans": "Stability/strength, access/maintenance, footprint and local site conditions.",
     "mb": "1 mark per valid practical consideration (max 2)."}
   ],
   "note": ("The open top matters: there is <i>no</i> top disc in the cost. Students who include 2πr² "
            "overestimate the cost.")
  },

  {
   "id": "D6", "title": "Comparing Test Scores", "criteria": ["D", "C"],
   "diff": "Reasoning", "marks": 12,
   "stem": "Box plots for Class A and Class B on the same mathematics test.",
   "parts": [
    {"p": "(a)",
     "work": ["Read the five values from each box plot (values are approximate, ±1)."],
     "tbl": {"widths": ["24%", "15%", "15%", "15%", "15%", "16%"],
             "head": ["", "Minimum", "Q1", "Median", "Q3", "Maximum"],
             "rows": [["Class A", "42", "57", "68", "80", "95"],
                      ["Class B", "35", "60", "73", "78", "92"]]},
     "ans": "A: 42, 57, 68, 80, 95    B: 35, 60, 73, 78, 92",
     "mb": "1 mark per correct row (2) · 2 marks for accuracy on all ten values."},

    {"p": "(b)",
     "work": ["<b>Centre:</b> Class B has the higher median (73 vs 68), so a typical B student scored 5 marks more.",
              "<b>Spread:</b> the interquartile ranges are A: 80 − 57 = 23 and B: 78 − 60 = 18, so the middle 50% of B is tighter; the ranges are A: 53 and B: 57, so B has the wider overall spread because of its long lower whisker.",
              "<b>Skewness:</b> A is roughly symmetric (median 68 sits about halfway between the quartiles, and the whiskers are similar at 15 and 15). B is negatively skewed: the median is close to Q3 (73 vs 78) and the lower whisker (35 to 60 = 25) is much longer than the upper (78 to 92 = 14)."],
     "ans": "B has the higher centre but the smaller IQR; A is symmetric, B is left-skewed with a low tail.",
     "mb": "2 marks for centre with values · 1 mark for spread · 1 mark for skewness."},

    {"p": "(c)",
     "work": ["Above Q3 the top 25% of students lie. Interpolating within the upper half of each box:",
              "Class A: 25% + (80 − 75)/(80 − 68) × 25% ≈ 25% + 10% = 35%",
              "Class B: 25% + (78 − 75)/(78 − 73) × 25% ≈ 25% + 15% = 40%"],
     "ans": "Class B — about 40% compared with about 35% in Class A.",
     "mb": "1 mark for using the quartiles · 1 mark for a justified choice (either class accepted with reasoning)."},

    {"p": "(d)",
     "work": ["The claim is <b>partly</b> true. B's median is higher (73 vs 68) and its upper quartile is close, so typical B performance is better.",
              "However A reaches higher at the top (Q3 = 80 vs 78; maximum 95 vs 92) and has a higher floor (minimum 42 vs 35). B's lower whisker shows a group of weak scores.",
              "A balanced judgement: B is better <i>on average</i>, but A is stronger at the top end and has no very low scores — overall performance is comparable."],
     "ans": "Partly supported: B is better in the middle, but A is stronger at the top and has a higher minimum.",
     "mb": "1 mark for a supported judgement · 1 mark for using values from both classes."}
   ],
   "note": ("Compare with <i>numbers</i>. “Class B is better because its box is higher” earns little; "
            "quoting median, IQR and whisker lengths earns the marks.")
  },

  {
   "id": "D7", "title": "Choosing a Savings Account", "criteria": ["D", "B"],
   "diff": "Reasoning", "marks": 15,
   "stem": "Amina invests 200 000 CFA for 5 years. Bank X: 4.5% simple. Bank Y: 4% compound annually. Bank Z: 3.8% compounded quarterly.",
   "parts": [
    {"p": "(a)",
     "work": ["Simple interest: A = P(1 + rt)",
              "A = 200 000(1 + 0.045 × 5) = 200 000 × 1.225"],
     "ans": "245 000 CFA (interest 45 000 CFA)",
     "mb": "1 mark for the formula · 1 mark for substitution · 1 mark for the answer."},

    {"p": "(b)",
     "work": ["Compound interest: A = P(1 + r)ᵗ",
              "A = 200 000(1.04)⁵ = 200 000 × 1.216653"],
     "ans": "≈ 243 331 CFA",
     "mb": "1 mark for the formula · 1 mark for 1.04⁵ · 1 mark for the answer."},

    {"p": "(c)",
     "work": ["Bank X pays 245 000 and Bank Y pays 243 331:",
              "245 000 − 243 331 = 1 669 CFA."],
     "ans": "Bank X pays more, by about 1 670 CFA.",
     "mb": "1 mark for the comparison · 1 mark for the difference."},

    {"p": "(d)",
     "work": ["Doubling at 4%: 200 000(1.04)ᵗ = 400 000  →  (1.04)ᵗ = 2",
              "t = log 2 / log 1.04 = 0.30103 / 0.017033 = 17.67",
              "17 years gives (1.04)¹⁷ = 1.9479 (not yet double); 18 years gives 2.0258 (doubled)."],
     "ans": "18 complete years",
     "mb": "1 mark for the equation · 2 marks for logs · 1 mark for rounding up to a complete year."},

    {"p": "(e)",
     "work": ["Bank Z: quarterly rate 3.8%/4 = 0.95%, with 4 × 5 = 20 quarters.",
              "A = 200 000(1.0095)²⁰ = 200 000 × 1.208187 = 241 637 CFA",
              "Comparison of the three: X 245 000 &gt; Y 243 331 &gt; Z 241 637.",
              "Z's nominal 3.8% is actually 3.85% effective, below Y's 4%.",
              "<b>Recommendation:</b> Y over Z — it pays about 1 690 CFA more after 5 years and is simple to operate. (X pays most over exactly 5 years, but only because its simple rate is higher; beyond about 7 years Y overtakes X.)"],
     "ans": "Z ≈ 241 637 CFA; choose Y over Z (about 1 690 CFA more).",
     "mb": "1 mark for the quarterly set-up · 1 mark for the value · 1 mark for a justified recommendation."}
   ],
   "note": ("Comparing nominal rates is not enough — convert to effective annual rates. Z's 3.8% quarterly "
            "compounding is 3.85% effective, still below Y's 4%.")
  },

  {
   "id": "D8", "title": "Study Time vs Test Score", "criteria": ["D", "C"],
   "diff": "Applying", "marks": 12,
   "stem": "A scatter plot of study hours against test score for 12 students, with line of best fit y = 2.9x + 7.0.",
   "parts": [
    {"p": "(a)",
     "work": ["<b>Direction:</b> positive — more study hours are associated with higher scores.",
              "<b>Strength:</b> strong — the points lie close to a straight line (correlation roughly 0.9).",
              "<b>Form:</b> linear; no obvious curve or outliers."],
     "ans": "Strong positive linear association.",
     "mb": "1 mark per feature (direction, strength, form)."},

    {"p": "(b)",
     "work": ["Using the printed line y = 2.9x + 7.0:",
              "x = 6:  y = 2.9(6) + 7.0 = 24.4",
              "x = 11: y = 2.9(11) + 7.0 = 38.9",
              "(If the gradient 3.2 quoted in the task is used instead: 26.2 and 42.2.)"],
     "ans": "≈ 24% for 6 hours and ≈ 39% for 11 hours",
     "mb": "1 mark each, with substitution shown."},

    {"p": "(c)",
     "work": ["The data cover only about 1 to 10 hours. Predicting at 20 hours extrapolates far beyond the observed range, where the linear pattern may no longer hold.",
              "There are also practical limits: nobody can study 20 focused hours a week indefinitely, and the score cannot exceed 100%."],
     "ans": "Extrapolation beyond the data range (and beyond a realistic study week).",
     "mb": "1 mark for extrapolation · 1 mark for the explanation."},

    {"p": "(d)",
     "work": ["Gradient ≈ 2.9 (the task quotes 3.2): each additional hour of study per week is associated with about 3 percentage points more on the test.",
              "The intercept ≈ 7 is the predicted score for zero study hours."],
     "ans": "Each extra hour of weekly study predicts roughly +3 percentage points.",
     "mb": "1 mark for the correct direction/magnitude · 1 mark for context and units."},

    {"p": "(e)",
     "work": ["Possible confounders: prior attainment, attendance, the quality of teaching or of revision materials, home environment, motivation, sleep, or test anxiety.",
              "Any of these can raise both study time and score, so correlation does not prove that studying causes the higher score."],
     "ans": "e.g. prior attainment or attendance (affects both variables).",
     "mb": "1 mark for a valid variable · 1 mark for explaining the confounding effect · 1 mark for the causal caution."}
   ],
   "note": ("Note the internal inconsistency in the task: the plotted line is y = 2.9x + 7.0 while part (d) "
            "mentions 3.2. Both readings are accepted; the <i>interpretation</i> is what is marked.")
  },

  {
   "id": "D9", "title": "Coastal Navigation", "criteria": ["D", "C"],
   "diff": "Reasoning", "marks": 14,
   "stem": "A boat sails from A on bearing 040° for 30 km to B, then on bearing 115° for 40 km to C.",
   "parts": [
    {"p": "(a)",
     "work": ["The bearing of A from B is the reverse bearing: 040° + 180° = 220°.",
              "The bearing of C from B is 115°, measured clockwise from north at B.",
              "The interior angle between BA and BC is the difference:",
              "∠ABC = 220° − 115° = 105°"],
     "ans": "105° (back-bearing 220° minus bearing 115°)",
     "mb": "1 mark for the back-bearing · 1 mark for the difference · 1 mark for the conclusion."},

    {"p": "(b)",
     "work": ["Cosine rule, with AB = 30, BC = 40 and the included angle 105°:",
              "AC² = 30² + 40² − 2(30)(40)cos 105°",
              "= 900 + 1600 − 2400(−0.258819)",
              "= 2500 + 621.17 = 3121.17",
              "AC = 55.87"],
     "ans": "AC ≈ 56 km",
     "mb": "1 mark for the cosine rule · 1 mark for substitution · 1 mark for cos 105° = −0.2588 · 1 mark for the answer."},

    {"p": "(c)",
     "work": ["Use the sine rule to find the angle at A, then add the bearing of AB:",
              "sin A / 40 = sin 105° / 55.87  →  sin A = 40 × 0.9659/55.87 = 0.6916",
              "A = 43.8°",
              "Bearing of C from A = 040° + 43.8° = 83.8°.",
              "(Coordinate check: C is at (55.5, 6.1) from A, giving atan(55.5/6.1) ≈ 84°.)"],
     "ans": "Bearing ≈ 084°",
     "mb": "1 mark for the sine rule · 1 mark for the angle at A · 1 mark for adding the bearing · 1 mark for rounding."},

    {"p": "(d)",
     "work": ["Time = distance/speed = 55.87/18 = 3.1037 hours.",
              "0.1037 × 60 = 6.2 minutes."],
     "ans": "≈ 3 hours 6 minutes",
     "mb": "1 mark for the division · 1 mark for converting the decimal part · 1 mark for the answer in h and min."}
   ],
   "note": ("Always sketch and mark north lines at each point — the interior angle 105° comes from a "
            "back-bearing, which is where most marks are lost.")
  },

  {
   "id": "D10", "title": "Designing a Cone from a Sector", "criteria": ["D", "C"],
   "diff": "Extension Challenge", "marks": 15,
   "stem": "A cone is made from a sector of radius 8 cm and angle 70°.",
   "parts": [
    {"p": "(a)",
     "work": ["Arc length = (θ/360) × 2πr = (70/360) × 2π(8)",
              "= (7/36)(16π) = 28π/9"],
     "ans": "28π/9 ≈ 9.77 cm",
     "mb": "1 mark for the formula · 1 mark for substitution · 1 mark for the exact value."},

    {"p": "(b)",
     "work": ["The arc becomes the circumference of the cone's base:",
              "2πr(cone) = 28π/9  →  r = 14/9"],
     "ans": "r = 14/9 ≈ 1.56 cm",
     "mb": "1 mark for equating to 2πr · 2 marks for the value."},

    {"p": "(c)",
     "work": ["The sector radius becomes the slant height: l = 8.",
              "h² + r² = l²  →  h² = 64 − (14/9)² = 64 − 2.4198 = 61.5802",
              "h = 7.8473…"],
     "ans": "h ≈ 7.85 cm",
     "mb": "1 mark for Pythagoras · 1 mark for substitution · 1 mark for the value."},

    {"p": "(d)",
     "work": ["V = (1/3)πr²h = ⅓π(2.4198)(7.8473) = 19.885"],
     "ans": "V ≈ 19.9 cm³",
     "mb": "1 mark for the formula · 1 mark for substitution · 1 mark for the answer."},

    {"p": "(e)",
     "work": ["Let the sector angle be θ. Then r = 8θ/360 and h = √(64 − r²).",
              "V(θ) = (1/3)πr²h. Solve V(θ) = 150 by trial and refinement:",
              "θ = 200°: V ≈ 134 cm³;  θ = 215°: V ≈ 153 cm³;  θ = 212°: V ≈ 150 cm³.",
              "Refining gives θ ≈ 211.7°."],
     "ans": "θ ≈ 212°",
     "mb": "1 mark for the volume as a function of θ · 2 marks for a systematic search · 1 mark for θ ≈ 212° (accept 210°–213°)."}
   ],
   "note": ("Keep exact values (28π/9, 14/9) until the last step — rounding early is the main source of "
            "error in this type of task.")
  }
 ]
}
]
