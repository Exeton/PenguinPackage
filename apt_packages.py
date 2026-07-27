import os
import gzip

from pathlib import Path
from PenguinPackage.package import Package, PackageRepository, Dependency

import urllib.request
from urllib.parse import urljoin
import shutil

import subprocess

"""Gets the apt package repositories configured on the local system.

This checks /etc/apt/sources.list and /etc/apt/sources.list.d/
"""


def get_system_package_repos() -> list[PackageRepository]:

    repos: list[PackageRepository] = []

    for file in os.listdir("/etc/apt/sources.list.d/"):

        full_path = f"/etc/apt/sources.list.d/{file}"
        print(full_path)

        with open(full_path, "r") as sources_file:
            sources = sources_file.read().split("\n\n")
            for source in sources:

                repo = PackageRepository()

                lines = [line for line in source.split("\n") if ":" in line]
                key_values = [line.split(":", 1) for line in lines]

                if len(key_values) == 0:
                    continue

                for key_value in key_values:

                    key = key_value[0]
                    value = key_value[1].lstrip()

                    if key == "X-Repolib-Name":
                        repo.name = value
                    if key == "URIs":
                        repo.uri = value.split(" ")
                    if key == "Suites":
                        repo.suites = value.split(" ")
                    if key == "Components":
                        repo.components = value.split(" ")

                if repo.name == "":
                    repo.name = file
                repos.append(repo)
    return repos


def download_package_indexes(repos: list[PackageRepository]):

    for repo in repos:
        # Todo: Some uris are used as fallbacks, should all be downloaded?
        # Should fetch each combination of uri, suite, component?

        for component in repo.components:
            download_package_index(repo.uri[0], repo.suites[0], component)
    pass


def unzip_package_index(filename):

    input_path = Path(filename)

    output_directory = input_path.parent
    output_file = input_path.stem

    with gzip.open(filename) as gz:
        with open(output_directory / output_file, "wb") as out:
            shutil.copyfileobj(gz, out)


"""
Dist: The codename of the ubuntu distribution. (noble, jammy, etc.)
Component: (Main, etc.)

You can view sample indexes at /var/lib/apt/lists/ on debian systems
"""


def download_package_index(
    url, dist, component="main", architecture="amd64", output_folder="package_indexes"
):
    path = f"dists/{dist}/{component}/binary-{architecture}/Packages.gz"
    final_url = urljoin(url + "/", path)

    output_file_name = final_url.replace("https://", "").replace("http://", "")
    output_file_name = output_file_name.replace("/", "_")

    # TODO better path handling, for example if they include a / in their path
    output_path = output_folder + "/" + output_file_name

    os.makedirs(output_folder, exist_ok=True)

    urllib.request.urlretrieve(final_url, output_path)

    unzip_package_index(output_path)


"""When output name is none, it'll use whatever the default name would be when downloading with apt"""


def _download_package(
    repository_url, file_location, output_folder="debs", output_name=None, extract=False
):
    final_url: str = urljoin(repository_url, file_location)
    print(final_url)

    # TODO: Check what default package name would be when using apt

    if output_name == None:
        output_name = final_url.split("/")[-1]

    destination = str(Path(output_folder) / output_name)

    os.makedirs(output_folder, exist_ok=True)

    urllib.request.urlretrieve(final_url, destination)

    if extract:
        extract_package(destination)


def download_package(package: Package, extract=True):
    _download_package(
        "http://" + package.repo_url + "/", package.download_path, extract=extract
    )


def extract_dependencies(dependencies_str: str) -> list[Dependency]:

    result = []

    # Example dependencies_str: libc6 (>= 2.34), libcurl4t64 (>= 7.16.2), libmicrohttpd12t64 (>= 0.9.50)
    dependencies = dependencies_str.split(",")

    for dependency in dependencies:

        parts = dependency.lstrip().split(" (")
        new_dep = Dependency()
        new_dep.name = parts[0]

        if len(parts) > 1:
            version_parts = parts[1].split(" ")
            new_dep.version_comparator = version_parts[0]
            new_dep.version_data = version_parts[1][:-1]

        result.append(new_dep)

    return result


def extract_package_from_stanza(lines: list[str]) -> Package:

    mappings = {"Package": "name", "Version": "version", "Filename": "download_path"}

    mapping_keys = mappings.keys()

    package = Package()

    for line in lines:

        if line == "":
            continue

        if ":" not in line:
            continue  # TODO: Add suppourt ofr multiline fields like description

        first_colon_index = line.index(":")

        key_str = line[0:first_colon_index]

        key = key_str
        if key_str in mapping_keys:
            key = mappings[key_str]

        value = line[first_colon_index + 1 :].lstrip()

        if hasattr(package, key):
            setattr(package, key, value)

        if key == "Depends":
            package.dependencies = extract_dependencies(value)

    return package


def extract_packages_from_index_contents(file_contents: str, repo_url: str):
    #print(f"Content length: {len(file_contents)}")

    lines = file_contents.split("\n")
    #print(f"Total lines: {len(lines)}")

    current_package = []
    packages = []

    for line in lines:
        if line.startswith("Package") and len(current_package) > 0:
            package = extract_package_from_stanza(current_package)
            package.repo_url = repo_url
            packages.append(package)
            current_package = []

        current_package.append(line)

    return packages


def extract_packages_from_index(path):

    file_name = Path(path).name
    repo_url_parts = file_name.split("_")

    repo_url = f"{repo_url_parts[0]}/{repo_url_parts[1]}"

    with open(path) as f:
        return extract_packages_from_index_contents(f.read(), repo_url)


def get_all_packages(index_directory) -> list[Package]:

    all_packages = []
    for file in os.listdir(index_directory):

        if "Packages" not in Path(file).suffix:
            continue

        all_packages.extend(extract_packages_from_index(index_directory + "/" + file))

    return all_packages


def extract_package(path):

    # TODO: Switch off of using ar and to using pyunpack or a custom unzip implementation?

    path_obj = Path(path)
    deb_location = str(path_obj.absolute())

    file_name = path_obj.stem

    working_directory = path_obj.absolute().parent / file_name

    os.makedirs(working_directory, exist_ok=True)

    result = subprocess.run(["ar", "-x", deb_location], cwd=working_directory)
    print(result.stdout)
    print(result.returncode)
    print(result)

    deb_folder = Path(deb_location[:-4])

    control_file_zst = deb_folder / "control.tar.zst"
    control_file_xz = deb_folder / "control.tar.xz"
    data_file_zst = deb_folder / "data.tar.zst"
    data_file_xz = deb_folder / "data.tar.xz"

    control_folder = deb_folder / "control"
    data_folder = deb_folder / "data"

    os.makedirs(control_folder, exist_ok=True)
    os.makedirs(data_folder, exist_ok=True)


    if control_file_zst.exists():
        result_2 = subprocess.run(["tar", "-I", "zstd", "-xf", "control.tar.zst", "-C", "control"], cwd=deb_folder)
    elif control_file_xz.exists():
        result_2 = subprocess.run(["tar", "-I", "xz", "-xf", "control.tar.xz", "-C", "control"], cwd=deb_folder)

    if data_file_zst.exists():
        result_3 = subprocess.run(["tar", "-I", "zstd", "-xf", "data.tar.zst", "-C", "data"], cwd=deb_folder)
    elif data_file_xz.exists():
        result_3 = subprocess.run(["tar", "-I", "xz", "-xf", "data.tar.xz", "-C", "data"], cwd=deb_folder)