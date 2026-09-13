import sys
from pathlib import Path

# ---------------------------------------------------------
# LOGOALGORITHM v3.0 Launcher
# Imports all biosynthesis and ternary logic modules
# ---------------------------------------------------------

from qutrit_cube_storage import QutritCubeStorageArray
from logonery_module import LogoneryModule
from logo_program_executor import LogoProgramExecutor
from plant_mesh_network import PlantMeshNetworkController, PlantMeshNode
from ternary_logic_gates import TernaryLogicGates


def main():
    if len(sys.argv) < 2:
        print("Utilizare: python logo_launcher.py <fisier.logo>")
        print("\nExample usage:")
        print("  python logo_launcher.py script.logo")
        return

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Eroare: fișierul {file_path} nu există.")
        return

    # Inițializează cubul și modulul de biosinteză
    cube = QutritCubeStorageArray(size=3)
    logonery = LogoneryModule(cube_size=3)
    executor = LogoProgramExecutor(cube, logonery)

    # Citește DSL-ul
    script_text = file_path.read_text(encoding="utf-8")

    print(f"[Launcher] Rulează scriptul LOGOALGORITHM: {file_path}")
    print(f"[Launcher] Versiune: 3.0 (cu suport mesh network și logică ternară)")
    print("="*75)
    
    executor.run_script(script_text)

    print(f"[Launcher] Execuție finalizată.")


if __name__ == "__main__":
    main()
