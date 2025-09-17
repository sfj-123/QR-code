"""
This code file contains the implementation of the QR code generator for version 2 & version 1 QR code.
So it could change the version of the QR code according to the input data length automatically.
Also, it provides the core functionality for generating QR codes with more various customization options.
"""

# ===== Developers =====
# 31808308_PanYuxuan finished Version 2 and Automatic Version Selection and Multiple Mask Patterns and Penalty Scoring.
# 31808395_ShenFangjie designed Step-by-Step Display animation.
# 31808636_ZhangEnze finished Inclusive, Accessible Customisation.
# 31808380_MaoLeping help to design the _png function and modified the QR rendering.

# ===== Imports and Global Constants =====
from PIL import Image
import io
import os
import tempfile
import base64
import reedsolo
import itertools

# Mode indicators for different data types
mds = {'binary': 4}

# Error correction levels
err_lv = {'L': 'L'}

# Length field sizes for different versions and modes
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

# Version sizes (number of modules per side)
v_sz = [None, 21, 25]  # Added version 2 size

# Data capacity for different versions and error correction levels
cap = {1: {"L": {0: 152, 1: 41, 2: 25, 4: 17, 8: 10}},
       2: {"L": {0: 272, 1: 77, 2: 47, 4: 32, 8: 20}}}  # Added version 2 capacity

# Error correction codewords configuration
ecc = {1: {'L': [7, 1, 19, 0, 0]},
       2: {'L': [10, 1, 34, 0, 0]}}  # Added version 2 ECC

# Generator polynomials for Reed-Solomon encoding
gp = {7: [87, 229, 146, 149, 238, 102, 21],
      10: [251, 67, 46, 61, 118, 70, 64, 94, 32, 45]}  # Added version 2 generator polynomial

# Format information for different error correction levels and mask patterns
tp_bits = {'L': {
    0: '111011111000100',
    1: '111001011110011',
    2: '111110110101010',
    3: '111100010011101',
    4: '110011000101111',
    5: '110001100011000',
    6: '110110001000001',
    7: '110100101110110',
}, }

# Mask pattern functions
masks = [
    lambda row, col: (row + col) % 2 == 0,
    lambda row, col: row % 2 == 0,
    lambda row, col: col % 3 == 0,
    lambda row, col: (row + col) % 3 == 0,
    lambda row, col: ((row // 2) + (col // 3)) % 2 == 0,
    lambda row, col: ((row * col) % 2) + ((row * col) % 3) == 0,
    lambda row, col: (((row * col) % 2) + ((row * col) % 3)) % 2 == 0,
    lambda row, col: (((row + col) % 2) + ((row * col) % 3)) % 2 == 0]


# ===== Color and Gradient Utilities =====
def hex_to_rgb(hex_color):
    """
    Convert hexadecimal color code to RGB tuple.

    Args:
        hex_color (str): Hexadecimal color code (e.g., '#FF0000')

    Returns:
        tuple: RGB color values (r, g, b)
    """
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def create_linear_gradient(size, color1, color2, horizontal=True):
    """
    Generate a linear gradient image.

    Args:
        size (tuple): Image dimensions (width, height)
        color1 (tuple): Start color (RGB)
        color2 (tuple): End color (RGB)
        horizontal (bool): If True, gradient is horizontal; if False, vertical

    Returns:
        PIL.Image: Gradient image
    """
    width, height = size
    base = Image.new('RGB', size, color1)
    top = Image.new('RGB', size, color2)
    mask = Image.new('L', size)
    for i in range(width if horizontal else height):
        value = int(255 * i / (width - 1 if horizontal else height - 1))
        if horizontal:
            mask.paste(value, (i, 0, i + 1, height))
        else:
            mask.paste(value, (0, i, width, i + 1))
    base.paste(top, (0, 0), mask)
    return base


# ===== Penalty Calculation for Mask Patterns =====
def calculate_penalty(mask):
    """
    Calculate penalty scores for a mask pattern according to QR code standards.

    Args:
        mask (list): 2D list representing the QR code matrix

    Returns:
        list: Penalty scores for each rule [R1, R2, R3, R4]
    """
    score = [0, 0, 0, 0]  # Initialize scores for 4 penalty rules

    # Rule 1: Adjacent identical modules in row/column
    for row in mask:
        cnt = 1
        for i in range(1, len(row)):
            if row[i] == row[i - 1]:
                cnt += 1
            else:
                if cnt >= 5:
                    score[0] += (cnt - 5) + 3
                cnt = 1
        if cnt >= 5:
            score[0] += (cnt - 5) + 3

    # Rule 2: 2x2 identical blocks
    for i in range(len(mask) - 1):
        for j in range(len(mask) - 1):
            if (mask[i][j] == mask[i][j + 1] and
                    mask[i][j] == mask[i + 1][j] and
                    mask[i][j] == mask[i + 1][j + 1]):
                score[1] += 3

    # Rule 3: Finder-like patterns
    patterns = [
        [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1],  # Horizontal
        [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]  # Vertical
    ]
    for i in range(len(mask)):
        for j in range(len(mask)):
            # Check horizontal pattern
            if j <= len(mask) - 11:
                match = True
                for k in range(11):
                    if mask[i][j + k] != patterns[0][k]:
                        match = False
                        break
                if match:
                    score[2] += 40

            # Check vertical pattern
            if i <= len(mask) - 11:
                match = True
                for k in range(11):
                    if mask[i + k][j] != patterns[1][k]:
                        match = False
                        break
                if match:
                    score[2] += 40

    # Rule 4: Balance of dark and light modules
    dark = sum(sum(row) for row in mask)
    total = len(mask) ** 2
    percent = abs(dark * 100 / total - 50) / 5
    score[3] = int(percent) * 10

    return score


# ===== Core QR Code Construction Class =====
class QRBuilder:
    """
    QR Code Builder class that handles the construction of QR codes.
    Implements the core QR code generation algorithm.
    """

    def __init__(self, data, version, mode, error, debug=False):
        """
        Initialize QR code builder.

        Args:
            data (str): Data to encode
            version (int): QR code version (1 or 2)
            mode (str): Encoding mode
            error (str): Error correction level
            debug (bool): Enable debug output
        """
        self.data = data
        self.version = version
        self.debug = debug

        if mode != 'binary':
            raise ValueError(f'{mode} is not a valid mode.')
        self.mode = mds[mode]

        if error != 'L':
            raise ValueError(f'{error} is not a valid error level.')
        self.error = err_lv[error]

        self.eccw = ecc[self.version][self.error]
        self.buf = io.StringIO()

        self._add()
        self._make()

    def _group(self, n, it, fill=None):
        """
        Group items into n-sized chunks.

        Args:
            n (int): Size of each group
            it (iterable): Items to group
            fill: Value to fill incomplete groups

        Returns:
            zip_longest: Iterator of grouped items
        """
        return itertools.zip_longest(*[iter(it)] * n, fillvalue=fill)

    def _bin(self, d, l):
        """
        Convert number to binary string with fixed length.

        Args:
            d (int): Number to convert
            l (int): Desired length of binary string

        Returns:
            str: Binary string
        """
        return format(int(d), f'0{l}b')

    def _lenbits(self):
        """
        Generate length field bits based on version and mode.

        Returns:
            str: Binary string representing length field
        """
        if self.version <= 9:
            v = 9
        elif self.version <= 26:
            v = 26
        else:
            v = 40

        l = len_field[v][self.mode]
        s = self._bin(len(self.data), l)
        if len(s) > l:
            raise ValueError(f'The supplied data will not fit the version {self.version}.')
        return s

    def _encode(self):
        """
        Encode data according to selected mode.

        Returns:
            str: Encoded binary string
        """
        return self._encode_bytes()

    def _encode_bytes(self):
        """
        Encode data as bytes.

        Returns:
            str: Binary string representation of bytes
        """
        with io.StringIO() as buf:
            for ch in self.data:
                val = ord(ch) if not isinstance(ch, int) else ch
                buf.write(format(val, '08b'))
            return buf.getvalue()

    def _add(self):
        """
        Add mode indicator, length field, and encoded data to buffer.
        Also handles padding and error correction.
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
        """
        Add terminator bits if needed.

        Args:
            payload (str): Current bit stream

        Returns:
            str: Terminator bits or None
        """
        cap_bits = cap[self.version][self.error][0]
        plen = len(payload)
        if plen > cap_bits:
            raise ValueError(f'The input would not fit the version {self.version}')
        if plen == cap_bits:
            return None
        if plen <= cap_bits - 4:
            return self._bin(0, 4)
        return self._bin(0, cap_bits - plen)

    def _pad2byte(self):
        """
        Add padding bits to make length multiple of 8.

        Returns:
            str: Padding bits or None
        """
        bits_short = 8 - (len(self.buf.getvalue()) % 8)
        if bits_short in (0, 8):
            return None
        return self._bin(0, bits_short)

    def _fill(self):
        """
        Add fill bytes to reach capacity.

        Returns:
            str: Fill bytes or None
        """
        dbs = len(self.buf.getvalue()) // 8
        tbs = cap[self.version][self.error][0] // 8
        need = tbs - dbs
        if need <= 0:
            return None
        block = itertools.cycle(['11101100', '00010001'])
        return ''.join(next(block) for _ in range(need))

    def _rs(self, db, ebs):
        """
        Generate Reed-Solomon error correction codewords.

        Args:
            db (list): Data bytes
            ebs (int): Number of error correction bytes

        Returns:
            list: Error correction codewords
        """
        db_bytes = bytes(db)
        rs = reedsolo.RSCodec(ebs)
        codeword = rs.encode(db_bytes)
        ecc_bytes = codeword[-ebs:]
        return list(ecc_bytes)

    def _make(self):
        """
        Construct the final QR code matrix with finder patterns,
        alignment patterns, and data bits.
        """
        from copy import deepcopy

        sz = v_sz[self.version]

        row = [' ' for x in range(sz)]
        tpl = [deepcopy(row) for x in range(sz)]

        self._finder(tpl)
        if self.version >= 2:
            self._alignment(tpl)

        if self.debug:
            print("[Step 5] Matrix after adding finder/timing/separator/dark module:")
            self._print(tpl)

        # Generate all 8 masks
        self.masks = []
        for i in range(8):
            cur_mask = [row[:] for row in tpl]
            self._type(cur_mask, tp_bits[self.error][i])
            self._apply_mask(cur_mask, masks[i])
            self.masks.append(cur_mask)

        # Evaluate all masks and select the best one
        self.best_mask = self._select_best_mask()
        self.code = self.masks[self.best_mask]

        if self.debug:
            print(f"[Step 6] Best mask selected: {self.best_mask}")
            print("[Step 7] Final matrix after best mask applied:")
            self._print(self.code)

    def _print(self, m):
        """
        Print QR code matrix for debugging.

        Args:
            m (list): 2D matrix to print
        """
        for row in m:
            print(''.join(['#' if x == 1 else '.' if x == 0 else ' ' for x in row]))
        print()

    def _finder(self, m):
        """
        Add finder patterns to the matrix.

        Args:
            m (list): QR code matrix
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

    def _alignment(self, m):
        """
        Add alignment pattern for version 2+ QR codes.

        Args:
            m (list): QR code matrix
        """
        if self.version < 2:
            return

        # Alignment pattern is at (18, 18) for version 2
        center = 18
        size = 5

        # Outer black square
        for i in range(center - 2, center + 3):
            for j in [center - 2, center + 2]:
                m[i][j] = 1
                m[j][i] = 1

        # Inner white square
        for i in range(center - 1, center + 2):
            for j in [center - 1, center + 1]:
                m[i][j] = 0
                m[j][i] = 0

        # Center black dot
        m[center][center] = 1

    def _type(self, m, tp_str):
        """
        Add format information to the matrix.

        Args:
            m (list): QR code matrix
            tp_str (str): Format information string
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

    def _apply_mask(self, m, pattern):
        """
        Apply mask pattern to the matrix.

        Args:
            m (list): QR code matrix
            pattern (function): Mask pattern function
        """
        bits = iter(self.buf.getvalue())

        row_start = itertools.cycle([len(m) - 1, 0])
        row_stop = itertools.cycle([-1, len(m)])
        direction = itertools.cycle([-1, 1])

        for col in range(len(m) - 1, 0, -2):
            if col <= 6:
                col -= 1
            col_pair = itertools.cycle([col, col - 1])
            for row in range(next(row_start), next(row_stop), next(direction)):
                for _ in range(2):
                    c = next(col_pair)
                    if m[row][c] != ' ':
                        continue
                    try:
                        bit = int(next(bits))
                    except StopIteration:
                        bit = 0
                    m[row][c] = bit ^ 1 if pattern(row, c) else bit

    def _select_best_mask(self):
        """
        Select the best mask pattern based on penalty scores.

        Returns:
            int: Index of the best mask pattern
        """
        scores = []
        for i in range(len(self.masks)):
            penalty = calculate_penalty(self.masks[i])
            scores.append(sum(penalty))
            if self.debug:
                print(f"Mask {i} penalty scores: {penalty}, total: {sum(penalty)}")

        best = scores.index(min(scores))
        return best


# ===== High-level QR Code Interface =====
class QRCode:
    """
    Main QR Code class that handles QR code generation and customization.
    """

    def __init__(self, content, error='L', version=None, mode=None, encoding='iso-8859-1', debug=False):
        """
        Initialize QR code generator.

        Args:
            content (str): Content to encode
            error (str): Error correction level
            version (int): QR code version
            mode (str): Encoding mode
            encoding (str): Character encoding
            debug (bool): Enable debug output
        """
        self.data = content
        self.error = error
        self.encoding = encoding

        # Auto-detect version if not specified
        if version is None:
            self.version = self._pick_best_version(content)
        else:
            if version not in (1, 2):
                raise ValueError("Version must be 1 or 2")
            self.version = version

        self.mode = mode
        self.mode_num = mds.get(mode, mds['binary'])

        try:
            self.code = QRBuilder(content, self.version, self.mode, self.error, debug=debug).code
        except ValueError as e:
            if "would not fit" in str(e):
                # Try version 2 if version 1 fails
                if self.version == 1:
                    self.version = 2
                    self.code = QRBuilder(content, self.version, self.mode, self.error, debug=debug).code
                else:
                    raise
            else:
                raise

    def _pick_best_version(self, content):
        """
        Automatically select the best QR code version for the content.

        Args:
            content (str): Content to encode

        Returns:
            int: Selected QR code version
        """
        # Try version 1 first
        try:
            QRBuilder(content, 1, 'binary', self.error)
            return 1
        except ValueError:
            # If version 1 fails, try version 2
            try:
                QRBuilder(content, 2, 'binary', self.error)
                return 2
            except ValueError:
                raise ValueError("Content too long for version 1 or 2 QR codes")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "QRCode(content={0}, error='{1}', version={2}, mode='{3}')".format(
            repr(self.data), self.error, self.version, self.mode)

    def _detect_content_type(self, content, encoding):
        """
        Detect content type and encoding.

        Args:
            content (str): Content to analyze
            encoding (str): Character encoding

        Returns:
            tuple: (mode, encoding)
        """
        return 'binary', encoding

    def show(self, scale=10, quiet=4):
        """
        Display QR code in a temporary file.

        Args:
            scale (int): Size scale
            quiet (int): Quiet zone size

        Returns:
            str: Path to temporary file
        """
        f = tempfile.NamedTemporaryFile('wb', suffix='.png', delete=False)
        self.png(f, scale=scale, quiet_zone=quiet)
        f.close()
        return f.name

    def png_size(self, scale=1, quiet=4):
        """
        Calculate PNG size.

        Args:
            scale (int): Size scale
            quiet (int): Quiet zone size

        Returns:
            int: PNG size in pixels
        """
        return _png_size(self.version, scale, quiet)

    def png(self, file, scale=1, module_color=(0, 0, 0, 255), background=(255, 255, 255, 255), quiet_zone=4):
        """
        Generate PNG image of QR code.

        Args:
            file: File object or path
            scale (int): Size scale
            module_color (tuple): QR code color (RGBA)
            background (tuple): Background color (RGBA)
            quiet_zone (int): Quiet zone size
        """
        _png(self.code, self.version, file, scale,
             module_color=module_color, background=background, quiet_zone=quiet_zone)

    def png_b64(self, scale=1, quiet_zone=4):
        """
        Generate base64-encoded PNG image.

        Args:
            scale (int): Size scale
            quiet_zone (int): Quiet zone size

        Returns:
            str: Base64-encoded PNG image
        """
        with io.BytesIO() as vf:
            self.png(file=vf, scale=scale, quiet_zone=quiet_zone)
            img_str = base64.b64encode(vf.getvalue()).decode("ascii")
        return img_str


# ===== Factory and Utility Functions =====
def make_qr(content, error='L', version=None, mode=None, encoding=None, debug=False):
    """
    Create a QR code.

    Args:
        content (str): Content to encode
        error (str): Error correction level
        version (int): QR code version
        mode (str): Encoding mode
        encoding (str): Character encoding
        debug (bool): Enable debug output

    Returns:
        QRCode: QR code object
    """
    return QRCode(content, error, version, mode, encoding, debug=debug)


def _png_size(version, scale, quiet=4):
    """
    Calculate PNG size.

    Args:
        version (int): QR code version
        scale (int): Size scale
        quiet (int): Quiet zone size

    Returns:
        int: PNG size in pixels
    """
    scale = int(scale)
    return scale * v_sz[version] + 2 * quiet * scale


def _png(code, version, file, scale=1, module_color=(0, 0, 0, 255),
         background=(255, 255, 255, 255), quiet_zone=4, debug=False):
    """
    Generate PNG image of QR code.

    Args:
        code (list): QR code matrix
        version (int): QR code version
        file: File object or path
        scale (int): Size scale
        module_color (tuple): QR code color (RGBA)
        background (tuple): Background color (RGBA)
        quiet_zone (int): Quiet zone size
        debug (bool): Enable debug output
    """
    cnt = len(code)
    sz = cnt * scale + 2 * quiet_zone * scale

    px = []
    white = [1] * scale
    black = [0] * scale

    px.extend([[1] * sz for _ in range(quiet_zone * scale)])

    for row in code:
        row_px = [1] * (quiet_zone * scale)
        for bit in row:
            row_px.extend(black if bit else white)
        row_px.extend([1] * (quiet_zone * scale))
        px.extend([row_px] * scale)

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


# ===== QR Code Image Generation and Advanced Styling =====
def qr_img(data, color="#000000", background="#ffffff", scale=10, border_width=4, border_color="#000000",
           shape="square", **kwargs):
    """
    Generate QR code image with custom styling.

    Args:
        data (str): Content to encode
        color (str): QR code color (hex)
        background (str): Background color (hex)
        scale (int): Size scale
        border_width (int): Border width
        border_color (str): Border color (hex)
        shape (str): Module shape ('square' or 'circle')
        **kwargs: Additional styling parameters

    Returns:
        PIL.Image: QR code image
    """
    version = None  # Auto-detect version
    error = 'L'
    qr = make_qr(data, error=error, version=version, mode='binary', debug=False)
    code = qr.code
    size = len(code)
    img_size = size * scale + 2 * border_width

    img = Image.new("RGB", (img_size, img_size), background)
    draw = ImageDraw = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw
    draw = draw(img)

    # Draw border
    if border_width > 0:
        for x in range(img_size):
            for y in range(border_width):
                img.putpixel((x, y), hex_to_rgb(border_color))
                img.putpixel((x, img_size - 1 - y), hex_to_rgb(border_color))
        for y in range(img_size):
            for x in range(border_width):
                img.putpixel((x, y), hex_to_rgb(border_color))
                img.putpixel((img_size - 1 - x, y), hex_to_rgb(border_color))

    # Draw QR code content
    for y in range(size):
        for x in range(size):
            if code[y][x] == 1:
                px = x * scale + border_width
                py = y * scale + border_width
                if shape == "circle":
                    draw.ellipse([px, py, px + scale - 1, py + scale - 1], fill=color)
                else:
                    draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=color)

    return img


def generate_qr_code2(input_string, color="#000000", background="#ffffff", scale=10,
                     border_width=4, border_color="#000000", gradient_type="none",
                     gradient_colors=None, return_version=False):
    """
    Generate QR code with advanced styling options.

    Args:
        input_string (str): Content to encode
        color (str): QR code color (hex)
        background (str): Background color (hex)
        scale (int): Size scale
        border_width (int): Border width
        border_color (str): Border color (hex)
        gradient_type (str): Gradient type ('none', 'linear', or 'radial')
        gradient_colors (list): List of two colors for gradient
        return_version (bool): Whether to return QR code version

    Returns:
        tuple: (mask_images, mask_scores, best_mask[, version])
    """
    # Generate QR code object
    qr = make_qr(input_string, error='L', version=None, mode='binary', debug=False)
    builder = QRBuilder(input_string, qr.version, 'binary', 'L')
    masks = builder.masks
    # Detailed scoring
    mask_scores = [calculate_penalty(mask) for mask in masks]
    best_mask = builder.best_mask
    version = qr.version

    # Generate QR code images for all 8 masks
    size = len(masks[0])
    img_size = size * scale + 2 * border_width
    mask_images = []
    for idx, mask in enumerate(masks):
        img = Image.new("RGB", (img_size, img_size), background)
        draw = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw(img)
        # Border
        if border_width > 0:
            for x in range(img_size):
                for y in range(border_width):
                    img.putpixel((x, y), hex_to_rgb(border_color))
                    img.putpixel((x, img_size - 1 - y), hex_to_rgb(border_color))
            for y in range(img_size):
                for x in range(border_width):
                    img.putpixel((x, y), hex_to_rgb(border_color))
                    img.putpixel((img_size - 1 - x, y), hex_to_rgb(border_color))

        # Gradient support
        grad_img = None
        if gradient_type != "none" and gradient_colors and len(gradient_colors) == 2:
            grad_img = create_linear_gradient(
                (size, size),
                hex_to_rgb(gradient_colors[0]),
                hex_to_rgb(gradient_colors[1]),
                horizontal=(gradient_type == "linear")
            )

        for y in range(size):
            for x in range(size):
                if mask[y][x] == 1:
                    px = x * scale + border_width
                    py = y * scale + border_width
                    # Sample gradient color or normal color
                    if grad_img:
                        fill_color = grad_img.getpixel((x, y))
                    else:
                        fill_color = color
                    if isinstance(fill_color, str):
                        fill_color = hex_to_rgb(fill_color)
                    draw.rectangle([px, py, px + scale - 1, py + scale - 1], fill=fill_color)
        mask_images.append(img)

    if return_version:
        return mask_images, mask_scores, best_mask, version
    else:
        return mask_images, mask_scores, best_mask


# ===== Step-by-Step QR Code Construction Visualization =====
def generate_step_images(input_string, color="#000000", background="#ffffff", scale=10, mask_id=0):
    """
    Generate step-by-step QR code construction images.

    Args:
        input_string (str): Content to encode
        color (str): QR code color (hex)
        background (str): Background color (hex)
        scale (int): Size scale
        mask_id (int): Mask pattern index

    Returns:
        list: List of PIL.Image objects showing construction steps
    """
    qr = make_qr(input_string, error='L', version=None, mode='binary', debug=False)
    builder = QRBuilder(input_string, qr.version, 'binary', 'L')
    size = len(builder.masks[0])
    border_width = 4
    img_size = size * scale + 2 * border_width

    # 1. Finder Pattern
    tpl = [[' ' for _ in range(size)] for _ in range(size)]
    builder._finder(tpl)
    img1 = Image.new("RGB", (img_size, img_size), background)
    draw1 = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw(img1)
    for y in range(size):
        for x in range(size):
            if tpl[y][x] == 1:
                px = x * scale + border_width
                py = y * scale + border_width
                draw1.rectangle([px, py, px + scale - 1, py + scale - 1], fill=color)

    # 2. Alignment Pattern (Version 2+)
    tpl2 = [row[:] for row in tpl]
    if builder.version >= 2:
        builder._alignment(tpl2)
    img2 = Image.new("RGB", (img_size, img_size), background)
    draw2 = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw(img2)
    for y in range(size):
        for x in range(size):
            if tpl2[y][x] == 1:
                px = x * scale + border_width
                py = y * scale + border_width
                draw2.rectangle([px, py, px + scale - 1, py + scale - 1], fill=color)

    # 3. Format Information
    tpl3 = [row[:] for row in tpl2]
    builder._type(tpl3, tp_bits['L'][mask_id])
    img3 = Image.new("RGB", (img_size, img_size), background)
    draw3 = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw(img3)
    for y in range(size):
        for x in range(size):
            if tpl3[y][x] == 1:
                px = x * scale + border_width
                py = y * scale + border_width
                draw3.rectangle([px, py, px + scale - 1, py + scale - 1], fill=color)

    # 4. Data Bits
    tpl4 = [row[:] for row in tpl3]
    # Get encoded data bits
    data_bits = builder.buf.getvalue()
    bits = iter(data_bits)
    row_start = itertools.cycle([len(tpl4) - 1, 0])
    row_stop = itertools.cycle([-1, len(tpl4)])
    direction = itertools.cycle([-1, 1])
    for col in range(len(tpl4) - 1, 0, -2):
        if col <= 6:
            col -= 1
        col_pair = itertools.cycle([col, col - 1])
        for row in range(next(row_start), next(row_stop), next(direction)):
            for _ in range(2):
                c = next(col_pair)
                if tpl4[row][c] != ' ':
                    continue
                try:
                    bit = int(next(bits))
                except StopIteration:
                    bit = 0
                tpl4[row][c] = bit
    img4 = Image.new("RGB", (img_size, img_size), background)
    draw4 = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw(img4)
    for y in range(size):
        for x in range(size):
            if tpl4[y][x] == 1:
                px = x * scale + border_width
                py = y * scale + border_width
                draw4.rectangle([px, py, px + scale - 1, py + scale - 1], fill=color)

    # 5. Final QR Code (After Masking)
    mask = builder.masks[mask_id]
    img5 = Image.new("RGB", (img_size, img_size), background)
    draw5 = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw(img5)
    for y in range(size):
        for x in range(size):
            if mask[y][x] == 1:
                px = x * scale + border_width
                py = y * scale + border_width
                draw5.rectangle([px, py, px + scale - 1, py + scale - 1], fill=color)

    return [img1, img2, img3, img4, img5]