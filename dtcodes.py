"""
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published
by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,　but WITHOUT ANY WARRANTY; without even the implied warranty of　
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the　GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


import struct


def _write_dtype_C1(file, data):
    file.write(struct.pack("c", data.encode('ascii')))


def _write_dtype_B1(file, data):
    file.write(struct.pack("B", data))


def _write_dtype_N1(file, data):
    file.write(struct.pack("B", data))


def _write_dtype_U1(file, data):
    file.write(struct.pack("B", data))


def _write_dtype_U2(file, data):
    file.write(struct.pack("H", data))


def _write_dtype_U4(file, data):
    file.write(struct.pack("I", data))


def _write_dtype_U8(file, data):
    file.write(struct.pack("H", data))


def _write_dtype_I1(file, data):
    file.write(struct.pack("b", data))


def _write_dtype_I2(file, data):
    file.write(struct.pack("h", data))


def _write_dtype_I4(file, data):
    file.write(struct.pack("i", data))


def _write_dtype_I8(file, data):
    file.write(struct.pack("q", data))


def _write_dtype_R4(file, data):
    file.write(struct.pack("f", data))


def _write_dtype_R8(file, data):
    file.write(struct.pack("d", data))


def _write_dtype_header(file, len, typ, sub):
    _write_dtype_U2(file, len)
    _write_dtype_U1(file, typ)
    _write_dtype_U1(file, sub)


def _write_nbytes(file, data, n):
    file.write(struct.pack("{}s".format(n), data.encode('ascii')))


def _write_dtype_Cn(file, data):
    _write_dtype_B1(file, len(data))
    if len(data):
        _write_nbytes(file, data, len(data))


def _write_dtype_Bn(file, data):
    data = str(data)  # change to string type, then we can use _write_dtype_Cn
    if data:
        [_write_dtype_Cn(file, d) for d in data]
    else:
        _write_dtype_B1(file, len(data))


def _write_dtype_Dn(file, data):
    if data:
        _write_dtype_U2(file, len(data)*8)
        [_write_dtype_U1(file, d) for d in data]
    else:
        _write_dtype_U2(file, len(data))


def _write_dtype_xU1(file, data, n):
    for i in range(int(n)):
        _write_dtype_U1(file, data[i])


def _write_dtype_xU2(file, data, n):
    for i in range(int(n)):
        _write_dtype_U2(file, data[i])


def _write_dtype_xR4(file, data, n):
    for i in range(int(n)):
        _write_dtype_R4(file, data[i])


def _write_dtype_xCn(file, data, n):
    for i in range(int(n)):
        _write_dtype_Cn(file, data[i])


def _write_dtype_xBn(file, data, n):
    for i in range(int(n)):
        _write_dtype_Bn(file, data[i])


def _write_dtype_xN1(file, data, n):
    for i in range(int(int(n)/2 + int(n) % 2)):
        _write_dtype_U1(file, data[i])


_VN_map = {  # first byte is vn map key, following bytes is data
    0: lambda file, data: [_write_dtype_B1(file, 0), _write_dtype_B1(file, data)],
    1: lambda file, data: [_write_dtype_B1(file, 1), _write_dtype_U1(file, data)],
    2: lambda file, data: [_write_dtype_B1(file, 2), _write_dtype_U2(file, data)],
    3: lambda file, data: [_write_dtype_B1(file, 3), _write_dtype_U4(file, data)],
    4: lambda file, data: [_write_dtype_B1(file, 4), _write_dtype_I1(file, data)],
    5: lambda file, data: [_write_dtype_B1(file, 5), _write_dtype_I2(file, data)],
    6: lambda file, data: [_write_dtype_B1(file, 6), _write_dtype_I4(file, data)],
    7: lambda file, data: [_write_dtype_B1(file, 7), _write_dtype_R4(file, data)],
    8: lambda file, data: [_write_dtype_B1(file, 8), _write_dtype_R8(file, data)],
    10: lambda file, data: [_write_dtype_B1(file, 10), _write_dtype_Cn(file, data)],
    11: lambda file, data: [_write_dtype_B1(file, 11), _write_dtype_Bn(file, data)],
    12: lambda file, data: [_write_dtype_B1(file, 12), _write_dtype_Dn(file, data)],
    13: lambda file, data: [_write_dtype_B1(file, 13), _write_dtype_N1(file, data)]
}


write_record_map = {
    "C1": _write_dtype_C1,
    "B1": _write_dtype_B1,
    "U1": _write_dtype_U1,
    "U2": _write_dtype_U2,
    "U4": _write_dtype_U4,
    "U8": _write_dtype_U8,
    "I1": _write_dtype_I1,
    "I2": _write_dtype_I2,
    "I4": _write_dtype_I4,
    "I8": _write_dtype_I8,
    "R4": _write_dtype_R4,
    "R8": _write_dtype_R8,
    "Cn": _write_dtype_Cn,
    "Bn": _write_dtype_Bn,
    "Dn": _write_dtype_Dn,
    "kxU1": _write_dtype_xU1,
    "kxU2": _write_dtype_xU2,
    "kxCn": _write_dtype_xCn,
    "kxN1": _write_dtype_xN1,
    "kxR4": _write_dtype_xR4,
    "Vn": _VN_map,
    "Header": _write_dtype_header
}


pack_len_map = {
  "C1": struct.calcsize("c"),
  "B1": struct.calcsize("B"),
  "U1": struct.calcsize("B"),
  "U2": struct.calcsize("H"),
  "U4": struct.calcsize("I"),
  "U8": struct.calcsize("Q"),
  "I1": struct.calcsize("b"),
  "I2": struct.calcsize("h"),
  "I4": struct.calcsize("i"),
  "I8": struct.calcsize("q"),
  "R4": struct.calcsize("f"),
  "R8": struct.calcsize("d")
}
