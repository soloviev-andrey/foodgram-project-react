import pkg_resources

with open('requirements.txt') as f:
    requirements = [line.strip() for line in f]

installed_packages = [pkg.key for pkg in pkg_resources.working_set]

unused_packages = [pkg for pkg in requirements if pkg not in installed_packages]

print("Неиспользуемые пакеты:")
for pkg in unused_packages:
    print(pkg)
