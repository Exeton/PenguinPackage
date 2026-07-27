#Example Repos: Core, Extra, Multilib
import os

import urllib.request

import subprocess
import gzip
import shutil

from PenguinPackage.package import Package, Dependency, PackageList

from pathlib import Path

def download_arch_official_indexes(mirror_url:str, repos=["core", "extra"], operating_system="x86_64"):
    
    os.makedirs("arch_indexes", exist_ok= True)

    for repo in repos:
        download_url = mirror_url.replace("$repo", repo).replace("$arch", operating_system)
        final_url = download_url + f"/{repo}.db"

        print(f"Downloading index: {final_url}")
        urllib.request.urlretrieve(final_url, f"arch_indexes/{repo}.db")

        os.makedirs(f"arch_indexes/{repo}", exist_ok=True)

        result_2 = subprocess.run(["tar", "-xzf", f"{repo}.db", "-C", repo], cwd="arch_indexes")

        #shutil.unpack_archive(f"arch_indexes/{repo}.db", f"arch_indexes/repo")

#        with gzip.open(f"arch_indexes/{repo}.db") as gz:
#            with open(f"arch_indexes/{repo}", "wb") as out:
#                shutil.copyfileobj(gz, out)


def get_desc_as_dict(desc_contents: str) -> dict:
    
    desc_dict = {}
    key = ""
    values = []

    lines = desc_contents.split()

    for line in lines:
        if line.startswith("%") and line.endswith("%"):
            new_key = line[1:-1]
            #TODO: Throw if 0 and not first line
            if len(values) > 0:
                desc_dict[key] = values
                values = []
            key = new_key
        else:
            values.append(line)
    
    return desc_dict


def get_official_arch_packages() -> list[Package]:
    packages = []

    archive_folder = Path("arch_indexes")

    for database in archive_folder.iterdir():

        if not database.is_dir():
            continue

        for package_folder in database.iterdir():
            
            if not package_folder.is_dir():
                continue

            desc_file = package_folder / "desc"

            with open(desc_file, "r") as f:
                desc_contents = f.read()
                desc_dict = get_desc_as_dict(desc_contents)

                package = Package()

                package.name = desc_dict['NAME'][0]#Some packages, base doesn't work, for example there's glib c and glib c locales
                #package.name = desc_dict['BASE'][0]
                
                if 'FILENAME' in desc_dict:
                    package.download_path = desc_dict['FILENAME'][0]

                if 'DEPENDS' in desc_dict:
                    for dep in desc_dict['DEPENDS']:
                        dependency = Dependency(dep)
                        package.dependencies.append(dependency)

                if 'VERSION' in desc_dict:
                    package.version = desc_dict['VERSION'][0]

                package.source = f"arch_official/{database.stem}"

                #TODO: Add package download url

                packages.append(package)                

    return packages

def download_arch_package(package: Package, extract=True, overwrite=False):
    os.makedirs("arch_official_packages", exist_ok=True)

    pool_url = 'https://fastly.mirror.pkgbuild.com/pool/packages'
    final_url = f'{pool_url}/{package.download_path}'

    file_destination = f"arch_official_packages/{package.name}.tar.zst"


    if final_url == 'https://fastly.mirror.pkgbuild.com/pool/packages/binutils-2.46+r70+g155188ea10a7-1-x86_64.pkg.tar.zst':
        return

    if overwrite or os.path.isfile(file_destination) == False:
        #try:
        urllib.request.urlretrieve(final_url, file_destination)
        #except:
        #    if "systemd" not in final_url

    if extract:
        package_folder = f'arch_official_packages/{package.name}'

        os.makedirs(package_folder, exist_ok=True)
        result_2 = subprocess.run(["tar", "-I", "zstd", "-xf", file_destination, "-C", package_folder])
        return package_folder


    return file_destination


def install_all_arch_packages(packages_to_install: list[Package], all_packages: PackageList, install_path='', bypass_warning =False):
    if bypass_warning == False:
        raise "This is an expiremental feature and may break your system. Use only inside a sandboxed environment"

    os.makedirs(install_path, exist_ok=True)
    already_visited = []
    for package in packages_to_install:
        _install_arch_package_and_dependencies(package, all_packages, already_visited, install_path)



def install_arch_package(package: Package, all_packages: PackageList, install_path='', bypass_warning =False):
    if bypass_warning == False:
        raise "This is an expiremental feature and may break your system. Use only inside a sandboxed environment"

    os.makedirs(install_path, exist_ok=True)
    _install_arch_package_and_dependencies(package, all_packages, [], install_path)

def _install_arch_package_and_dependencies(package: Package, all_packages: PackageList, already_visited:list[str]=[], install_path=''):

    if package == None:
        return

    if package.name in already_visited:
        return
    
    already_visited.append(package.name)

    for dep in package.dependencies:

        #Arch packages can depend on themselves
        if package.name == dep.name:
            continue

        _install_arch_package_and_dependencies(all_packages.get_package(dep.name, throw_if_missing=False), all_packages, already_visited, install_path)


    install_single_package(package, install_path)

#Installs a package assuming its dependencies are already installed
def install_single_package(package: Package, installation_path=''):
    #Copy folder
    #Run installation script

    print(f"Installing package: {package.name}")

    if package.name == "binutils":
        return

    ignore=shutil.ignore_patterns('.BUILDINFO', '.MTREE', '.PKGINFO')

    folder = download_arch_package(package)

    if os.path.isfile(folder + '/.INSTALL'):
        print(f"Skipping install steps for: {package.name}. The package is located at {folder}")

    try:
        shutil.copytree(folder, installation_path, dirs_exist_ok=True, ignore=ignore, symlinks=True)
    except:
        print(f"Failed installing package: {package.name}. Skipping")
