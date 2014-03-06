import os

import sublime
import subprocess
import re


class VcsHelper(object):
    @classmethod
    def vcs_dir(cls, directory):
        """Return the path to the metadata directory, assuming it is
        directly under the passed directory."""
        if not directory:
            return False
        return os.path.join(directory, cls.meta_data_directory())

    @classmethod
    def vcs_file_path(cls, view, vcs_path):
        """Returns the relative path to the file in the Sublime view, in
        the repository rooted at vcs_path."""
        if not vcs_path:
            return False
        full_file_path = os.path.realpath(view.file_name())
        vcs_path_to_file = \
            full_file_path.replace(vcs_path, '').replace('\\', '/')
        if vcs_path_to_file[0] == '/':
            vcs_path_to_file = vcs_path_to_file[1:]
        return vcs_path_to_file

    @classmethod
    def vcs_root(cls, directory):
        """Returns the top-level directory of the repository."""
        if os.path.exists(os.path.join(directory,
                          cls.meta_data_directory())):
            return directory
        else:
            parent = os.path.realpath(os.path.join(directory, os.path.pardir))
            if parent == directory:
                # we have reached root dir
                return False
            else:
                return cls.vcs_root(parent)

    @classmethod
    def vcs_tree(cls, view):
        """Returns the directory at the top of the tree that contains
        the file in the passed Sublime view."""
        full_file_path = view.file_name()
        file_parent_dir = os.path.realpath(os.path.dirname(full_file_path))
        return cls.vcs_root(file_parent_dir)

    @classmethod
    def is_repository(cls, view):
        if view is None or view.file_name() is None or not cls.vcs_dir(cls.vcs_tree(view)):
            return False
        else:
            return True


class GitHelper(VcsHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.git'

    @classmethod
    def is_git_repository(cls, view):
        return cls.is_repository(view)


class HgHelper(VcsHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.hg'

    @classmethod
    def is_hg_repository(cls, view):
        return cls.is_repository(view)


class SvnHelper(VcsHelper):
    @classmethod
    def meta_data_directory(cls):
        return '.svn'

    @classmethod
    def is_svn_repository(cls, view):
        return cls.is_repository(view)


class PerforceHelper(VcsHelper):
    # We need this to call p4 to find the root dir
    p4bin = 'p4'
    # Cache so that things arent -too- slow
    vcs_root_cache = {}

    @classmethod
    def meta_data_directory(cls):
        return ''

    @classmethod
    def vcs_root(cls, directory):
        if directory in cls.vcs_root_cache:
            return cls.vcs_root_cache[directory]

        # This is not great...
        # TODO: find a better way to find the root p4 dir
        info, err = subprocess.Popen([
            cls.p4bin,
            '-d', directory,
            'info'], stdout=subprocess.PIPE).communicate()
        match = re.search(r'\nClient root: ([^\n]+)', info.decode('utf-8'))
        if match is None:
            cls.vcs_root_cache[directory] = False
            return False
        cls.vcs_root_cache[directory] = match.group(1)
        return match.group(1)

    @classmethod
    def is_p4_repository(cls, view):
        if view is None or view.file_name() is None:
            return False

        cur_dir = os.path.abspath(view.file_name())
        rt = os.path.abspath(cls.vcs_root(cur_dir))
        return len(os.path.commonprefix([rt, cur_dir])) >= len(rt)
