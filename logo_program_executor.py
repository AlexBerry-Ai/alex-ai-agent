"""
LogoProgramExecutor v3.0
Interpreter and executor for the LOGOALGORITHM DSL.
Processes plant mesh network commands and cube operations.
"""

from typing import Dict, List, Optional, Any
import re
from datetime import datetime
from qutrit_cube_storage import QutritCubeStorageArray
from logonery_module import LogoneryModule
from ternary_logic_gates import TernaryLogicGates


class LogoProgramExecutor:
    """Executes LOGOALGORITHM DSL programs."""

    def __init__(self, cube: QutritCubeStorageArray, logonery: LogoneryModule):
        """
        Initialize the executor.
        
        Args:
            cube: QutritCubeStorageArray instance for storage
            logonery: LogoneryModule instance for biosynthesis
        """
        self.cube = cube
        self.logonery = logonery
        self.variables: Dict[str, Any] = {}
        self.execution_log: List[str] = []
        self.pc = 0  # Program counter

    def run_script(self, script_text: str) -> None:
        """
        Parse and execute a LOGOALGORITHM script.
        
        Args:
            script_text: The DSL script as a string
        """
        print(f"\n[EXECUTOR] Starting LOGOALGORITHM execution at {datetime.now().strftime('%H:%M:%S')}")
        
        lines = script_text.strip().split('\n')
        self.pc = 0
        
        while self.pc < len(lines):
            line = lines[self.pc].strip()
            self.pc += 1
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            try:
                self._execute_instruction(line)
            except Exception as e:
                print(f"[ERROR] Line {self.pc}: {e}")
                self.execution_log.append(f"ERROR at line {self.pc}: {e}")
        
        print(f"[EXECUTOR] Execution completed at {datetime.now().strftime('%H:%M:%S')}")

    def _execute_instruction(self, instruction: str) -> Any:
        """
        Execute a single instruction from the DSL.
        
        Args:
            instruction: The instruction string
            
        Returns:
            Result of the instruction execution
        """
        # Parse command and arguments
        parts = instruction.split()
        if not parts:
            return
        
        command = parts[0].upper()
        args = parts[1:]
        
        # CUBE operations
        if command == 'SET':
            # SET x y z value
            if len(args) < 4:
                raise ValueError("SET requires 4 arguments: x y z value")
            x, y, z, val = int(args[0]), int(args[1]), int(args[2]), int(args[3])
            self.cube.set(x, y, z, val)
            print(f"  [CUBE] Set ({x},{y},{z}) = {val}")
        
        elif command == 'GET':
            # GET x y z
            if len(args) < 3:
                raise ValueError("GET requires 3 arguments: x y z")
            x, y, z = int(args[0]), int(args[1]), int(args[2])
            val = self.cube.get(x, y, z)
            print(f"  [CUBE] Get ({x},{y},{z}) = {val}")
            return val
        
        elif command == 'ROTATE':
            # ROTATE axis
            if len(args) < 1:
                raise ValueError("ROTATE requires axis: X, Y, or Z")
            axis = args[0].upper()
            if axis == 'X':
                self.cube.rotate_x()
            elif axis == 'Y':
                self.cube.rotate_y()
            elif axis == 'Z':
                self.cube.rotate_z()
            else:
                raise ValueError(f"Unknown rotation axis: {axis}")
            print(f"  [CUBE] Rotated {axis}")
        
        elif command == 'FLIP':
            # FLIP axis
            if len(args) < 1:
                raise ValueError("FLIP requires axis: X, Y, or Z")
            axis = args[0].upper()
            if axis == 'X':
                self.cube.flip_x()
            elif axis == 'Y':
                self.cube.flip_y()
            elif axis == 'Z':
                self.cube.flip_z()
            else:
                raise ValueError(f"Unknown flip axis: {axis}")
            print(f"  [CUBE] Flipped {axis}")
        
        elif command == 'RESET':
            self.cube.reset()
            print(f"  [CUBE] Reset to ground state")
        
        # LOGONERY operations
        elif command == 'SIGNAL':
            # SIGNAL signal_name state
            if len(args) < 2:
                raise ValueError("SIGNAL requires name and state")
            signal_name = args[0]
            state = int(args[1])
            self.logonery.emit_signal(signal_name, state)
        
        elif command == 'PATHWAY':
            # PATHWAY name gate1 gate2 ...
            if len(args) < 2:
                raise ValueError("PATHWAY requires name and at least one gate")
            pathway_name = args[0]
            gates = args[1:]
            self.logonery.register_pathway(pathway_name, gates)
        
        elif command == 'STRESS':
            # STRESS stress_type severity
            if len(args) < 2:
                raise ValueError("STRESS requires type and severity")
            stress_type = args[0]
            severity = int(args[1])
            responses = self.logonery.trigger_stress_response(stress_type, severity)
            print(f"  [STRESS] Triggered {stress_type} response: {responses}")
        
        elif command == 'LOGIC':
            # LOGIC gate_name arg1 arg2 ...
            if len(args) < 2:
                raise ValueError("LOGIC requires gate name and arguments")
            gate_name = args[0].upper()
            gate_args = [int(a) for a in args[1:]]
            gate = self.logonery.gate_registry.get_gate(gate_name)
            result = gate(*gate_args)
            print(f"  [LOGIC] {gate_name}({', '.join(map(str, gate_args))}) = {result}")
            return result
        
        elif command == 'VARIABLE':
            # VARIABLE var_name value
            if len(args) < 2:
                raise ValueError("VARIABLE requires name and value")
            var_name = args[0]
            try:
                value = int(args[1])
            except ValueError:
                value = ' '.join(args[1:])
            self.variables[var_name] = value
            print(f"  [VAR] {var_name} = {value}")
        
        elif command == 'PRINT':
            # PRINT message
            message = ' '.join(args)
            print(f"  [PRINT] {message}")
            self.execution_log.append(message)
        
        elif command == 'STATUS':
            # STATUS
            status = self.logonery.get_status_report()
            print(status)
        
        else:
            raise ValueError(f"Unknown command: {command}")

    def get_execution_log(self) -> List[str]:
        """Get the execution log."""
        return self.execution_log
