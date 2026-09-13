"""
QutritCubeStorageArray Module v3.0
Stores and manages data in a 3D cube using qutrit (3-state quantum) logic.
Each cell can hold values 0, 1, or 2 (ternary/trinary states).
"""

from typing import Tuple, List, Optional
import numpy as np


class QutritCubeStorageArray:
    """
    A 3D cube storage array using qutrit (3-state) logic.
    Each cell in the cube can hold a value of 0, 1, or 2.
    """

    def __init__(self, size: int = 3):
        """
        Initialize the qutrit cube.
        
        Args:
            size: Dimensions of the cube (size x size x size)
        """
        if size < 1:
            raise ValueError("Cube size must be at least 1")
        
        self.size = size
        # Initialize cube with all zeros (ground state)
        self.cube = np.zeros((size, size, size), dtype=np.int8)
        self.history = []  # Track state changes for debugging

    def set(self, x: int, y: int, z: int, value: int) -> None:
        """
        Set a qutrit value at position (x, y, z).
        
        Args:
            x, y, z: Coordinates in the cube
            value: Qutrit value (0, 1, or 2)
            
        Raises:
            ValueError: If value is not 0, 1, or 2
            IndexError: If coordinates are out of bounds
        """
        if value not in [0, 1, 2]:
            raise ValueError(f"Qutrit value must be 0, 1, or 2, got {value}")
        
        if not self._in_bounds(x, y, z):
            raise IndexError(f"Coordinates ({x}, {y}, {z}) out of bounds for cube size {self.size}")
        
        old_value = self.cube[x, y, z]
        self.cube[x, y, z] = value
        self.history.append({"pos": (x, y, z), "old": old_value, "new": value})

    def get(self, x: int, y: int, z: int) -> int:
        """
        Get the qutrit value at position (x, y, z).
        
        Args:
            x, y, z: Coordinates in the cube
            
        Returns:
            The qutrit value (0, 1, or 2)
            
        Raises:
            IndexError: If coordinates are out of bounds
        """
        if not self._in_bounds(x, y, z):
            raise IndexError(f"Coordinates ({x}, {y}, {z}) out of bounds for cube size {self.size}")
        
        return int(self.cube[x, y, z])

    def rotate_x(self) -> None:
        """Rotate the cube around the X-axis."""
        self.cube = np.rot90(self.cube, axes=(1, 2))
        self.history.append({"operation": "rotate_x"})

    def rotate_y(self) -> None:
        """Rotate the cube around the Y-axis."""
        self.cube = np.rot90(self.cube, axes=(0, 2))
        self.history.append({"operation": "rotate_y"})

    def rotate_z(self) -> None:
        """Rotate the cube around the Z-axis."""
        self.cube = np.rot90(self.cube, axes=(0, 1))
        self.history.append({"operation": "rotate_z"})

    def flip_x(self) -> None:
        """Flip the cube along the X-axis."""
        self.cube = np.flip(self.cube, axis=0)
        self.history.append({"operation": "flip_x"})

    def flip_y(self) -> None:
        """Flip the cube along the Y-axis."""
        self.cube = np.flip(self.cube, axis=1)
        self.history.append({"operation": "flip_y"})

    def flip_z(self) -> None:
        """Flip the cube along the Z-axis."""
        self.cube = np.flip(self.cube, axis=2)
        self.history.append({"operation": "flip_z"})

    def get_slice(self, axis: str, index: int) -> np.ndarray:
        """
        Get a 2D slice of the cube.
        
        Args:
            axis: 'x', 'y', or 'z'
            index: Position along the axis
            
        Returns:
            A 2D numpy array representing the slice
        """
        if axis == 'x':
            return self.cube[index, :, :]
        elif axis == 'y':
            return self.cube[:, index, :]
        elif axis == 'z':
            return self.cube[:, :, index]
        else:
            raise ValueError("Axis must be 'x', 'y', or 'z'")

    def reset(self) -> None:
        """Reset all cells to 0 (ground state)."""
        self.cube = np.zeros((self.size, self.size, self.size), dtype=np.int8)
        self.history.append({"operation": "reset"})

    def get_state(self) -> np.ndarray:
        """Get a copy of the current cube state."""
        return self.cube.copy()

    def set_state(self, state: np.ndarray) -> None:
        """Set the cube to a specific state."""
        if state.shape != (self.size, self.size, self.size):
            raise ValueError(f"State shape must be ({self.size}, {self.size}, {self.size})")
        self.cube = state.astype(np.int8)
        self.history.append({"operation": "set_state"})

    def count_states(self, value: int) -> int:
        """Count how many cells contain a specific qutrit value."""
        return int(np.sum(self.cube == value))

    def _in_bounds(self, x: int, y: int, z: int) -> bool:
        """Check if coordinates are within bounds."""
        return 0 <= x < self.size and 0 <= y < self.size and 0 <= z < self.size

    def __repr__(self) -> str:
        return f"QutritCubeStorageArray(size={self.size})"

    def __str__(self) -> str:
        """Print a simple representation of the cube."""
        lines = [f"QutritCubeStorageArray (size={self.size})"]
        lines.append(f"State counts: 0s={self.count_states(0)}, 1s={self.count_states(1)}, 2s={self.count_states(2)}")
        return "\n".join(lines)
