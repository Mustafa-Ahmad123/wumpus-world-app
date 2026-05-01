"""
logic_engine.py
───────────────
Propositional Logic Knowledge Base and Resolution Refutation Engine
for the Wumpus World agent.

Literals are represented as strings:
  "P_2_3"     → Pit at grid (row=2, col=3)
  "NEG_P_2_3" → No pit at (2,3)
  "W_2_3"     → Wumpus at (2,3)
  "NEG_W_2_3" → No wumpus at (2,3)
  "B_2_3"     → Breeze at (2,3)
  "NEG_B_2_3" → No breeze at (2,3)
  etc.

Clauses are lists of literal strings (CNF disjunctions).
The KB is a set of such clauses.
"""

from __future__ import annotations
from typing import List, Set, Tuple, Optional
import copy


# ─── LITERAL UTILITIES ───────────────────────────────────────────────────────

def negate(literal: str) -> str:
    """Return the negation of a literal."""
    if literal.startswith("NEG_"):
        return literal[4:]
    return "NEG_" + literal


def is_tautology(clause: List[str]) -> bool:
    """Return True if a clause contains both a literal and its negation."""
    lits = set(clause)
    for lit in lits:
        if negate(lit) in lits:
            return True
    return False


def resolve(clause_a: List[str], clause_b: List[str]) -> Optional[List[str]]:
    """
    Try to resolve two clauses on one complementary pair.
    Returns the resolvent (deduplicated), or None if no resolution is possible
    or the resolvent is a tautology.
    """
    for lit in clause_a:
        neg = negate(lit)
        if neg in clause_b:
            # Resolve on lit / neg
            new_clause = list(set(clause_a) - {lit}) | list(set(clause_b) - {neg})
            # Deduplicate
            new_clause = list(dict.fromkeys(new_clause))
            if is_tautology(new_clause):
                return None
            return new_clause
    return None


# ─── KNOWLEDGE BASE ──────────────────────────────────────────────────────────

class WumpusKB:
    """
    Propositional Knowledge Base for the Wumpus World.

    Internal representation: a list of CNF clauses.
    Each clause is a frozenset of literal strings.
    We store as list[list[str]] for mutability during inference.
    """

    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.clauses: List[List[str]] = []

        # Axiom: start cell is safe (no pit, no wumpus)
        self.add_clause([f"NEG_P_{rows-1}_0"])
        self.add_clause([f"NEG_W_{rows-1}_0"])

    # ── Public TELL interface ─────────────────────────────────────────────────

    def add_clause(self, clause: List[str]):
        """Add a CNF clause to the KB (skip duplicates and tautologies)."""
        clause = list(dict.fromkeys(clause))          # deduplicate
        if is_tautology(clause):
            return
        fs = frozenset(clause)
        if not any(frozenset(c) == fs for c in self.clauses):
            self.clauses.append(clause)

    def tell_breeze(self, r: int, c: int):
        """Agent perceives breeze at (r,c) → pit in at least one neighbor."""
        adj = self._adj(r, c)
        # Biconditional encoded as:
        #   B_r_c → (P_n1 ∨ P_n2 ∨ …)
        self.add_clause([f"B_{r}_{c}"])
        if adj:
            self.add_clause([f"P_{ar}_{ac}" for ar, ac in adj])

    def tell_no_breeze(self, r: int, c: int):
        """No breeze at (r,c) → no pit in any neighbor."""
        self.add_clause([f"NEG_B_{r}_{c}"])
        for ar, ac in self._adj(r, c):
            self.add_clause([f"NEG_P_{ar}_{ac}"])

    def tell_stench(self, r: int, c: int):
        """Agent perceives stench at (r,c) → wumpus in at least one neighbor."""
        adj = self._adj(r, c)
        self.add_clause([f"S_{r}_{c}"])
        if adj:
            self.add_clause([f"W_{ar}_{ac}" for ar, ac in adj])

    def tell_no_stench(self, r: int, c: int):
        """No stench at (r,c) → no wumpus in any neighbor."""
        self.add_clause([f"NEG_S_{r}_{c}"])
        for ar, ac in self._adj(r, c):
            self.add_clause([f"NEG_W_{ar}_{ac}"])

    def tell_safe(self, r: int, c: int):
        """Mark a cell as confirmed safe."""
        self.add_clause([f"NEG_P_{r}_{c}"])
        self.add_clause([f"NEG_W_{r}_{c}"])

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _adj(self, r: int, c: int) -> List[Tuple[int, int]]:
        return [(ar, ac)
                for ar, ac in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
                if 0 <= ar < self.rows and 0 <= ac < self.cols]

    def snapshot(self) -> List[List[str]]:
        """Return a deep copy of all clauses (for use in refutation)."""
        return [list(cl) for cl in self.clauses]


# ─── RESOLUTION REFUTATION ENGINE ────────────────────────────────────────────

class ResolutionEngine:
    """
    Implements Resolution Refutation (proof by contradiction) in CNF.

    To prove α:
      1. Add ¬α to the KB copy.
      2. Apply resolution repeatedly.
      3. If the empty clause is derived → contradiction → α is proved.

    Uses unit propagation first (fast), then full pairwise resolution (complete).
    """

    def __init__(self, kb: WumpusKB):
        self.kb = kb
        self.steps = 0          # cumulative inference step counter

    def resolution_refutation(self, goal: str) -> bool:
        """
        Try to prove 'goal' by refutation.
        Returns True if goal is entailed by the KB, False otherwise.
        """
        # Negate the goal and add to a working copy of the KB
        clauses = self.kb.snapshot()
        clauses.append([negate(goal)])

        result, steps = self._resolve(clauses)
        self.steps += steps
        return result

    # ── Internal resolution loop ──────────────────────────────────────────────

    def _resolve(self, clauses: List[List[str]]) -> Tuple[bool, int]:
        """
        Full resolution procedure.
        Returns (contradiction_found, steps_taken).
        """
        steps = 0
        MAX_STEPS = 500        # safety cap

        # Phase 1 — Unit propagation (fast O(n))
        changed = True
        while changed and steps < MAX_STEPS:
            changed, clauses, contradiction = self._unit_propagate(clauses)
            steps += 1
            if contradiction:
                return True, steps

        # Phase 2 — Pairwise resolution (complete but slower)
        seen: Set[frozenset] = {frozenset(c) for c in clauses}

        while steps < MAX_STEPS:
            new_resolvents: List[List[str]] = []
            n = len(clauses)
            found_new = False

            for i in range(n):
                for j in range(i + 1, n):
                    resolvent = resolve(clauses[i], clauses[j])
                    if resolvent is None:
                        continue
                    if len(resolvent) == 0:
                        # Empty clause = contradiction
                        return True, steps + 1
                    fs = frozenset(resolvent)
                    if fs not in seen:
                        seen.add(fs)
                        new_resolvents.append(resolvent)
                        found_new = True
                    steps += 1
                    if steps >= MAX_STEPS:
                        break
                if steps >= MAX_STEPS:
                    break

            if not found_new:
                # No new clauses generated → goal not provable
                return False, steps

            clauses.extend(new_resolvents)

            # Run unit propagation on the expanded set
            changed = True
            while changed and steps < MAX_STEPS:
                changed, clauses, contradiction = self._unit_propagate(clauses)
                steps += 1
                if contradiction:
                    return True, steps

        return False, steps

    @staticmethod
    def _unit_propagate(
        clauses: List[List[str]],
    ) -> Tuple[bool, List[List[str]], bool]:
        """
        One pass of unit propagation.
        Returns (changed, new_clauses, contradiction_found).
        """
        units = [c[0] for c in clauses if len(c) == 1]
        if not units:
            return False, clauses, False

        changed = False
        for u in units:
            neg_u = negate(u)
            new_clauses = []
            for cl in clauses:
                if u in cl:
                    # Clause is satisfied → remove it
                    changed = True
                    continue
                if neg_u in cl:
                    # Shorten clause by removing neg_u
                    shortened = [lit for lit in cl if lit != neg_u]
                    if len(shortened) == 0:
                        return True, [], True   # Empty clause = contradiction
                    new_clauses.append(shortened)
                    changed = True
                else:
                    new_clauses.append(cl)
            clauses = new_clauses

        return changed, clauses, False


# ─── CONVENIENCE: CNF DISPLAY ────────────────────────────────────────────────

def clause_to_str(clause: List[str], rows: int) -> str:
    """
    Convert an internal clause list to a human-readable CNF string,
    using display coordinates (row counting from bottom, col from 1).
    """
    parts = []
    for lit in clause:
        neg = lit.startswith("NEG_")
        base = lit[4:] if neg else lit
        tokens = base.split("_")
        prefix = tokens[0]          # P, W, B, S, …
        if len(tokens) == 3:
            r, c = int(tokens[1]), int(tokens[2])
            display = f"{prefix}_{rows - r},{c + 1}"
        else:
            display = base
        parts.append(("¬" if neg else "") + display)
    return " ∨ ".join(parts)