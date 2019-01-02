import os
from unittest import TestCase


class TCLHandler:
    _source_folder = "data"
    _extension = '.tcl'
    _current_file = None
    _tcl_buffer = ""

    def __init__(self):
        cwd = os.getcwd()
        self._source_folder = os.path.join(cwd, os.path.normpath(self._source_folder))

    def file_list(self):
        bases = set([f["base_name"] for f in self._files()])
        return ', '.join(bases)

    # loads a data file from disk.  returns name, version, contents
    def load(self, fname):
        if not fname.endswith(self._extension):
            fname = fname + self._extension

        version = self._get_latest_version(fname)
        fname = self.set_version(fname, version)
        self._tcl_buffer = ""
        self._current_file = os.path.join(self._source_folder, fname)
        with open(self._current_file, 'r') as f:
            self._tcl_buffer = f.read()
        return self._current_file, version, self._tcl_buffer

    # write to next version of this file...
    def save(self, tcl_buffer2):
        fname = os.path.basename(self._current_file)
        version = self._get_latest_version(fname)
        if tcl_buffer2 != self._tcl_buffer:
            version = version + 1
            new_file = self.set_version(fname, version)
            new_file = os.path.join(self._source_folder, new_file)
            self._current_file = new_file
            with open(self._current_file, 'w') as f:
                f.write(tcl_buffer2)
            self._tcl_buffer = tcl_buffer2
        return self._current_file, version, tcl_buffer2

    def get_basename(self, fname):
        base, _, extension = self._get_parts(fname)
        return "{}.{}".format(base, extension)

    def set_version(self, fname, version):
        base, _, extension = self._get_parts(fname)
        return self._set_parts(base, str(version), extension)

    def get_version(self, fname):
        _, version, _ = self._get_parts(fname)
        return int(version)

    def _get_latest_version(self, fname):
        fname = self.get_basename(fname)
        return max([f["version"] for f in self._files() if f["base_name"] == fname])

    def _get_parts(self, fname):
        spl = fname.split('.')
        if len(spl) == 3:
            version = int(spl[1])
            extension = spl[2]
        else:
            version = 1
            extension = spl[1]
        return spl[0], version, extension

    def _set_parts(self, base, version, extension):
        if int(version) > 1:
            ret = "{}.{}.{}".format(base, version, extension)
        else:
            ret = "{}.{}".format(base, extension)
        return ret

    def _files(self):
        ff = [{"base_name": self.get_basename(fn), "version": self.get_version(fn)} for fn in
              os.listdir(self._source_folder)]
        return [{"base_name": self.get_basename(fn), "version": self.get_version(fn)} for fn in
                os.listdir(self._source_folder)]


class TestTCLSource(TestCase):

    def test__get_basename(self):
        tcl = TCLHandler()
        self.assertEqual("test1.data", tcl.get_basename("test1.1.data"))
        self.assertEqual("test1.data", tcl.get_basename("test1.data"))

    def test__set_version(self):
        tcl = TCLHandler()
        self.assertEqual("test1.2.data", tcl.set_version("test1.data", 2))
        self.assertEqual("test1.2.data", tcl.set_version("test1.3.data", 2))

    def test__get_version(self):
        tcl = TCLHandler()
        self.assertEqual(2, tcl.get_version("test1.2.data"))
        self.assertEqual(1, tcl.get_version("test.data"))

    def test_file_list(self):
        tcl = TCLHandler()
        l = tcl.file_list()
        print(l)
        self.assertTrue(len(l) > 0)

    def test_load(self):
        tcl = TCLHandler()
        fnm, version, tcl_text = tcl.load("test.data")
        print(fnm, version, tcl)
        self.assertTrue(len(fnm) > 0)
        self.assertTrue(version > 0)

    def test_save(self):
        tcl = TCLHandler()
        fnm, version, tcl_text = tcl.load("test.data")
        self.assertTrue(len(fnm) > 0)
        self.assertTrue(version > 0)
        fnm = tcl.save("This is another version")
        self.assertTrue(len(fnm) > 0)
