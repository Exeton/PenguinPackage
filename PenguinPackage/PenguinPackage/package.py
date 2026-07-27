import re

class Dependency:
    version_comparator = ""
    version_data = ""
    name: str
    source: str

    def __init__(self, package_str=None):
        #Split package string on equality operators: <>=, etc

        if package_str == None:
            return

        comparison_operators = ['<', '>', '=']

        name_builder = ''
        version_builder = ''
        comparison_builder = ''

        before_comparison = True
        in_comparison = True

        for char in package_str:

            if char in comparison_operators:
                if before_comparison:
                    before_comparison = False
                    in_comparison = True
            
            if char not in comparison_operators and in_comparison:
                in_comparison = False

            if before_comparison:
                name_builder += char
            elif in_comparison:
                comparison_builder += char
            else:
                version_builder += char

        self.version_comparator = comparison_builder
        self.version_data = version_builder
        self.name = name_builder

                




class Package:
    version = ""
    name = ""
    dependencies : list[Dependency]
    source = "" #Deb, rpm, aur, etc.

    #TODO: Is this bad pratice?
    repo_url = ""

    download_path = ""

    def __init__(self):
        self.dependencies = []
 

    def __str__(self):
        return f"{self.name} {self.source} v{self.version}"


class PackageRepository:
    """This will be the name listed in the sources file under X-Repolib-Name. Falls back to the file name"""
    name: str = ""
    uri: list[str] #List of strs?
    suites: list[str]
    components: list[str]

    def __str__(self):
        return f"Repository {self.name}"


class PackageList:
    packages: list[Package]

    def __init__(self, _packages):
        self.packages = _packages
    
    def get_all_packages(self, name, throw_if_missing=True):
        matches = [package for package in self.packages if package.name.lower() == name.lower()]

        if len(matches) == 0:
            if throw_if_missing:
                #TODO: Add did you mean <similar_package>?
                raise ValueError(f"No match for package {name}")
            else:
                print(f"No package found: {name}")
            return []
        
        return matches


    def get_package(self, name, throw_if_missing=True):

        if "systemd" == name:
            print("Sysd")

        matches = self.get_all_packages(name, throw_if_missing)
        if len(matches) == 0:
            return None

        highest_package = None
        highest_version = "0.0.0.0"
        if len(matches) > 1:
            for match in matches:
                if self.is_version_a_greater_or_equal(match.version, highest_version):
                    highest_package = match
                    highest_version = match.version
            return highest_package

        return matches[0]



    #TODO: Account for more complex versions. Example: '2.43+r22+g8362e8ce10b2-2'
    def is_version_a_greater_or_equal(self, version_a: str, version_b: str):

        #Remove all none numeric and -,+,. characters?

        #split_chars = [".", '-']

        split_regex = r"[.-]"

        parts_a = re.split(split_regex, version_a)
        parts_b = re.split(split_regex, version_b)

        #parts_a = version_a.split(split_chars)
        #parts_b = version_b.split(split_chars)

        for i in range(min(len(parts_a), len(parts_b))):
            if parts_a[i] > parts_b[i]:
                return True
            if parts_b[i] > parts_a[i]:
                return False
        
        #Consider version 1.0.0 to be >= 1.0
        return len(parts_a) >= len(parts_b)
