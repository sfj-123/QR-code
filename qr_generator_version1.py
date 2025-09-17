'''
This code file only contains the implementation of the QR code generator for version 1.
It is shown in the second sub-page of our Web.
In my opinion, it shows clearly how our QR code generator develops from version1 to version 2.
It is the foundation of our QR code generator project.
'''

# ===== Developers =====
# 31808308_PanYuxuan gave the framework of main classes(with no function contents) and Data Encoding and Format Information.
# 31808397_ShenRuiting mainly finished the rest content of functions and debugged Error Correction Integration and Matrix Layout and Patterns.

# ===== Imports and Global Constants =====
from PIL import Image
import io
import os
import tempfile
import base64
import reedsolo
import itertools

# Mode dictionary for QR encoding
mds = {'binary': 4}

# Error correction level dictionary
err_lv = {'L': 'L'}

# Length field for different QR versions and modes
len_field = {9: {1: 10, 2: 9, 4: 8, 8: 8},
             26: {1: 12, 2: 11, 4: 16, 8: 10},
             40: {1: 14, 2: 13, 4: 16, 8: 12}}

# Alphanumeric character mapping
asc = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
       '8': 8, '9': 9, 'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14,
       'F': 15, 'G': 16, 'H': 17, 'I': 18, 'J': 19, 'K': 20, 'L': 21,
       'M': 22, 'N': 23, 'O': 24, 'P': 25, 'Q': 26, 'R': 27, 'S': 28,
       'T': 29, 'U': 30, 'V': 31, 'W': 32, 'X': 33, 'Y': 34, 'Z': 35,
       ' ': 36, '$': 37, '%': 38, '*': 39, '+': 40, '-': 41, '.': 42,
       '/': 43, ':': 44}

# Version size (matrix size for each version)
v_sz = [None, 21]

# Data capacity for version 1 and error level L
cap = {1: {"L": {0: 152, 1: 41, 2: 25, 4: 17, 8: 10, }}}

# Error correction codeword info for version 1 and error level L
ecc = {1: { 'L': [7, 1, 19, 0, 0]}}

# Generator polynomial for Reed-Solomon
gp = {7: [87, 229, 146, 149, 238, 102, 21]}

# Type information bits for error level L and mask 0
tp_bits = {'L': {0: '111011111000100'}}

# Mask patterns (only one for version 1)
masks = [lambda r, c: (r + c) % 2 == 0]

# ===== QRBuilder: Core QR Code Construction Class =====
class QRBuilder:
    """
    QRBuilder handles the process of encoding data into a QR code matrix.
    """
    def __init__(self, data, version, mode, error, debug=False):
        self.data = data
        self.version = 1  # Only version 1 supported
        self.debug = debug
    
        # Only binary mode is supported
        if mode != 'binary':
            raise ValueError(f'{mode} is not a valid mode.')
        self.mode = mds[mode]
    
        # Only error level L is supported
        if error != 'L':
            raise ValueError(f'{error} is not a valid error level.')
        self.error = err_lv[error]
    
        # Error correction codeword info
        self.eccw = ecc[self.version][self.error]
        self.buf = io.StringIO()
    
        # Add data and build QR matrix
        self._add()
        self._make()

    def _group(self, n, it, fill=None):
        # Group iterable into n-sized chunks
        return itertools.zip_longest(*[iter(it)] * n, fillvalue=fill)

    def _bin(self, d, l):
        # Convert integer to binary string with fixed length
        return format(int(d), f'0{l}b')

    def _lenbits(self):
        # Get length field for QR encoding
        if self.version <= 9:
            v = 9
        elif self.version <= 26:
            v = 26
        else:
            v = 40
    
        l = len_field[v][self.mode]
        s = self._bin(len(self.data), l)
        if len(s) > l:
            raise ValueError('The supplied data will not fit the version 1.')
        return s

    def _encode(self):
        # Encode data as bytes (binary mode)
        return self._encode_bytes()

    def _encode_bytes(self):
        # Encode data as 8-bit binary
        with io.StringIO() as buf:
            for ch in self.data:
                val = ord(ch) if not isinstance(ch, int) else ch
                buf.write(format(val, '08b'))
            return buf.getvalue()

    def _add(self):
        """
        Add mode, length, and encoded data to buffer.
        Also handles terminator, padding, and error correction.
        """
        self.buf.write(self._bin(self.mode, 4))
        self.buf.write(self._lenbits())
        self.buf.write(self._encode())

        if self.debug:
            print("[Step 1] Encoded bit stream:")
            print(self.buf.getvalue())

        bits = self._term(self.buf.getvalue())
        if bits:
            self.buf.write(bits)

        add_bits = self._pad2byte()
        if add_bits:
            self.buf.write(add_bits)

        fill_bytes = self._fill()
        if fill_bytes:
            self.buf.write(fill_bytes)

        # Convert bit stream to bytes
        data = [int(''.join(x), 2) for x in self._group(8, self.buf.getvalue())]

        if self.debug:
            print("[Step 2] 8-bit grouped data bytes:")
            print(data)

        err_info = ecc[self.version][self.error]
        dbs = err_info[2]
        ebs = err_info[0]

        db = data[:dbs]
        eb = self._rs(db, ebs)

        if self.debug:
            print("[Step 3] Reed-Solomon error correction codewords:")
            print(eb)

        data_buf = io.StringIO()
        for b in db:
            data_buf.write(self._bin(b, 8))
        for b in eb:
            data_buf.write(self._bin(b, 8))

        self.buf = data_buf

        if self.debug:
            print("[Step 4] Data codewords + error codewords bit stream:")
            print(self.buf.getvalue())

    def _term(self, payload):
        # Add terminator bits if needed
        cap_bits = cap[self.version][self.error][0]
        plen = len(payload)
        if plen > cap_bits:
            raise ValueError('The input would not fit the version 1')
        if plen == cap_bits:
            return None
        if plen <= cap_bits - 4:
            return self._bin(0, 4)
        return self._bin(0, cap_bits - plen)

    def _pad2byte(self):
        # Pad to byte boundary
        bits_short = 8 - (len(self.buf.getvalue()) % 8)
        if bits_short in (0, 8):
            return None
        return self._bin(0, bits_short)

    def _fill(self):
        # Add pad bytes if needed
        dbs = len(self.buf.getvalue()) // 8
        tbs = cap[self.version][self.error][0] // 8
        need = tbs - dbs
        if need <= 0:
            return None
        block = itertools.cycle(['11101100', '00010001'])
        return ''.join(next(block) for _ in range(need))

    def _rs(self, db, ebs):
        # Generate Reed-Solomon error correction codewords
        db_bytes = bytes(db)
        rs = reedsolo.RSCodec(ebs)
        codeword = rs.encode(db_bytes)
        ecc_bytes = codeword[-ebs:]
        return list(ecc_bytes)

    def _make(self):
        """
        Build the QR matrix, add finder patterns, timing, and mask.
        """
        from copy import deepcopy

        sz = v_sz[self.version]

        # Initialize empty matrix
        row = [' ' for x in range(sz)]
        tpl = [deepcopy(row) for x in range(sz)]

        # Add finder patterns, timing, etc.
        self._finder(tpl)

        if self.debug:
            print("[Step 5] Matrix after adding finder/timing/separator/dark module:")
            self._print(tpl)

        # Apply mask
        self.msk = self._mask(tpl)

        self.best_mask = 0
        self.code = self.msk[0]

        if self.debug:
            print("[Step 6] Final matrix after mask 0 applied:")
            self._print(self.code)

    def _print(self, m):
        # Print QR matrix for debugging
        for row in m:
            print(''.join(['#' if x == 1 else '.' if x == 0 else ' ' for x in row]))
        print()

    def _finder(self, m):
        """
        Add finder patterns, separators, timing patterns, and dark module.
        """
        # Outer 7x7 black square
        for i in range(7):
            inv = -(i + 1)
            for j in [0, 6, -1, -7]:
                m[j][i] = 1
                m[i][j] = 1
                m[inv][j] = 1
                m[j][inv] = 1
    
        # Inner 5x5 white square
        for i in range(1, 6):
            inv = -(i + 1)
            for j in [1, 5, -2, -6]:
                m[j][i] = 0
                m[i][j] = 0
                m[inv][j] = 0
                m[j][inv] = 0
    
        # Center 3x3 black square
        for i in range(2, 5):
            for j in range(2, 5):
                inv = -(i + 1)
                m[i][j] = 1
                m[inv][j] = 1
                m[j][inv] = 1
    
        # Separator (white)
        for i in range(8):
            inv = -(i + 1)
            for j in [7, -8]:
                m[i][j] = 0
                m[j][i] = 0
                m[inv][j] = 0
                m[j][inv] = 0
    
        # Fill corners with blank
        for i in range(-8, 0):
            for j in range(-8, 0):
                m[i][j] = ' '
    
        # Timing pattern
        bit = itertools.cycle([1, 0])
        for i in range(8, len(m) - 8):
            b = next(bit)
            m[i][6] = b
            m[6][i] = b
    
        # Dark module
        m[-8][8] = 1

    def _mask(self, tpl):
        """
        Apply mask patterns to the matrix and return all masked matrices.
        """
        n = len(masks)
        ms = []
        for idx in range(n):
            cur = [row[:] for row in tpl]
            self._type(cur, tp_bits[self.error][idx])
            pat = masks[idx]
            bits = iter(self.buf.getvalue())
    
            row_start = itertools.cycle([len(cur) - 1, 0])
            row_stop = itertools.cycle([-1, len(cur)])
            direction = itertools.cycle([-1, 1])
    
            for col in range(len(cur) - 1, 0, -2):
                if col <= 6:
                    col -= 1
                col_pair = itertools.cycle([col, col - 1])
                for row in range(next(row_start), next(row_stop), next(direction)):
                    for _ in range(2):
                        c = next(col_pair)
                        if cur[row][c] != ' ':
                            continue
                        try:
                            bit = int(next(bits))
                        except StopIteration:
                            bit = 0
                        cur[row][c] = bit ^ 1 if pat(row, c) else bit
            ms.append(cur)
        return ms

    def _type(self, m, tp_str):
        """
        Add type information bits to the matrix.
        """
        f = iter(tp_str)
        for i in range(7):
            bit = int(next(f))
            m[8][i if i < 6 else i + 1] = bit
            m[-(i + 1)][8] = bit
    
        for i in range(-8, 0):
            bit = int(next(f))
            m[8][i] = bit
            j = -i
            m[j if j > 6 else j - 1][8] = bit

# ===== QRCode: High-level QR Code Interface =====
class QRCode:
    """
    QRCode is a high-level interface for generating QR codes.
    """
    def __init__(self, content, error='L', version=None, mode=None, encoding='iso-8859-1', debug=False):
        self.data = content
        self.error = error
        self.version = 1
        self.mode = mode
        self.encoding = encoding
        self.mode_num = mds.get(mode, mds['binary'])
        self.code = QRBuilder(content, self.version, self.mode, self.error, debug=debug).code

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "QRCode(content={0}, error='{1}', version={2}, mode='{3}')".format(
            repr(self.data), self.error, self.version, self.mode)

    def _detect_content_type(self, content, encoding):
        # Always returns binary mode for now
        return 'binary', encoding

    def show(self, scale=10, quiet=4):
        """
        Save QR code as PNG and return file path.
        """
        f = tempfile.NamedTemporaryFile('wb', suffix='.png', delete=False)
        self.png(f, scale=scale, quiet_zone=quiet)
        f.close()
        return f.name

    def png_size(self, scale=1, quiet=4):
        # Get PNG image size in pixels
        return _png_size(self.version, scale, quiet)

    def png(self, file, scale=1, quiet_zone=4):
        # Render QR code to PNG file
        _png(self.code, self.version, file, scale,
             module_color=(0, 0, 0, 255), background=(255, 255, 255, 255), quiet_zone=quiet_zone)

    def png_b64(self, scale=1, quiet_zone=4):
        """
        Return PNG as base64 string.
        """
        with io.BytesIO() as vf:
            self.png(file=vf, scale=scale, quiet_zone=quiet_zone)
            img_str = base64.b64encode(vf.getvalue()).decode("ascii")
        return img_str

# ===== Factory and Utility Functions =====
def make_qr(content, error='L', version=None, mode=None, encoding=None, debug=False):
    # Factory function to create QRCode object
    return QRCode(content, error, version, mode, encoding, debug=debug)

def _png_size(version, scale, quiet=4):
    # Calculate PNG image size in pixels
    scale = int(scale)
    return scale * v_sz[version] + 2 * quiet * scale

def _png(code, version, file, scale=1, module_color=(0, 0, 0, 255),
         background=(255, 255, 255, 255), quiet_zone=4, debug=False):
    """
    Render QR code matrix to PNG file using pypng.
    """
    cnt = len(code)
    sz = cnt * scale + 2 * quiet_zone * scale

    px = []
    white = [1] * scale
    black = [0] * scale

    # Top margin
    px.extend([[1] * sz for _ in range(quiet_zone * scale)])

    for row in code:
        row_px = [1] * (quiet_zone * scale)
        for bit in row:
            row_px.extend(black if bit else white)
        row_px.extend([1] * (quiet_zone * scale))
        px.extend([row_px] * scale)

    # Bottom margin
    px.extend([[1] * sz for _ in range(quiet_zone * scale)])

    try:
        import png
    except ImportError:
        raise ImportError("Please install pypng: pip install pypng")
    w = png.Writer(sz, sz, greyscale=True, bitdepth=1)
    if isinstance(file, str):
        with open(file, 'wb') as f:
            w.write(f, px)
    else:
        w.write(file, px)

def qr_img(data, debug=False):
    """
    Generate QR code image from input string.
    Returns a PIL Image object.
    """
    version = 1
    error = 'L'
    qr = make_qr(data, error=error, version=version, mode='binary', debug=debug)
    tmp = tempfile.NamedTemporaryFile('wb', suffix='.png', delete=False)
    qr.png(tmp, scale=10)
    tmp.close()
    img = Image.open(tmp.name).convert("1")
    os.unlink(tmp.name)
    return img