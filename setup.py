
import subprocess
from setuptools import setup

requirements = ["pandas==2.2.2",
                "python-terrier",
                "googlesearch-python",
                "PyPDF2",
                "git+https://github.com/emory-irlab/pyterrier_genrank.git",
                "python-dotenv",
                "numpy==1.26.4"
                ]
def create_conda_env(env_name):
    """Creates a Conda environment and installs pip requirements."""
    try:
        # Step 1: Check if Conda is installed
        subprocess.run(["conda", "--version"], check=True)

        # Step 2: Create the Conda environment
        print(f"Creating Conda environment: {env_name}")
        subprocess.run(["conda", "create", "-y", "-n", env_name, "python=3.10"], check=True)

        env_python_path = subprocess.run(
            ["conda", "run", "-n", env_name, "which", "python"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        subprocess.run(
            [env_python_path, "-m", "pip", "install"] + requirements,
            check=True,
        )
        print(f"Environment {env_name} created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during setup: {e}")
        exit(1)


if __name__ == "__main__":
    env_name = "conqret-rag"  # Replace with your desired Conda environment name
    create_conda_env(env_name)