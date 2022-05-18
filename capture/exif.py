import subprocess
import json

class ExifTool(object):
    """Creates a persistent session exiftool command line wrapper, this enables 
        ultra fast file metadata querying by keeping exiftool always open in
        a background subprocess. 
        USAGE:
            >>> from imagine.exif import EXIFTOOL
            >>> key = EXIFTOOL.getFields(str(filepath), ['-exposureTime#'], float)
            >>> 0.01
    """

    def __init__(self):
        self._exif_proc = None

    @property
    def exif(self):
        if not self._exif_proc:
            self._exif_proc = subprocess.Popen(
                'exiftool -stay_open True -@ -',
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        return self._exif_proc

    def getFields(self, path, fields, result_type):
        """Retrieves the given fields as a specified python type.

            Parameters
            ----------
            path : string
                input file path
            fields : List
                single or multiple keys to  
            result_type : dict, int, str or float
                Pass the desired python type to get back as a result. 

            Returns
            -------
            dict, int, str or float
                The result as json key values or a single value in other forms.
        """
        exif = self.exif
        if isinstance(result_type, dict):
            fields.insert(0, '-json')
        else:
            fields.insert(0, '-s3') # single

        fields.append(path)
        fields.append('-execute\n') # for -stay_open flag

        exif.stdin.write(bytes('\n'.join(fields), encoding='utf-8'))
        exif.stdin.flush()
        output = b''
        while True:
            line = exif.stdout.readline()
            output += line
            if output.endswith(b'y}\r\n'):
                break

        data = output.decode('utf-8').replace('{ready}', '')

        if isinstance(result_type, dict):
            result = json.loads(data)[0]
        else:
            result = result_type(data)

        return result

    def __del__(self):
        # Kill the exiftool child process
        if self._exif_proc:
            pid = self._exif_proc.pid
            subprocess.call(
                f'taskkill /F /T /PID {pid}',
                creationflags=subprocess.CREATE_NO_WINDOW)

EXIFTOOL = ExifTool()
