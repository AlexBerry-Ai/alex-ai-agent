"""
TernaryLogicGates Module v3.0
Logic gates and operations for ternary (3-state) systems.
States: -1 (negative/critical), 0 (neutral/ground), 1 (positive/optimal)
"""

from typing import List, Dict, Callable
import numpy as np


class TernaryLogicGates:
    """Collection of ternary logic gates for plant biosynthesis control."""

    @staticmethod
    def TERNARY_AND(a: int, b: int) -> int:
        """
        Ternary AND operation.
        Returns the minimum of the two values.
        """
        return min(a, b)

    @staticmethod
    def TERNARY_OR(a: int, b: int) -> int:
        """
        Ternary OR operation.
        Returns the maximum of the two values.
        """
        return max(a, b)

    @staticmethod
    def TERNARY_NOT(a: int) -> int:
        """
        Ternary NOT operation (negation).
        -1 -> 1, 0 -> 0, 1 -> -1
        """
        return -a

    @staticmethod
    def TERNARY_XOR(a: int, b: int) -> int:
        """
        Ternary XOR (exclusive OR).
        Returns difference, clamped to [-1, 0, 1]
        """
        result = a - b
        return np.clip(result, -1, 1)

    @staticmethod
    def TERNARY_MAJORITY(a: int, b: int, c: int) -> int:
        """
        Ternary majority gate.
        Returns the most frequent value among three inputs.
        """
        values = sorted([a, b, c])
        return values[1]  # Middle value

    @staticmethod
    def TERNARY_CONSENSUS(a: int, b: int, c: int) -> int:
        """
        Ternary consensus gate.
        Returns 0 if values differ, otherwise returns the common value.
        """
        if a == b == c:
            return a
        else:
            return 0

    @staticmethod
    def TERNARY_IMPLIES(a: int, b: int) -> int:
        """
        Ternary implication: a -> b
        Returns 1 if (a <= b), -1 if (a > b)
        """
        return 1 if a <= b else -1

    @staticmethod
    def TERNARY_THRESHOLD(value: int, lower: int, upper: int) -> int:
        """
        Ternary threshold gate.
        Returns -1 if value < lower, 1 if value > upper, 0 otherwise.
        """
        if value < lower:
            return -1
        elif value > upper:
            return 1
        else:
            return 0

    @staticmethod
    def TERNARY_NAND(a: int, b: int) -> int:
        """
        Ternary NAND: NOT(AND)
        """
        return -TernaryLogicGates.TERNARY_AND(a, b)

    @staticmethod
    def TERNARY_NOR(a: int, b: int) -> int:
        """
        Ternary NOR: NOT(OR)
        """
        return -TernaryLogicGates.TERNARY_OR(a, b)

    @staticmethod
    def TERNARY_BLEND(a: int, b: int, factor: float) -> int:
        """
        Blend two ternary values with a weighting factor (0.0 to 1.0).
        factor=0.0 returns a, factor=1.0 returns b
        """
        blended = a * (1 - factor) + b * factor
        return int(np.clip(blended, -1, 1))

    @staticmethod
    def TERNARY_ACCUMULATE(values: List[int], operation: str = 'and') -> int:
        """
        Accumulate multiple ternary values using a specified operation.
        
        Args:
            values: List of ternary values
            operation: 'and', 'or', 'majority', 'sum_clamp'
            
        Returns:
            The accumulated ternary value
        """
        if not values:
            return 0
        
        if operation == 'and':
            result = values[0]
            for v in values[1:]:
                result = TernaryLogicGates.TERNARY_AND(result, v)
            return result
        
        elif operation == 'or':
            result = values[0]
            for v in values[1:]:
                result = TernaryLogicGates.TERNARY_OR(result, v)
            return result
        
        elif operation == 'majority':
            counts = {-1: 0, 0: 0, 1: 0}
            for v in values:
                counts[v] += 1
            return max(counts, key=counts.get)
        
        elif operation == 'sum_clamp':
            return int(np.clip(sum(values), -1, 1))
        
        else:
            raise ValueError(f"Unknown operation: {operation}")

    @staticmethod
    def TERNARY_OSCILLATE(state: int, cycle_position: int, cycle_length: int) -> int:
        """
        Create oscillating ternary patterns useful for rhythmic biological processes.
        
        Args:
            state: Current ternary state
            cycle_position: Current position in the cycle (0 to cycle_length-1)
            cycle_length: Total length of the cycle
            
        Returns:
            Modulated ternary value
        """
        phase = (cycle_position / cycle_length) * 2 * np.pi
        modulation = np.sin(phase)
        
        if modulation > 0.5:
            return state
        elif modulation < -0.5:
            return -state
        else:
            return 0


class TernaryGateRegistry:
    """Registry for custom ternary gates and operations."""

    def __init__(self):
        self.gates: Dict[str, Callable] = {
            'AND': TernaryLogicGates.TERNARY_AND,
            'OR': TernaryLogicGates.TERNARY_OR,
            'NOT': TernaryLogicGates.TERNARY_NOT,
            'XOR': TernaryLogicGates.TERNARY_XOR,
            'MAJORITY': TernaryLogicGates.TERNARY_MAJORITY,
            'CONSENSUS': TernaryLogicGates.TERNARY_CONSENSUS,
            'IMPLIES': TernaryLogicGates.TERNARY_IMPLIES,
            'THRESHOLD': TernaryLogicGates.TERNARY_THRESHOLD,
            'NAND': TernaryLogicGates.TERNARY_NAND,
            'NOR': TernaryLogicGates.TERNARY_NOR,
            'BLEND': TernaryLogicGates.TERNARY_BLEND,
            'ACCUMULATE': TernaryLogicGates.TERNARY_ACCUMULATE,
            'OSCILLATE': TernaryLogicGates.TERNARY_OSCILLATE,
        }

    def register_gate(self, name: str, func: Callable) -> None:
        """Register a custom gate."""
        self.gates[name] = func

    def get_gate(self, name: str) -> Callable:
        """Retrieve a gate by name."""
        if name not in self.gates:
            raise KeyError(f"Gate '{name}' not found in registry")
        return self.gates[name]

    def list_gates(self) -> List[str]:
        """List all available gates."""
        return list(self.gates.keys())
