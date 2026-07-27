Python library for handling multiple package formats on linux.

This library is still in development.

Usage (Apt packages)

``` python

from apt_packages import download_package_indexes, get_all_packages, download_package

download_package_indexes(get_system_package_repos())

all_packages = get_all_packages(
    path_to_indexes
)
print(len(all_packages))

python_canidates = [
    package for package in all_packages if "libpython3-all-dbg" in package.name
]

for canidate in python_canidates:
    print(canidate)

download_package(python_canidates[0], True)
```

Usage (Arch Package + Package List)

``` python
download_arch_official_indexes('https://fastly.mirror.pkgbuild.com/$repo/os/$arch')

official_packages = PackageList(get_official_arch_packages())
install_arch_package(official_packages.get_package("meson"), official_packages, 'test_directory', bypass_warning=True)
install_arch_package(official_packages.get_package("python"), official_packages, 'test_directory', bypass_warning=True)
install_arch_package(official_packages.get_package("bash"), official_packages, 'test_directory', bypass_warning=True)
```

Usage (AUR)
``` python
#download_aur_metadata()
#download_package("steam-native-runtime" )
#extract_packages_from_metadata()
```

Drawing Package Graph

``` python
from graph_drawing_utilities_graphviz import draw_graph_from_name_arch
draw_graph_from_name_arch("python")
```
