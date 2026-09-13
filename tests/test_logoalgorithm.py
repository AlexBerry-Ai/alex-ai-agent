# Testing framework for LOGOALGORITHM
import pytest
from qutrit_cube_storage import QutritCubeStorageArray
from logonery_module import LogoneryModule
from ternary_logic_gates import TernaryLogicGates
from logo_program_executor import LogoProgramExecutor


class TestQutritCubeStorage:
    def test_set_and_get(self):
        cube = QutritCubeStorageArray(size=3)
        cube.set(0, 0, 0, 1)
        assert cube.get(0, 0, 0) == 1

    def test_bounds_check(self):
        cube = QutritCubeStorageArray(size=3)
        with pytest.raises(IndexError):
            cube.set(5, 5, 5, 1)

    def test_reset(self):
        cube = QutritCubeStorageArray(size=3)
        cube.set(1, 1, 1, 2)
        cube.reset()
        assert cube.get(1, 1, 1) == 0

    def test_rotation(self):
        cube = QutritCubeStorageArray(size=3)
        cube.set(0, 0, 0, 1)
        cube.rotate_x()
        # After rotation, state should be preserved (rotated)
        assert len(cube.history) > 0


class TestTernaryLogicGates:
    def test_and_gate(self):
        assert TernaryLogicGates.TERNARY_AND(1, 1) == 1
        assert TernaryLogicGates.TERNARY_AND(1, 0) == 0
        assert TernaryLogicGates.TERNARY_AND(1, -1) == -1

    def test_or_gate(self):
        assert TernaryLogicGates.TERNARY_OR(1, 1) == 1
        assert TernaryLogicGates.TERNARY_OR(1, -1) == 1
        assert TernaryLogicGates.TERNARY_OR(-1, -1) == -1

    def test_not_gate(self):
        assert TernaryLogicGates.TERNARY_NOT(1) == -1
        assert TernaryLogicGates.TERNARY_NOT(0) == 0
        assert TernaryLogicGates.TERNARY_NOT(-1) == 1

    def test_majority_gate(self):
        assert TernaryLogicGates.TERNARY_MAJORITY(1, 1, -1) == 0  # Middle value
        assert TernaryLogicGates.TERNARY_MAJORITY(1, 1, 1) == 1


class TestLogoneryModule:
    def test_signal_emission(self):
        logonery = LogoneryModule(cube_size=3)
        logonery.emit_signal("test_signal", 1)
        assert logonery.chemical_signals["test_signal"] == 1

    def test_stress_response(self):
        logonery = LogoneryModule(cube_size=3)
        responses = logonery.trigger_stress_response("drought", 1)
        assert "aba_synthesis" in responses

    def test_pathway_registration(self):
        logonery = LogoneryModule(cube_size=3)
        logonery.register_pathway("test_path", ["AND", "OR"])
        assert "test_path" in logonery.biosynthesis_pathways


class TestLogoExecutor:
    def test_set_command(self, capsys):
        cube = QutritCubeStorageArray(size=3)
        logonery = LogoneryModule(cube_size=3)
        executor = LogoProgramExecutor(cube, logonery)
        
        executor._execute_instruction("SET 0 0 0 1")
        assert cube.get(0, 0, 0) == 1

    def test_signal_command(self):
        cube = QutritCubeStorageArray(size=3)
        logonery = LogoneryModule(cube_size=3)
        executor = LogoProgramExecutor(cube, logonery)
        
        executor._execute_instruction("SIGNAL test 1")
        assert logonery.chemical_signals["test"] == 1

    def test_variable_command(self):
        cube = QutritCubeStorageArray(size=3)
        logonery = LogoneryModule(cube_size=3)
        executor = LogoProgramExecutor(cube, logonery)
        
        executor._execute_instruction("VARIABLE x 42")
        assert executor.variables["x"] == 42
