#Typically the AUR is queried over the web
# This will dowload the metadata to reduce load on the aur

#AUR https://wiki.archlinux.org/title/Aurweb_RPC_interface

import os
import urllib.request
from urllib.parse import urljoin
import gzip
import shutil
import json

from PenguinPackage.package import Package, Dependency

#TODO: Require GitPython
from git import Repo

def download_aur_metadata(overwrite=False):
    metadata_location = "https://aur.archlinux.org/packages-meta-v1.json.gz"

    #TODO: Update to use extended version

    output_path = "aur/metadata.json.gz"
    os.makedirs("aur", exist_ok=True)

    if os.path.exists(output_path) == False:
        print("Redownloading AUR metadata")
        urllib.request.urlretrieve(metadata_location, output_path)

    with gzip.open(output_path) as gz:
        with open("aur/metadata.json", "wb") as out:
            shutil.copyfileobj(gz, out)
            #TODO: Fix
    
    with open("aur/metadata.json") as file:
        data = json.load(file)

    
def download_package(package_base):

    dest = f"aur/{package_base}"

    os.makedirs(f"aur/{package_base}", exist_ok=True)
    Repo.clone_from(f"https://aur.archlinux.org/{package_base}.git", dest)


def extract_packages_from_metadata() -> list[Package]:
    
    packages = []

    with open('aur/packages-meta-ext-v1.json') as f:
        data = json.load(f)
        for entry in data:
            package = Package()
            package.version = entry['Version']
            package.name = entry['PackageBase']
            package.download_path = f"https://aur.archlinux.org/{entry['PackageBase']}.git"
            
            dependencies = []

            if 'Depends' in entry:
                for dep in entry['Depends']:
                    dependency = Dependency()
                    dependency.name = dep
                    dependencies.append(dependency)
                package.dependencies = dependencies

            packages.append(package)

    return packages



