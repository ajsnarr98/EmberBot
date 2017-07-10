import pip

pipDependencyFilename = 'pip_dependencies'

def install():
    """ Installs any missing dependencies using pip """
    dependencies = get_pip_dependencies()

    if dependencies:
        for package in dependencies:
            try:
                pip.main(['install', package])
            except:
                pass

def get_pip_dependencies():
    """ Returns a list of pip modules to install """

    try:
        with open(pipDependencyFilename, 'r') as f:
            return f.readlines()
    except (FileNotFoundError, EOFError):
        return None
