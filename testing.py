import pkg_resources

dependencies = [
    'discord',
    'discord.py',
    'python-dotenv'
]

def check_dependency_versions():
    for dependency in dependencies:
        try:
            version = pkg_resources.get_distribution(dependency).version
            print(f"{dependency}: {version}")
        except pkg_resources.DistributionNotFound:
            print(f"{dependency}: Not installed")

check_dependency_versions()

