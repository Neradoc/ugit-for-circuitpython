# ugit
# micropython OTA update from github
# Created by TURFPTAx for the openmuscle project
# Check out https://openmuscle.org for more info
#
# Pulls files and folders from open github repository

import os
import json
import hashlib
import binascii
import microcontroller
import time

#### -------------User Variables----------------####
# Don't remove ugit.py from the ignore_files unless you know what you are doing :D
# Put the files you don't want deleted or updated here use '/filename.ext'
IGNORE_FILES = [
    "/ugit.py",
    "/.Trashes",
    "/.fseventsd",
    "/.metadata_never_index",
    "/boot_out.txt",
    "/settings.toml",
]
### -----------END OF USER VARIABLES ----------####

# Static URLS
# GitHub uses 'main' instead of master for python repository trees
giturl = "https://github.com/{user}/{repository}"
URL_CALL_TREES = (
    "https://api.github.com/repos/{user}/{repository}/git/trees/main?recursive=1"
)
URL_RAW = "https://raw.githubusercontent.com/{user}/{repository}/master/"

IS_DIR = 0x4000
IS_FILE = 0x8000

def is_dir(file):
    return os.stat(file)[0] & IS_DIR != 0

def remove_item(item, tree):
    culled = []
    for i in tree:
        if item not in i:
            culled.append(i)
    return culled

def get_hash(file):
    with open(file, "rb") as o_file:
        r_file = o_file.read()
        sha1obj = hashlib.new("sha1", r_file)
        hash = sha1obj.digest()
        return binascii.hexlify(hash)


class UGit:
    def __init__(self, requests, user, repository, token="", ignore=(), base="/"):
        self.internal_tree = []
        self.user = user
        self.repository = repository
        self.token = token
        self.ignore = []
        self.ignore.extend(IGNORE_FILES)
        self.ignore.extend(ignore)
        self.base = "/" + base.strip("/")
        self.requests = requests

    def pull(f_path, raw_url):
        print(f"pulling {f_path} from github")
        # files = os.listdir()
        headers = {"User-Agent": "ugit-turfptax"}
        # ^^^ Github Requires user-agent header otherwise 403
        if len(self.token) > 0:
            headers["authorization"] = "bearer %s" % self.token
        r = self.requests.get(raw_url, headers=headers)
        try:
            with open(f_path, "wb") as new_file:
                new_file.write(r.content)
        except:
            print("decode fail try adding non-code files to .gitignore")
            try:
                new_file.close()
            except:
                print("tried to close new_file to save memory durring raw file decode")

    def pull_all(self):
        raw = URL_RAW.format(user=self.user, repository=self.repository)
        tree = self.pull_git_tree()
        self.build_internal_tree()
        self.remove_ignore()
        print(" ignore removed ----------------------")
        print(self.internal_tree)
        log = []
        # download and save all files
        for i in tree["tree"]:
            if i["type"] == "tree":
                try:
                    os.mkdir(i["path"])
                except:
                    print(f'failed to {i["path"]} dir may already exist')
            elif i["path"] not in self.ignore:
                try:
                    os.remove(i["path"])
                    log.append(f'{i["path"]} file removed from int mem')
                    self.internal_tree = remove_item(i["path"], self.internal_tree)
                except:
                    log.append(f'{i["path"]} del failed from int mem')
                    print("failed to delete old file")
                try:
                    pull(i["path"], raw + i["path"])
                    log.append(i["path"] + " updated")
                except:
                    log.append(i["path"] + " failed to pull")
        # delete files not in Github tree
        if len(self.internal_tree) > 0:
            print(self.internal_tree, " leftover!")
            for i in self.internal_tree:
                try:
                    os.remove(i)
                    log.append(i + " removed from int mem")
                except OSError:
                    log.append(i + " skipped, Read-only filesystem")
        try:
            with open("ugit_log.log", "w") as logfile:
                logfile.write("\n".join(log))
        except OSError:
            print("\n".join(log))
        print("You can now reset")
        # return check instead return with global

    def build_internal_tree(self):
        self.internal_tree = []
        for dir_item in os.listdir(self.base):
            item_path = (self.base + "/" + dir_item).replace("//", "/")
            self.add_to_tree(item_path)

    def add_to_tree(self, dir_item):
        if is_dir(dir_item):
            if len(os.listdir(dir_item)) >= 1:
                for sub_item in os.listdir(dir_item):
                    sub_path = dir_item + "/" + sub_item
                    self.add_to_tree(sub_path)
        else:
            try:
                print(f"sub path: {dir_item}")
                self.internal_tree.append([dir_item, get_hash(dir_item)])
            except OSError as er:
                print(f"{dir_item} could not be added to tree")

    def pull_git_tree(self):
        tree_url = URL_CALL_TREES.format(user=self.user, repository=self.repository)
        headers = {"User-Agent": "ugit-turfptax"}
        # ^^^ Github Requires user-agent header otherwise 403
        if len(self.token) > 0:
            headers["authorization"] = "bearer %s" % self.token
        r = self.requests.get(tree_url, headers=headers)
        tree = json.loads(r.content.decode("utf-8"))
        return tree

    def parse_git_tree(self):
        tree = self.pull_git_tree()
        dirs = []
        files = []
        for i in tree["tree"]:
            if i["type"] == "tree":
                dirs.append(i["path"])
            if i["type"] == "blob":
                files.append([i["path"], i["sha"], i["mode"]])
        print("dirs:", dirs)
        print("files:", files)

    def check_ignore(self):
        tree = self.pull_git_tree()
        check = []
        # download and save all files
        for i in tree["tree"]:
            if i["path"] not in self.ignore:
                print(i["path"] + " not in ignore")
            if i["path"] in self.ignore:
                print(i["path"] + " is in ignore")

    def remove_ignore(self):
        print("-"*70)
        print(self.internal_tree)
        print("-"*70)
        clean_tree = []
        int_tree = []
        for i in self.internal_tree:
            int_tree.append(i[0])
        print(int_tree)
        print("-"*70)
        for i in int_tree:
            if i not in self.ignore:
                clean_tree.append(i)
        print(clean_tree)
        print("-"*70)
        self.internal_tree = clean_tree

#     def update():
#         print("updates ugit.py to newest version")
#         raw_url = "https://raw.githubusercontent.com/turfptax/ugit/master/"
#         pull("ugit.py", raw_url + "ugit.py")

    def backup(self):
        self.build_internal_tree()
        backup_text = "ugit Backup Version 1.0\n\n"
        for i in self.internal_tree:
            data = open(i[0], "rb")
            backup_text += f"FN:SHA1{i[0]},{i[1]}\n"
            backup_text += "---" + binascii.b2a_base64(data.read()) + "---\n"
            data.close()
        with open("ugit.backup", "wb") as backup:
            backup.write(backup_text)

def test():
    user = "turfptax"
    repository = "ugit_test"
    token = ""
